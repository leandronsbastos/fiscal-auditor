"""
Script de configuração inicial do serviço ETL.

Este script auxilia na configuração inicial do serviço ETL,
incluindo verificação de dependências e criação do banco de dados.
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))


def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas."""
    print("\n" + "=" * 80)
    print("Verificando dependências...")
    print("=" * 80 + "\n")
    
    dependencias = {
        'sqlalchemy': 'SQLAlchemy',
        'psycopg2': 'psycopg2-binary',
        'lxml': 'lxml',
    }
    
    faltando = []
    
    for modulo, nome in dependencias.items():
        try:
            __import__(modulo)
            print(f"✓ {nome} - OK")
        except ImportError:
            print(f"✗ {nome} - NÃO INSTALADO")
            faltando.append(nome)
    
    if faltando:
        print(f"\n⚠ Dependências faltando: {', '.join(faltando)}")
        print("\nPara instalar, execute:")
        print(f"  pip install {' '.join(faltando)}")
        return False
    
    print("\n✓ Todas as dependências estão instaladas!")
    return True


def verificar_postgresql():
    """Verifica conexão com PostgreSQL."""
    print("\n" + "=" * 80)
    print("Verificando conexão com PostgreSQL...")
    print("=" * 80 + "\n")
    
    try:
        import psycopg2
        from etl_service.database import DATABASE_URL
        
        print(f"URL de conexão: {DATABASE_URL}\n")
        
        # Extrair partes da URL
        # postgresql://usuario:senha@host:porta/banco
        url_parts = DATABASE_URL.replace('postgresql://', '').split('@')
        if len(url_parts) == 2:
            creds = url_parts[0].split(':')
            host_db = url_parts[1].split('/')
            
            user = creds[0] if len(creds) > 0 else 'postgres'
            password = creds[1] if len(creds) > 1 else 'postgres'
            host_port = host_db[0].split(':')
            host = host_port[0] if len(host_port) > 0 else 'localhost'
            port = host_port[1] if len(host_port) > 1 else '5432'
            dbname = host_db[1] if len(host_db) > 1 else 'postgres'
            
            # Tentar conectar ao PostgreSQL (banco postgres)
            try:
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    dbname='postgres'  # Conectar ao banco padrão
                )
                conn.close()
                print(f"✓ Conexão com PostgreSQL estabelecida!")
                print(f"  Host: {host}:{port}")
                
                # Verificar se o banco de destino existe
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    dbname='postgres'
                )
                cur = conn.cursor()
                cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{dbname}'")
                existe = cur.fetchone()
                cur.close()
                conn.close()
                
                if existe:
                    print(f"✓ Banco de dados '{dbname}' existe")
                else:
                    print(f"⚠ Banco de dados '{dbname}' não existe")
                    print(f"\nPara criar o banco, execute no PostgreSQL:")
                    print(f"  CREATE DATABASE {dbname};")
                    return False
                
                return True
                
            except psycopg2.OperationalError as e:
                print(f"✗ Erro ao conectar: {e}")
                print("\nVerifique:")
                print("  1. PostgreSQL está rodando?")
                print("  2. As credenciais estão corretas?")
                print("  3. O firewall permite conexões?")
                return False
        
    except ImportError:
        print("✗ psycopg2 não está instalado")
        return False
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False


def criar_estrutura_diretorios():
    """Cria estrutura de diretórios se necessário."""
    print("\n" + "=" * 80)
    print("Verificando estrutura de diretórios...")
    print("=" * 80 + "\n")
    
    diretorios = [
        'etl_service',
    ]
    
    for diretorio in diretorios:
        if os.path.exists(diretorio):
            print(f"✓ {diretorio} - OK")
        else:
            print(f"⚠ {diretorio} - NÃO EXISTE")
    
    print("\n✓ Estrutura de diretórios OK!")
    return True


def inicializar_banco_dados():
    """Inicializa o banco de dados."""
    print("\n" + "=" * 80)
    print("Inicializando banco de dados...")
    print("=" * 80 + "\n")
    
    try:
        from etl_service.pipeline import inicializar_banco
        
        inicializar_banco()
        print("✓ Banco de dados inicializado com sucesso!")
        print("\nTabelas criadas:")
        print("  - nfe")
        print("  - nfe_item")
        print("  - nfe_duplicata")
        print("  - etl_processamento")
        print("  - etl_log_processamento")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao inicializar banco: {e}")
        import traceback
        traceback.print_exc()
        return False


def exibir_instrucoes_uso():
    """Exibe instruções de uso."""
    print("\n" + "=" * 80)
    print("CONFIGURAÇÃO CONCLUÍDA!")
    print("=" * 80 + "\n")
    
    print("Próximos passos:")
    print("\n1. Para processar XMLs de um diretório:")
    print('   python run_etl.py --diretorio "C:\\XMLs\\2024"')
    
    print("\n2. Para processar arquivos específicos:")
    print('   python run_etl.py --arquivos "nota1.xml" "nota2.xml"')
    
    print("\n3. Para ver exemplos de uso:")
    print("   python exemplo_etl.py")
    
    print("\n4. Para ver todas as opções:")
    print("   python run_etl.py --help")
    
    print("\n5. Consulte a documentação completa em:")
    print("   etl_service/README.md")
    
    print("\n" + "=" * 80 + "\n")


def main():
    """Executa a configuração inicial."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "CONFIGURAÇÃO INICIAL DO SERVIÇO ETL" + " " * 23 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Verificar dependências
    if not verificar_dependencias():
        print("\n❌ Configure as dependências antes de continuar.")
        return 1
    
    # Verificar estrutura
    if not criar_estrutura_diretorios():
        print("\n❌ Estrutura de diretórios inválida.")
        return 1
    
    # Verificar PostgreSQL
    if not verificar_postgresql():
        print("\n❌ Configure o PostgreSQL antes de continuar.")
        print("\nDica: Se você está usando outro banco, ajuste ETL_DATABASE_URL")
        return 1
    
    # Perguntar se deseja inicializar o banco
    print("\n" + "=" * 80)
    resposta = input("Deseja inicializar o banco de dados agora? (s/n): ").lower()
    
    if resposta == 's':
        if not inicializar_banco_dados():
            print("\n❌ Erro ao inicializar banco de dados.")
            return 1
    else:
        print("\n⚠ Lembre-se de inicializar o banco antes de usar:")
        print("  python run_etl.py --init-db")
    
    # Exibir instruções
    exibir_instrucoes_uso()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
