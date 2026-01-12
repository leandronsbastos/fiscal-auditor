from etl_service.database import engine
from sqlalchemy import text

print("\n=== Adicionando colunas faltantes ===\n")

try:
    with engine.connect() as conn:
        # Adicionar valor_ibs na tabela nfe
        print("1. Adicionando valor_ibs na tabela nfe...")
        conn.execute(text("ALTER TABLE nfe ADD COLUMN IF NOT EXISTS valor_ibs NUMERIC(15, 2)"))
        conn.commit()
        print("   ✓ Sucesso")
        
        # Adicionar situacao_tributaria_ibscbs na tabela nfe_item
        print("2. Adicionando situacao_tributaria_ibscbs na tabela nfe_item...")
        conn.execute(text("ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS situacao_tributaria_ibscbs VARCHAR(2)"))
        conn.commit()
        print("   ✓ Sucesso")
        
        print("\n=== Colunas adicionadas com sucesso! ===\n")
        
except Exception as e:
    print(f"\n❌ Erro: {e}\n")
