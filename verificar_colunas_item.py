import psycopg2
import os

DATABASE_URL = os.getenv("ETL_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fiscal_datalake")
parts = DATABASE_URL.replace('postgresql://', '').split('@')
user_pass = parts[0].split(':')
host_port_db = parts[1].split('/')
host_port = host_port_db[0].split(':')

conn = psycopg2.connect(
    host=host_port[0],
    port=int(host_port[1]) if len(host_port) > 1 else 5432,
    dbname=host_port_db[1],
    user=user_pass[0],
    password=user_pass[1]
)
cursor = conn.cursor()

print("Colunas da tabela nfe_item relacionadas aos campos da Fase 1:")
cursor.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name='nfe_item' 
    AND (column_name LIKE '%mono%' OR column_name LIKE '%beneficio%' OR column_name LIKE '%credito%' OR column_name LIKE '%escala%' OR column_name LIKE '%fabricante%')
    ORDER BY column_name
""")
for row in cursor.fetchall():
    print(f"  {row[0]}")

cursor.close()
conn.close()
