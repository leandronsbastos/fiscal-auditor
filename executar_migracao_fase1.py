"""
Script para executar a migração 003 - Campos Críticos Fase 1
"""
import psycopg2
import os

# Obter URL do banco do ambiente ou usar padrão
DATABASE_URL = os.getenv(
    "ETL_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/fiscal_datalake"
)

# Parsear a URL
# postgresql://user:password@host:port/database
parts = DATABASE_URL.replace('postgresql://', '').split('@')
user_pass = parts[0].split(':')
host_port_db = parts[1].split('/')
host_port = host_port_db[0].split(':')

DB_USER = user_pass[0]
DB_PASSWORD = user_pass[1]
DB_HOST = host_port[0]
DB_PORT = int(host_port[1]) if len(host_port) > 1 else 5432
DB_NAME = host_port_db[1]

def executar_migracao():
    """Executa a migração SQL."""
    print("=" * 80)
    print("EXECUTANDO MIGRAÇÃO 003 - Campos Críticos Fase 1")
    print("=" * 80)
    
    # Ler arquivo SQL
    with open('etl_service/migrations/003_adicionar_campos_criticos_fase1.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Conectar ao banco
    print(f"\nConectando ao banco {DB_NAME}...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        # Executar migração
        print("Executando SQL...")
        cursor.execute(sql)
        print("✓ Migração executada com sucesso!")
        
        # Verificar campos adicionados na tabela nfe
        print("\n" + "=" * 80)
        print("VERIFICANDO CAMPOS NA TABELA NFE")
        print("=" * 80)
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'nfe' 
            AND column_name IN (
                'indicador_presenca', 'indicador_final', 'indicador_intermediador',
                'codigo_municipio_fg_ibs', 'processo_emissao', 'versao_processo',
                'natureza_operacao', 'quantidade_bc_mono', 'valor_icms_mono',
                'tipo_integracao_pagamento', 'cnpj_intermediador'
            )
            ORDER BY column_name
        """)
        
        print("\nCampos encontrados na tabela nfe:")
        for row in cursor.fetchall():
            print(f"  • {row[0]}: {row[1]}")
        
        # Verificar campos adicionados na tabela nfe_item
        print("\n" + "=" * 80)
        print("VERIFICANDO CAMPOS NA TABELA NFE_ITEM")
        print("=" * 80)
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'nfe_item' 
            AND column_name IN (
                'codigo_beneficio_fiscal', 'codigo_beneficio_fiscal_ibs',
                'codigo_credito_presumido', 'percentual_credito_presumido',
                'indicador_escala_relevante', 'cnpj_fabricante',
                'quantidade_bc_mono', 'aliquota_adrem_mono', 'valor_icms_mono'
            )
            ORDER BY column_name
        """)
        
        print("\nCampos encontrados na tabela nfe_item:")
        for row in cursor.fetchall():
            print(f"  • {row[0]}: {row[1]}")
        
        # Contar registros
        print("\n" + "=" * 80)
        print("ESTATÍSTICAS DO BANCO")
        print("=" * 80)
        cursor.execute("SELECT COUNT(*) FROM nfe")
        count_nfe = cursor.fetchone()[0]
        print(f"Total de NF-es: {count_nfe}")
        
        cursor.execute("SELECT COUNT(*) FROM nfe_item")
        count_items = cursor.fetchone()[0]
        print(f"Total de itens: {count_items}")
        
        print("\n" + "=" * 80)
        print("✓ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Erro ao executar migração: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    executar_migracao()
