"""
Pipeline ETL principal para processamento de arquivos XML fiscais.

Este módulo orquestra o processo completo de ETL:
- Extract: Leitura dos arquivos XML
- Transform: Conversão dos dados para modelos do banco
- Load: Persistência no banco de dados
"""
import os
import glob
from typing import List, Optional
from pathlib import Path
import time
from datetime import datetime

from .extractor import XMLExtractor
from .transformer import DataTransformer
from .loader import DataLoader
from .database import init_database
from .config import config


class ETLPipeline:
    """
    Pipeline completo de ETL para documentos fiscais.
    
    Processa arquivos XML de NF-e e NFC-e, extraindo todos os dados
    e armazenando em um datalake estruturado.
    """

    def __init__(self):
        """Inicializa o pipeline ETL."""
        self.extractor = XMLExtractor()
        self.transformer = DataTransformer()
        self.loader = DataLoader()
        
        # Estatísticas
        self.stats = {
            'total_arquivos': 0,
            'processados': 0,
            'duplicados': 0,
            'erros': 0,
            'tempo_total': 0,
        }

    def processar_diretorio(self, diretorio: str = None, 
                           tipo_processamento: str = 'completo',
                           recursivo: bool = True) -> dict:
        """
        Processa todos os arquivos XML de um diretório.
        
        Args:
            diretorio: Caminho do diretório (usa config.diretorio_padrao se None)
            tipo_processamento: Tipo de processamento ('completo' ou 'incremental')
            recursivo: Se deve processar subdiretórios
            
        Returns:
            Dicionário com estatísticas do processamento
        """
        # Usar diretório padrão se não fornecido
        if not diretorio:
            diretorio = config.diretorio_padrao
            if not diretorio:
                raise ValueError("Nenhum diretório foi especificado e não há diretório padrão configurado!")
        
        print(f"\n{'='*80}")
        print(f"Iniciando processamento ETL")
        print(f"Diretório: {diretorio}")
        print(f"Tipo: {tipo_processamento}")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        if config.deletar_apos_processar:
            print(f"Modo: Deletar arquivos após processamento")
        elif config.mover_para_backup:
            print(f"Modo: Mover arquivos para backup ({config.diretorio_backup})")
        else:
            print(f"Modo: Manter arquivos originais")
        print(f"{'='*80}\n")
        
        inicio_total = time.time()
        
        # Iniciar processamento
        processamento_id = self.loader.iniciar_processamento(tipo_processamento)
        print(f"ID do Processamento: {processamento_id}\n")
        
        try:
            # Localizar arquivos XML
            arquivos_xml = self._localizar_arquivos_xml(diretorio, recursivo)
            self.stats['total_arquivos'] = len(arquivos_xml)
            
            print(f"Arquivos XML encontrados: {len(arquivos_xml)}\n")
            
            if not arquivos_xml:
                print("Nenhum arquivo XML encontrado!")
                self.loader.finalizar_processamento(
                    processamento_id=processamento_id,
                    status='concluido',
                    mensagem='Nenhum arquivo encontrado',
                    tempo_execucao=time.time() - inicio_total
                )
                return self.stats
            
            # Processar cada arquivo
            for i, arquivo in enumerate(arquivos_xml, 1):
                print(f"[{i}/{len(arquivos_xml)}] Processando: {Path(arquivo).name}")
                
                resultado = self.processar_arquivo(
                    arquivo=arquivo,
                    processamento_id=processamento_id
                )
                
                if resultado['sucesso']:
                    self.stats['processados'] += 1
                    print(f"  ✓ Sucesso - Chave: {resultado.get('chave_acesso', 'N/A')}")
                elif resultado['duplicado']:
                    self.stats['duplicados'] += 1
                    print(f"  ⚠ Duplicado - Chave: {resultado.get('chave_acesso', 'N/A')}")
                else:
                    self.stats['erros'] += 1
                    print(f"  ✗ Erro - {resultado.get('mensagem', 'Erro desconhecido')}")
                
                print()
            
            # Finalizar processamento
            self.stats['tempo_total'] = time.time() - inicio_total
            
            self.loader.finalizar_processamento(
                processamento_id=processamento_id,
                status='concluido',
                mensagem='Processamento concluído com sucesso',
                arquivos_processados=self.stats['processados'] + self.stats['duplicados'],
                arquivos_erro=self.stats['erros'],
                tempo_execucao=self.stats['tempo_total']
            )
            
            # Exibir resumo
            self._exibir_resumo()
            
        except Exception as e:
            self.stats['tempo_total'] = time.time() - inicio_total
            
            self.loader.finalizar_processamento(
                processamento_id=processamento_id,
                status='erro',
                mensagem=f'Erro no processamento: {str(e)}',
                arquivos_processados=self.stats['processados'],
                arquivos_erro=self.stats['erros'],
                tempo_execucao=self.stats['tempo_total']
            )
            
            print(f"\n❌ ERRO NO PROCESSAMENTO: {str(e)}\n")
            raise
        
        return self.stats

    def processar_arquivo(self, arquivo: str, 
                         processamento_id: Optional[int] = None) -> dict:
        """
        Processa um único arquivo XML.
        
        Args:
            arquivo: Caminho do arquivo XML
            processamento_id: ID do processamento ETL
            
        Returns:
            Dicionário com resultado do processamento
        """
        resultado = {
            'sucesso': False,
            'duplicado': False,
            'mensagem': '',
            'chave_acesso': None,
        }
        
        try:
            # Extract
            dados_extraidos = self.extractor.extrair_nfe(arquivo)
            resultado['chave_acesso'] = dados_extraidos.get('identificacao', {}).get('chave_acesso')
            
            # Transform
            nfe = self.transformer.transformar_nfe(dados_extraidos)
            
            # Load
            resultado_carga = self.loader.carregar_nfe(
                nfe=nfe,
                arquivo=arquivo,
                processamento_id=processamento_id,
                dados_emitente=dados_extraidos.get('emitente', {})
            )
            
            resultado.update(resultado_carga)
            
        except Exception as e:
            resultado['mensagem'] = f'Erro ao processar arquivo: {str(e)}'
        
        return resultado

    def processar_arquivos_lista(self, arquivos: List[str],
                                tipo_processamento: str = 'completo') -> dict:
        """
        Processa uma lista específica de arquivos.
        
        Args:
            arquivos: Lista de caminhos dos arquivos XML
            tipo_processamento: 'completo' ou 'incremental'
            
        Returns:
            Dicionário com estatísticas do processamento
        """
        print(f"\n{'='*80}")
        print(f"Iniciando processamento ETL de lista de arquivos")
        print(f"Total de arquivos: {len(arquivos)}")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        inicio_total = time.time()
        processamento_id = self.loader.iniciar_processamento(tipo_processamento)
        
        self.stats['total_arquivos'] = len(arquivos)
        
        try:
            for i, arquivo in enumerate(arquivos, 1):
                print(f"[{i}/{len(arquivos)}] Processando: {Path(arquivo).name}")
                
                resultado = self.processar_arquivo(
                    arquivo=arquivo,
                    processamento_id=processamento_id
                )
                
                if resultado['sucesso']:
                    self.stats['processados'] += 1
                elif resultado['duplicado']:
                    self.stats['duplicados'] += 1
                else:
                    self.stats['erros'] += 1
            
            self.stats['tempo_total'] = time.time() - inicio_total
            
            self.loader.finalizar_processamento(
                processamento_id=processamento_id,
                status='concluido',
                mensagem='Processamento concluído',
                arquivos_processados=self.stats['processados'] + self.stats['duplicados'],
                arquivos_erro=self.stats['erros'],
                tempo_execucao=self.stats['tempo_total']
            )
            
            self._exibir_resumo()
            
        except Exception as e:
            self.loader.finalizar_processamento(
                processamento_id=processamento_id,
                status='erro',
                mensagem=str(e),
                tempo_execucao=time.time() - inicio_total
            )
            raise
        
        return self.stats

    def _localizar_arquivos_xml(self, diretorio: str, recursivo: bool = True) -> List[str]:
        """
        Localiza todos os arquivos XML em um diretório.
        
        Args:
            diretorio: Caminho do diretório
            recursivo: Se deve buscar em subdiretórios
            
        Returns:
            Lista de caminhos dos arquivos XML
        """
        if recursivo:
            pattern = os.path.join(diretorio, '**', '*.xml')
            arquivos = glob.glob(pattern, recursive=True)
        else:
            pattern = os.path.join(diretorio, '*.xml')
            arquivos = glob.glob(pattern)
        
        return sorted(arquivos)

    def _exibir_resumo(self):
        """Exibe resumo do processamento."""
        print(f"\n{'='*80}")
        print("RESUMO DO PROCESSAMENTO")
        print(f"{'='*80}")
        print(f"Total de arquivos:     {self.stats['total_arquivos']:>6}")
        print(f"Processados:           {self.stats['processados']:>6}")
        print(f"Duplicados (ignorados):{self.stats['duplicados']:>6}")
        print(f"Erros:                 {self.stats['erros']:>6}")
        print(f"Tempo total:           {self.stats['tempo_total']:>6.2f}s")
        
        if self.stats['total_arquivos'] > 0:
            taxa_sucesso = (self.stats['processados'] / self.stats['total_arquivos']) * 100
            print(f"Taxa de sucesso:       {taxa_sucesso:>6.1f}%")
            
            tempo_medio = self.stats['tempo_total'] / self.stats['total_arquivos']
            print(f"Tempo médio/arquivo:   {tempo_medio:>6.2f}s")
        
        print(f"{'='*80}\n")


def inicializar_banco():
    """Inicializa o banco de dados, criando todas as tabelas."""
    print("Inicializando banco de dados...")
    init_database()
    print("✓ Banco de dados inicializado com sucesso!\n")


def executar_etl(diretorio: str, recursivo: bool = True):
    """
    Função auxiliar para executar o ETL facilmente.
    
    Args:
        diretorio: Diretório com arquivos XML
        recursivo: Se deve processar subdiretórios
    """
    pipeline = ETLPipeline()
    return pipeline.processar_diretorio(diretorio, recursivo=recursivo)
