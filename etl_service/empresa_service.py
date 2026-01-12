"""
Serviço de gerenciamento de empresas para o ETL.

Responsável por validar e cadastrar automaticamente empresas
durante o processamento dos XMLs.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class EmpresaService:
    """Serviço para gerenciar empresas no banco de dados."""
    
    def __init__(self, session: Session):
        """
        Inicializa o serviço de empresas.
        
        Args:
            session: Sessão do SQLAlchemy
        """
        self.session = session
    
    def validar_ou_cadastrar_empresa(
        self, 
        cnpj: str, 
        dados_emitente: Dict[str, Any]
    ) -> Optional[int]:
        """
        Valida se empresa existe e cadastra se necessário.
        
        Args:
            cnpj: CNPJ da empresa (apenas números ou formatado)
            dados_emitente: Dados do emitente extraídos do XML
            
        Returns:
            ID da empresa no banco de dados ou None se erro
        """
        try:
            # Importar aqui para evitar dependência circular
            from sqlalchemy import text
            
            # Limpar CNPJ (remover formatação)
            cnpj_limpo = self._limpar_cnpj(cnpj)
            
            if not cnpj_limpo:
                logger.warning("CNPJ inválido ou não informado")
                return None
            
            # Conectar ao banco fiscal_auditor
            db_url = os.environ.get(
                'FISCAL_AUDITOR_DATABASE_URL',
                'postgresql://postgres:postgres@localhost:5432/fiscal_auditor'
            )
            engine = create_engine(db_url)
            
            with engine.begin() as conn:
                # Verificar se empresa existe
                result = conn.execute(
                    text("SELECT id FROM empresas WHERE cnpj = :cnpj"),
                    {"cnpj": cnpj_limpo}
                ).fetchone()
                
                if result:
                    logger.info(f"Empresa encontrada: CNPJ {cnpj_limpo}, ID {result[0]}")
                    return result[0]
                
                # Cadastrar nova empresa
                logger.info(f"Cadastrando nova empresa: CNPJ {cnpj_limpo}")
                
                # Preparar campos conforme schema existente (inscricao_estadual, cidade, estado, etc.)
                razao_social = (dados_emitente.get('razao_social') or 'NÃO INFORMADO')
                nome_fantasia = dados_emitente.get('nome_fantasia')
                inscricao_estadual = dados_emitente.get('inscricao_estadual')
                inscricao_municipal = dados_emitente.get('inscricao_municipal')

                end = dados_emitente.get('endereco', {}) if isinstance(dados_emitente.get('endereco', {}), dict) else {}
                logradouro = end.get('logradouro')
                numero = end.get('numero')
                complemento = end.get('complemento')
                bairro = end.get('bairro')
                endereco_str = ', '.join([p for p in [logradouro, numero, complemento, bairro] if p]) or None
                cidade = end.get('municipio')
                estado = end.get('uf')
                cep = end.get('cep')
                telefone = end.get('telefone')
                email = dados_emitente.get('email')

                result = conn.execute(
                    text("""
                        INSERT INTO empresas (
                            cnpj, razao_social, nome_fantasia,
                            inscricao_estadual, inscricao_municipal,
                            endereco, cidade, estado, cep, telefone, email,
                            ativo, data_criacao, data_atualizacao
                        ) VALUES (
                            :cnpj, :razao_social, :nome_fantasia,
                            :inscricao_estadual, :inscricao_municipal,
                            :endereco, :cidade, :estado, :cep, :telefone, :email,
                            true, NOW(), NOW()
                        ) RETURNING id
                    """),
                    {
                        "cnpj": cnpj_limpo,
                        "razao_social": razao_social,
                        "nome_fantasia": nome_fantasia,
                        "inscricao_estadual": inscricao_estadual,
                        "inscricao_municipal": inscricao_municipal,
                        "endereco": endereco_str,
                        "cidade": cidade,
                        "estado": estado,
                        "cep": cep,
                        "telefone": telefone,
                        "email": email
                    }
                )
                
                empresa_id = result.fetchone()[0]
                logger.info(f"Empresa cadastrada com sucesso: ID {empresa_id}")
                return empresa_id
                
        except Exception as e:
            logger.error(f"Erro ao validar/cadastrar empresa: {e}", exc_info=True)
            return None
        
        # Verificar se empresa já existe
        empresa = self._buscar_empresa_por_cnpj(cnpj_limpo)
        
        if empresa:
            logger.debug(f"Empresa já cadastrada: {cnpj_limpo}")
            return empresa['id']
        
        # Empresa não existe, cadastrar
        logger.info(f"Cadastrando nova empresa: {cnpj_limpo}")
        empresa_id = self._cadastrar_empresa(cnpj_limpo, dados_emitente)
        
        return empresa_id
    
    def _buscar_empresa_por_cnpj(self, cnpj: str) -> Optional[Dict[str, Any]]:
        """
        Busca empresa por CNPJ.
        
        Args:
            cnpj: CNPJ da empresa (apenas números)
            
        Returns:
            Dicionário com dados da empresa ou None
        """
        try:
            result = self.session.execute(
                """
                SELECT id, cnpj, razao_social, nome_fantasia, 
                       inscricao_estadual, ativo
                FROM empresas
                WHERE cnpj = :cnpj
                LIMIT 1
                """,
                {'cnpj': cnpj}
            )
            
            row = result.fetchone()
            if row:
                return {
                    'id': row[0],
                    'cnpj': row[1],
                    'razao_social': row[2],
                    'nome_fantasia': row[3],
                    'inscricao_estadual': row[4],
                    'ativo': row[5]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar empresa: {e}")
            return None
    
    def _cadastrar_empresa(
        self, 
        cnpj: str, 
        dados_emitente: Dict[str, Any]
    ) -> Optional[int]:
        """
        Cadastra nova empresa no banco.
        
        Args:
            cnpj: CNPJ da empresa
            dados_emitente: Dados extraídos do XML
            
        Returns:
            ID da empresa cadastrada ou None em caso de erro
        """
        try:
            # Extrair dados do emitente
            razao_social = dados_emitente.get('razao_social', '')[:200]
            nome_fantasia = dados_emitente.get('nome_fantasia', '')[:200] or None
            inscricao_estadual = dados_emitente.get('inscricao_estadual', '')[:20] or None
            inscricao_municipal = dados_emitente.get('inscricao_municipal', '')[:20] or None
            
            # Dados de endereço
            endereco_dict = dados_emitente.get('endereco', {})
            logradouro = endereco_dict.get('logradouro', '')
            numero = endereco_dict.get('numero', '')
            complemento = endereco_dict.get('complemento', '')
            bairro = endereco_dict.get('bairro', '')
            
            # Montar endereço completo
            partes_endereco = [logradouro, numero, complemento, bairro]
            endereco = ', '.join([p for p in partes_endereco if p])[:300] or None
            
            cidade = endereco_dict.get('municipio', '')[:100] or None
            estado = endereco_dict.get('uf', '')[:2] or None
            cep = endereco_dict.get('cep', '')[:10] or None
            telefone = endereco_dict.get('telefone', '')[:20] or None
            
            # Inserir empresa
            result = self.session.execute(
                """
                INSERT INTO empresas (
                    cnpj, razao_social, nome_fantasia, 
                    inscricao_estadual, inscricao_municipal,
                    endereco, cidade, estado, cep, telefone,
                    ativo, data_criacao, data_atualizacao
                )
                VALUES (
                    :cnpj, :razao_social, :nome_fantasia,
                    :inscricao_estadual, :inscricao_municipal,
                    :endereco, :cidade, :estado, :cep, :telefone,
                    :ativo, :data_criacao, :data_atualizacao
                )
                RETURNING id
                """,
                {
                    'cnpj': cnpj,
                    'razao_social': razao_social,
                    'nome_fantasia': nome_fantasia,
                    'inscricao_estadual': inscricao_estadual,
                    'inscricao_municipal': inscricao_municipal,
                    'endereco': endereco,
                    'cidade': cidade,
                    'estado': estado,
                    'cep': cep,
                    'telefone': telefone,
                    'ativo': True,
                    'data_criacao': datetime.now(),
                    'data_atualizacao': datetime.now()
                }
            )
            
            empresa_id = result.fetchone()[0]
            self.session.commit()
            
            logger.info(f"Empresa cadastrada com sucesso. ID: {empresa_id}, CNPJ: {cnpj}")
            return empresa_id
            
        except Exception as e:
            logger.error(f"Erro ao cadastrar empresa: {e}", exc_info=True)
            self.session.rollback()
            return None
    
    def _limpar_cnpj(self, cnpj: str) -> Optional[str]:
        """
        Remove formatação do CNPJ.
        
        Args:
            cnpj: CNPJ com ou sem formatação
            
        Returns:
            CNPJ apenas com números ou None se inválido
        """
        if not cnpj:
            return None
        
        # Remover caracteres não numéricos
        cnpj_limpo = ''.join(c for c in str(cnpj) if c.isdigit())
        
        # Validar tamanho
        if len(cnpj_limpo) != 14:
            return None
        
        return cnpj_limpo
    
    def formatar_cnpj(self, cnpj: str) -> str:
        """
        Formata CNPJ para exibição.
        
        Args:
            cnpj: CNPJ sem formatação
            
        Returns:
            CNPJ formatado (99.999.999/9999-99)
        """
        if not cnpj or len(cnpj) != 14:
            return cnpj
        
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
