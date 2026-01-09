"""
Configuração do serviço ETL.

Carrega configurações de arquivo .env.etl ou variáveis de ambiente.
"""
import os
from pathlib import Path
from typing import Optional


class ETLConfig:
    """Configurações do serviço ETL."""
    
    def __init__(self):
        """Inicializa as configurações."""
        self._carregar_env()
    
    def _carregar_env(self):
        """Carrega variáveis do arquivo .env.etl se existir."""
        env_file = Path(__file__).parent.parent / '.env.etl'
        
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if linha and not linha.startswith('#'):
                        if '=' in linha:
                            chave, valor = linha.split('=', 1)
                            # Não sobrescrever se já existe no ambiente
                            if chave not in os.environ:
                                os.environ[chave] = valor
    
    @property
    def diretorio_padrao(self) -> Optional[str]:
        """Diretório padrão para monitoramento."""
        return os.getenv('DIRETORIO_PADRAO')
    
    @property
    def deletar_apos_processar(self) -> bool:
        """Se deve deletar arquivos após processar."""
        return os.getenv('DELETAR_APOS_PROCESSAR', 'false').lower() == 'true'
    
    @property
    def mover_para_backup(self) -> bool:
        """Se deve mover para backup ao invés de deletar."""
        return os.getenv('MOVER_PARA_BACKUP', 'false').lower() == 'true'
    
    @property
    def diretorio_backup(self) -> Optional[str]:
        """Diretório de backup."""
        return os.getenv('DIRETORIO_BACKUP')
    
    @property
    def validar_por_chave(self) -> bool:
        """Se deve validar duplicatas por chave de acesso."""
        return os.getenv('VALIDAR_POR_CHAVE', 'true').lower() == 'true'
    
    @property
    def validar_por_hash(self) -> bool:
        """Se deve validar duplicatas por hash do arquivo."""
        return os.getenv('VALIDAR_POR_HASH', 'false').lower() == 'true'
    
    @property
    def recursivo(self) -> bool:
        """Se deve processar subdiretórios."""
        return os.getenv('RECURSIVO', 'true').lower() == 'true'
    
    @property
    def processar_subdiretorios(self) -> bool:
        """Se deve processar subdiretórios."""
        return os.getenv('PROCESSAR_SUBDIRETORIOS', 'true').lower() == 'true'
    
    @property
    def database_url(self) -> str:
        """URL do banco de dados."""
        return os.getenv(
            'ETL_DATABASE_URL',
            'postgresql://postgres:postgres@localhost:5432/fiscal_datalake'
        )


# Instância global
config = ETLConfig()
