"""
Script principal para executar o serviço ETL.

Este script permite executar o processo ETL de forma independente,
processando arquivos XML de NF-e e NFC-e e armazenando em um datalake.
"""
import sys
import os
import argparse
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl_service.pipeline import ETLPipeline, inicializar_banco
from etl_service.database import DATABASE_URL
from etl_service.config import config


def main():
    """Função principal do script ETL."""
    parser = argparse.ArgumentParser(
        description='Serviço ETL para processamento de XMLs fiscais',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Inicializar o banco de dados (primeira execução)
  python run_etl.py --init-db

  # Processar usando diretório padrão do .env.etl
  python run_etl.py

  # Processar todos os XMLs de um diretório específico
  python run_etl.py --diretorio "C:\\XMLs\\2024"

  # Processar sem deletar os arquivos
  python run_etl.py --no-delete

  # Processar apenas o diretório principal (sem subdiretórios)
  python run_etl.py --diretorio "C:\\XMLs\\2024" --no-recursivo

  # Processar arquivos específicos
  python run_etl.py --arquivos "nota1.xml" "nota2.xml" "nota3.xml"
        """
    )
    
    # Argumentos
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Inicializa o banco de dados criando todas as tabelas'
    )
    
    parser.add_argument(
        '--diretorio', '-d',
        type=str,
        help='Diretório contendo arquivos XML (usa diretório padrão se não especificado)'
    )
    
    parser.add_argument(
        '--arquivos', '-a',
        nargs='+',
        help='Lista de arquivos XML específicos para processar'
    )
    
    parser.add_argument(
        '--no-recursivo',
        action='store_true',
        help='Não processar subdiretórios (apenas quando usando --diretorio)'
    )
    
    parser.add_argument(
        '--tipo',
        choices=['completo', 'incremental'],
        default='completo',
        help='Tipo de processamento (padrão: completo)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Caminho para arquivo de configuração .env.etl alternativo'
    )
    
    parser.add_argument(
        '--no-delete',
        action='store_true',
        help='Não deletar arquivos após processamento (sobrescreve configuração)'
    )
    
    parser.add_argument(
        '--db-url',
        type=str,
        help=f'URL de conexão do banco de dados (padrão: {DATABASE_URL})'
    )
    
    args = parser.parse_args()
    
    # Exibir banner
    exibir_banner()
    
    # Carregar configuração alternativa se especificada
    if args.config:
        os.environ['ETL_CONFIG_PATH'] = args.config
        config.reload()
        print(f"Usando arquivo de configuração: {args.config}\n")
    
    # Sobrescrever opção de deletar se --no-delete foi passado
    if args.no_delete:
        os.environ['DELETAR_APOS_PROCESSAR'] = 'false'
        config.reload()
        print("Modo: Arquivos NÃO serão deletados após processamento\n")
    
    # Configurar URL do banco se fornecida
    if args.db_url:
        os.environ['ETL_DATABASE_URL'] = args.db_url
        print(f"Usando banco de dados: {args.db_url}\n")
    else:
        print(f"Usando banco de dados: {DATABASE_URL}\n")
    
    # Inicializar banco de dados
    if args.init_db:
        try:
            inicializar_banco()
            print("Banco de dados inicializado com sucesso!")
            return 0
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {e}")
            return 1
    
    # Validar argumentos - permitir execução sem argumentos para usar diretório padrão
    if not args.diretorio and not args.arquivos:
        if not config.diretorio_padrao:
            print("Erro: Você deve especificar --diretorio, --arquivos ou configurar DIRETORIO_PADRAO no .env.etl")
            print("Use --help para ver as opções disponíveis")
            return 1
        
        print(f"Usando diretório padrão: {config.diretorio_padrao}\n")
    
    # Criar pipeline
    pipeline = ETLPipeline()
    
    try:
        # Processar diretório
        if args.diretorio or not args.arquivos:
            diretorio = args.diretorio or config.diretorio_padrao
            
            if not os.path.isdir(diretorio):
                print(f"Erro: Diretório não encontrado: {diretorio}")
                return 1
            
            recursivo = not args.no_recursivo
            stats = pipeline.processar_diretorio(
                diretorio=diretorio,
                tipo_processamento=args.tipo,
                recursivo=recursivo
            )
        
        # Processar arquivos específicos
        elif args.arquivos:
            # Validar arquivos
            arquivos_invalidos = [a for a in args.arquivos if not os.path.isfile(a)]
            if arquivos_invalidos:
                print(f"Erro: Arquivos não encontrados:")
                for arq in arquivos_invalidos:
                    print(f"  - {arq}")
                return 1
            
            stats = pipeline.processar_arquivos_lista(
                arquivos=args.arquivos,
                tipo_processamento=args.tipo
            )
        
        # Verificar se houve erros
        if stats['erros'] > 0:
            print(f"\n⚠ Processamento concluído com {stats['erros']} erro(s)")
            return 1
        
        print("\n✓ Processamento concluído com sucesso!")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠ Processamento interrompido pelo usuário")
        return 130
    
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        return 1


def exibir_banner():
    """Exibe banner do serviço ETL."""
    banner = """
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                     SERVIÇO ETL - DOCUMENTOS FISCAIS                       ║
║                                                                            ║
║                  Extração, Transformação e Carga de XMLs                   ║
║                          NF-e e NFC-e para Datalake                        ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


if __name__ == '__main__':
    sys.exit(main())
