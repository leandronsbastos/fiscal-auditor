"""
Script para executar migração SQL - Adicionar campos IBS/CBS.

Execute este script para adicionar os campos da reforma tributária ao banco de dados.
"""
import os
from etl_service.database import engine
from sqlalchemy import text

def executar_migracao():
    """Executa a migração SQL."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    migration_file = os.path.join(script_dir, 'etl_service', 'migrations', '002_adicionar_campos_reforma_tributaria.sql')
    
    print("=" * 80)
    print("EXECUTANDO MIGRAÇÃO: Adicionar campos IBS/CBS (Reforma Tributária)")
    print("=" * 80)
    print()
    
    # Ler arquivo SQL
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Usar engine global
    try:
        with engine.connect() as conn:
            # Executar cada comando SQL separadamente
            commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
            
            for i, command in enumerate(commands, 1):
                if command:
                    print(f"[{i}/{len(commands)}] Executando comando...")
                    conn.execute(text(command))
                    conn.commit()
                    print(f"  ✓ Sucesso")
            
            print()
            print("=" * 80)
            print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 80)
            print()
            print("Os seguintes campos foram adicionados:")
            print()
            print("Tabela 'nfe' (totalizadores):")
            print("  - valor_ibs")
            print("  - valor_cbs")
            print()
            print("Tabela 'nfe_item' (itens):")
            print("  - situacao_tributaria_ibscbs")
            print("  - base_calculo_ibs")
            print("  - aliquota_ibs")
            print("  - valor_ibs")
            print("  - base_calculo_cbs")
            print("  - aliquota_cbs")
            print("  - valor_cbs")
            print()
            
    except Exception as e:
        print()
        print("=" * 80)
        print("ERRO AO EXECUTAR MIGRAÇÃO!")
        print("=" * 80)
        print(f"Erro: {str(e)}")
        print()
        raise

if __name__ == '__main__':
    executar_migracao()
