"""
Script para adicionar colunas do ICMS Monofásico (NT 2023.003) na tabela nfe_item
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from etl_service.config import config

def adicionar_colunas_icms_mono():
    """Adiciona colunas do ICMS Monofásico na tabela nfe_item"""
    
    engine = create_engine(config.database_url)
    
    sql = """
    ALTER TABLE nfe_item 
    ADD COLUMN IF NOT EXISTS quantidade_bc_mono NUMERIC(15, 4),
    ADD COLUMN IF NOT EXISTS valor_icms_mono NUMERIC(15, 2),
    ADD COLUMN IF NOT EXISTS aliquota_adrem_mono NUMERIC(15, 4),
    ADD COLUMN IF NOT EXISTS quantidade_bc_mono_reten NUMERIC(15, 4),
    ADD COLUMN IF NOT EXISTS valor_icms_mono_reten NUMERIC(15, 2),
    ADD COLUMN IF NOT EXISTS aliquota_adrem_mono_reten NUMERIC(15, 4),
    ADD COLUMN IF NOT EXISTS quantidade_bc_mono_ret NUMERIC(15, 4),
    ADD COLUMN IF NOT EXISTS valor_icms_mono_ret NUMERIC(15, 2),
    ADD COLUMN IF NOT EXISTS aliquota_adrem_mono_ret NUMERIC(15, 4);
    """
    
    try:
        with engine.begin() as conn:
            conn.execute(text(sql))
            print("✓ Colunas do ICMS Monofásico adicionadas com sucesso!")
            
            # Verificar se as colunas foram criadas
            result = conn.execute(text("""
                SELECT column_name, data_type, numeric_precision, numeric_scale
                FROM information_schema.columns
                WHERE table_name = 'nfe_item'
                AND column_name LIKE '%mono%'
                ORDER BY column_name;
            """))
            
            print("\nColunas criadas:")
            for row in result:
                print(f"  - {row[0]}: {row[1]}({row[2]},{row[3]})")
                
    except Exception as e:
        print(f"✗ Erro ao adicionar colunas: {e}")
        raise
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("Adicionando colunas do ICMS Monofásico (NT 2023.003)...")
    print("=" * 80)
    adicionar_colunas_icms_mono()
    print("=" * 80)
    print("Migração concluída!")
