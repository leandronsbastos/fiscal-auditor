"""
Script para inicializar o banco de dados PostgreSQL.
"""
from fiscal_auditor.database import init_db, engine
from fiscal_auditor.db_models import Base

def create_database():
    """Cria todas as tabelas no banco de dados."""
    print("Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tabelas criadas com sucesso!")
    print()
    print("Tabelas criadas:")
    print("  - usuarios")
    print("  - empresas")
    print("  - usuario_empresa (tabela de relacionamento)")
    print("  - analises")
    print("  - documentos_fiscais")
    print()
    print("Configure a variável de ambiente DATABASE_URL para conectar:")
    print('  DATABASE_URL="postgresql://usuario:senha@host:porta/banco"')
    print()
    print("Exemplo:")
    print('  DATABASE_URL="postgresql://postgres:postgres@localhost:5432/fiscal_auditor"')

if __name__ == "__main__":
    create_database()
