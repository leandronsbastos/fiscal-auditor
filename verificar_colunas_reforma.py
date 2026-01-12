from etl_service.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)

print("\n=== Colunas IBS/CBS na tabela 'nfe' ===")
nfe_cols = inspector.get_columns('nfe')
for col in nfe_cols:
    if 'ibs' in col['name'].lower() or 'cbs' in col['name'].lower():
        print(f"  ✓ {col['name']}: {col['type']}")

print("\n=== Colunas IBS/CBS na tabela 'nfe_item' ===")
item_cols = inspector.get_columns('nfe_item')
for col in item_cols:
    if 'ibs' in col['name'].lower() or 'cbs' in col['name'].lower():
        print(f"  ✓ {col['name']}: {col['type']}")

print("\n")
