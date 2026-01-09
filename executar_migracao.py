"""
Script para executar a migração SQL da tabela arquivos_processados.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from etl_service.database import engine
from sqlalchemy import text


def executar_migracao():
    """Executa a migração SQL para criar a tabela arquivos_processados."""
    
    print("\n" + "="*80)
    print("EXECUTANDO MIGRAÇÃO: Tabela arquivos_processados")
    print("="*80 + "\n")
    
    # Ler arquivo SQL
    sql_file = Path(__file__).parent / "etl_service" / "migrations" / "001_criar_tabela_arquivos_processados.sql"
    
    if not sql_file.exists():
        print(f"❌ Erro: Arquivo SQL não encontrado: {sql_file}")
        return 1
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✓ Arquivo SQL carregado: {sql_file.name}\n")
    
    try:
        with engine.connect() as conn:
            # Executar cada statement SQL
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement:
                    print(f"[{i}/{len(statements)}] Executando statement...")
                    conn.execute(text(statement))
                    conn.commit()
            
            print("\n" + "="*80)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*80)
            print("\nTabela 'arquivos_processados' criada com:")
            print("  - Estrutura completa")
            print("  - Índices otimizados")
            print("  - Comentários descritivos")
            print("\n")
            
            return 0
            
    except Exception as e:
        print("\n" + "="*80)
        print("❌ ERRO AO EXECUTAR MIGRAÇÃO")
        print("="*80)
        print(f"\nErro: {str(e)}\n")
        
        import traceback
        traceback.print_exc()
        
        return 1


if __name__ == '__main__':
    sys.exit(executar_migracao())
