"""
Loader de dados - Módulo de Carregamento do ETL.

Este módulo é responsável por carregar (persistir) os dados transformados
no banco de dados, gerenciando transações e tratando duplicações.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import time
import hashlib
import os
import shutil
import logging

from .models import NFe, LogProcessamento, ProcessamentoETL, ArquivoProcessado
from .database import SessionLocal
from .config import config

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Carregador de dados no banco de dados.
    
    Gerencia a persistência dos dados transformados, garantindo
    integridade e registrando logs do processo.
    """

    def __init__(self, db_session: Optional[Session] = None):
        """
        Inicializa o loader.
        
        Args:
            db_session: Sessão do banco de dados (opcional)
        """
        self.db_session = db_session
    
    def arquivo_ja_processado(self, caminho_arquivo: str) -> bool:
        """
        Verifica se um arquivo já foi processado anteriormente.
        
        Args:
            caminho_arquivo: Caminho completo do arquivo
            
        Returns:
            True se já foi processado, False caso contrário
        """
        session = self.db_session or SessionLocal()
        
        try:
            # Verificar por caminho do arquivo
            if config.validar_por_chave:
                arquivo_proc = session.query(ArquivoProcessado).filter(
                    ArquivoProcessado.caminho_arquivo == caminho_arquivo,
                    ArquivoProcessado.status == 'processado'
                ).first()
                
                if arquivo_proc:
                    return True
            
            # Verificar por hash do arquivo
            if config.validar_por_hash and os.path.exists(caminho_arquivo):
                hash_atual = self._calcular_hash_arquivo(caminho_arquivo)
                arquivo_proc = session.query(ArquivoProcessado).filter(
                    ArquivoProcessado.hash_arquivo == hash_atual,
                    ArquivoProcessado.status == 'processado'
                ).first()
                
                if arquivo_proc:
                    return True
            
            return False
            
        finally:
            if not self.db_session:
                session.close()
    
    def _calcular_hash_arquivo(self, caminho_arquivo: str) -> str:
        """
        Calcula o hash SHA256 de um arquivo.
        
        Args:
            caminho_arquivo: Caminho do arquivo
            
        Returns:
            Hash SHA256 em hexadecimal
        """
        sha256 = hashlib.sha256()
        with open(caminho_arquivo, 'rb') as f:
            for bloco in iter(lambda: f.read(4096), b''):
                sha256.update(bloco)
        return sha256.hexdigest()

    def carregar_nfe(self, nfe: NFe, arquivo: str, 
                     processamento_id: Optional[int] = None) -> dict:
        """
        Carrega uma NF-e no banco de dados.
        
        Args:
            nfe: Objeto NFe a ser persistido
            arquivo: Caminho do arquivo original
            processamento_id: ID do processamento ETL
            
        Returns:
            Dicionário com resultado da operação
        """
        inicio = time.time()
        session = self.db_session or SessionLocal()
        resultado = {
            'sucesso': False,
            'duplicado': False,
            'mensagem': '',
            'chave_acesso': nfe.chave_acesso,
        }
        
        try:
            # Verificar se arquivo já foi processado
            if arquivo and self.arquivo_ja_processado(arquivo):
                resultado['duplicado'] = True
                resultado['mensagem'] = 'Arquivo já foi processado anteriormente'
                
                # Registrar log
                self._registrar_log(
                    session=session,
                    processamento_id=processamento_id,
                    arquivo=arquivo,
                    chave_acesso=nfe.chave_acesso,
                    status='duplicado',
                    mensagem='Arquivo já processado anteriormente',
                    tempo=time.time() - inicio
                )
                
                if not self.db_session:
                    session.commit()
                
                # Deletar arquivo duplicado
                self.deletar_ou_mover_arquivo(arquivo)
                
                return resultado
            
            # Verificar se já existe por chave de acesso
            nfe_existente = session.query(NFe).filter(
                NFe.chave_acesso == nfe.chave_acesso
            ).first()
            
            if nfe_existente:
                resultado['duplicado'] = True
                resultado['mensagem'] = 'NF-e já existe no banco de dados'
                
                # Registrar log
                self._registrar_log(
                    session=session,
                    processamento_id=processamento_id,
                    arquivo=arquivo,
                    chave_acesso=nfe.chave_acesso,
                    status='duplicado',
                    mensagem='NF-e já processada anteriormente',
                    tempo=time.time() - inicio
                )
                
                if not self.db_session:
                    session.commit()
                
                # Registrar arquivo como processado (duplicado) e deletar
                if arquivo:
                    self.registrar_arquivo_processado(arquivo, nfe.chave_acesso, 'duplicado')
                    self.deletar_ou_mover_arquivo(arquivo)
                
                return resultado
            
            # Adicionar nova NF-e
            session.add(nfe)
            
            # Fazer flush para obter o ID da NF-e
            session.flush()
            
            # Registrar log de sucesso
            self._registrar_log(
                session=session,
                processamento_id=processamento_id,
                arquivo=arquivo,
                chave_acesso=nfe.chave_acesso,
                status='sucesso',
                mensagem='NF-e processada com sucesso',
                tempo=time.time() - inicio
            )
            
            # Commit obrigatório
            if not self.db_session:
                session.commit()
            
            # Registrar arquivo como processado com sucesso
            if arquivo:
                self.registrar_arquivo_processado(arquivo, nfe.chave_acesso, 'processado')
                # Deletar ou mover arquivo após processamento
                self.deletar_ou_mover_arquivo(arquivo)
            
            resultado['sucesso'] = True
            resultado['mensagem'] = 'NF-e carregada com sucesso'
            
        except IntegrityError as e:
            if not self.db_session:
                session.rollback()
            
            resultado['duplicado'] = True
            resultado['mensagem'] = f'Erro de integridade: {str(e)}'
            
            # Registrar log de erro
            self._registrar_log(
                session=session,
                processamento_id=processamento_id,
                arquivo=arquivo,
                chave_acesso=nfe.chave_acesso,
                status='duplicado',
                mensagem=resultado['mensagem'],
                tempo=time.time() - inicio
            )
            
            if not self.db_session:
                try:
                    session.commit()
                except:
                    pass
            
            # Registrar arquivo como erro e deletar
            if arquivo:
                self.registrar_arquivo_processado(arquivo, nfe.chave_acesso, 'erro')
                self.deletar_ou_mover_arquivo(arquivo)
            
        except Exception as e:
            if not self.db_session:
                session.rollback()
            
            resultado['mensagem'] = f'Erro ao carregar NF-e: {str(e)}'
            
            # Registrar log de erro
            self._registrar_log(
                session=session,
                processamento_id=processamento_id,
                arquivo=arquivo,
                chave_acesso=nfe.chave_acesso,
                status='erro',
                mensagem=resultado['mensagem'],
                tempo=time.time() - inicio
            )
            
            if not self.db_session:
                try:
                    session.commit()
                except:
                    pass
            
            # Registrar arquivo como erro (não deletar arquivos com erro)
            if arquivo:
                self.registrar_arquivo_processado(arquivo, nfe.chave_acesso, 'erro')
        
        finally:
            if not self.db_session:
                session.close()
        
        return resultado

    def carregar_nfes_lote(self, nfes: List[NFe], arquivos: List[str],
                           processamento_id: Optional[int] = None,
                           tamanho_lote: int = 100) -> dict:
        """
        Carrega múltiplas NF-es em lotes.
        
        Args:
            nfes: Lista de objetos NFe
            arquivos: Lista de caminhos dos arquivos originais
            processamento_id: ID do processamento ETL
            tamanho_lote: Tamanho do lote para commit
            
        Returns:
            Dicionário com estatísticas do carregamento
        """
        estatisticas = {
            'total': len(nfes),
            'sucesso': 0,
            'duplicados': 0,
            'erros': 0,
            'tempo_total': 0,
        }
        
        inicio_total = time.time()
        
        try:
            for i, (nfe, arquivo) in enumerate(zip(nfes, arquivos)):
                # Usar sessão separada para cada arquivo para evitar problemas
                resultado = self.carregar_nfe(
                    nfe=nfe,
                    arquivo=arquivo,
                    processamento_id=processamento_id
                )
                
                if resultado['sucesso']:
                    estatisticas['sucesso'] += 1
                elif resultado['duplicado']:
                    estatisticas['duplicados'] += 1
                else:
                    estatisticas['erros'] += 1
            
            estatisticas['tempo_total'] = time.time() - inicio_total
            
        except Exception as e:
            estatisticas['tempo_total'] = time.time() - inicio_total
            raise e
        
        return estatisticas

    def iniciar_processamento(self, tipo: str = 'completo') -> int:
        """
        Inicia um novo processamento ETL.
        
        Args:
            tipo: Tipo de processamento ('completo' ou 'incremental')
            
        Returns:
            ID do processamento criado
        """
        session = SessionLocal()
        
        try:
            processamento = ProcessamentoETL(
                data_processamento=datetime.now(),
                tipo_processamento=tipo,
                status='executando'
            )
            
            session.add(processamento)
            session.commit()
            session.refresh(processamento)
            
            return processamento.id
            
        finally:
            session.close()

    def finalizar_processamento(self, processamento_id: int,
                                status: str, mensagem: Optional[str] = None,
                                arquivos_processados: int = 0,
                                arquivos_erro: int = 0,
                                tempo_execucao: Optional[float] = None):
        """
        Finaliza um processamento ETL.
        
        Args:
            processamento_id: ID do processamento
            status: Status final ('concluido' ou 'erro')
            mensagem: Mensagem adicional
            arquivos_processados: Quantidade de arquivos processados
            arquivos_erro: Quantidade de arquivos com erro
            tempo_execucao: Tempo de execução em segundos
        """
        session = SessionLocal()
        
        try:
            processamento = session.query(ProcessamentoETL).filter(
                ProcessamentoETL.id == processamento_id
            ).first()
            
            if processamento:
                processamento.status = status
                processamento.mensagem = mensagem
                processamento.arquivos_processados = arquivos_processados
                processamento.arquivos_erro = arquivos_erro
                processamento.tempo_execucao = tempo_execucao
                
                session.commit()
            
        finally:
            session.close()

    def registrar_arquivo_processado(self, caminho_arquivo: str, chave_acesso: str, status: str):
        """
        Registra um arquivo como processado na tabela ArquivoProcessado.
        
        Args:
            caminho_arquivo: Caminho completo do arquivo
            chave_acesso: Chave de acesso da NF-e
            status: Status do processamento ('processado', 'duplicado', 'erro')
        """
        session = SessionLocal()
        
        try:
            # Calcular hash do arquivo
            hash_arquivo = None
            if os.path.exists(caminho_arquivo):
                hash_arquivo = self._calcular_hash_arquivo(caminho_arquivo)
            
            # Criar registro
            arquivo_proc = ArquivoProcessado(
                caminho_arquivo=caminho_arquivo,
                hash_arquivo=hash_arquivo,
                chave_acesso=chave_acesso,
                status=status,
                data_processamento=datetime.now(),
                deletado=False
            )
            
            session.add(arquivo_proc)
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Erro ao registrar arquivo processado: {str(e)}")
        finally:
            session.close()
    
    def deletar_ou_mover_arquivo(self, caminho_arquivo: str):
        """
        Deleta ou move um arquivo para backup após processamento.
        
        Args:
            caminho_arquivo: Caminho completo do arquivo
        """
        if not os.path.exists(caminho_arquivo):
            return
        
        try:
            # Verificar configuração
            if config.deletar_apos_processar:
                # Deletar arquivo
                os.remove(caminho_arquivo)
                logger.info(f"Arquivo deletado: {caminho_arquivo}")
                
                # Atualizar registro no banco
                self._atualizar_status_arquivo(caminho_arquivo, deletado=True)
                
            elif config.mover_para_backup and config.diretorio_backup:
                # Mover para diretório de backup
                backup_dir = config.diretorio_backup
                
                # Criar diretório de backup se não existir
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                # Mover arquivo mantendo o nome original
                nome_arquivo = os.path.basename(caminho_arquivo)
                caminho_backup = os.path.join(backup_dir, nome_arquivo)
                
                # Se já existe no backup, adicionar timestamp
                if os.path.exists(caminho_backup):
                    nome_base, extensao = os.path.splitext(nome_arquivo)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    nome_arquivo = f"{nome_base}_{timestamp}{extensao}"
                    caminho_backup = os.path.join(backup_dir, nome_arquivo)
                
                shutil.move(caminho_arquivo, caminho_backup)
                logger.info(f"Arquivo movido para backup: {caminho_backup}")
                
                # Atualizar registro no banco
                self._atualizar_status_arquivo(caminho_arquivo, 
                                               deletado=False, 
                                               caminho_backup=caminho_backup)
                
        except Exception as e:
            logger.error(f"Erro ao deletar/mover arquivo {caminho_arquivo}: {str(e)}")
    
    def _atualizar_status_arquivo(self, caminho_arquivo: str, deletado: bool, caminho_backup: str = None):
        """
        Atualiza o status de deleção de um arquivo processado.
        
        Args:
            caminho_arquivo: Caminho original do arquivo
            deletado: Se o arquivo foi deletado
            caminho_backup: Caminho do backup (se foi movido)
        """
        session = SessionLocal()
        
        try:
            arquivo_proc = session.query(ArquivoProcessado).filter(
                ArquivoProcessado.caminho_arquivo == caminho_arquivo
            ).first()
            
            if arquivo_proc:
                arquivo_proc.deletado = deletado
                if caminho_backup:
                    arquivo_proc.caminho_backup = caminho_backup
                session.commit()
                
        except Exception as e:
            session.rollback()
            logger.error(f"Erro ao atualizar status do arquivo: {str(e)}")
        finally:
            session.close()

    def obter_chaves_existentes(self, chaves: List[str]) -> set:
        """
        Verifica quais chaves de acesso já existem no banco.
        
        Args:
            chaves: Lista de chaves de acesso
            
        Returns:
            Set com chaves que já existem
        """
        session = self.db_session or SessionLocal()
        
        try:
            existentes = session.query(NFe.chave_acesso).filter(
                NFe.chave_acesso.in_(chaves)
            ).all()
            
            return set(chave[0] for chave in existentes)
            
        finally:
            if not self.db_session:
                session.close()

    def _registrar_log(self, session: Session, processamento_id: Optional[int],
                      arquivo: str, chave_acesso: str, status: str,
                      mensagem: str, tempo: float):
        """
        Registra log de processamento de um arquivo.
        
        Args:
            session: Sessão do banco
            processamento_id: ID do processamento ETL
            arquivo: Caminho do arquivo
            chave_acesso: Chave de acesso da NF-e
            status: Status do processamento
            mensagem: Mensagem descritiva
            tempo: Tempo de processamento em segundos
        """
        import os
        
        log = LogProcessamento(
            processamento_id=processamento_id,
            data_hora=datetime.now(),
            arquivo=arquivo,
            chave_acesso=chave_acesso,
            status=status,
            mensagem=mensagem,
            tempo_processamento=tempo,
            tamanho_arquivo=os.path.getsize(arquivo) if os.path.exists(arquivo) else None
        )
        
        session.add(log)
