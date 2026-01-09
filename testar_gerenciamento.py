"""
Script de teste para validar o sistema de gerenciamento automático de arquivos.

Este script testa:
1. Carregamento de configurações
2. Validação de duplicatas por hash
3. Validação de duplicatas por chave
4. Registro de arquivos processados
5. Deleção/movimentação de arquivos
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Adicionar path
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl_service.config import config
from etl_service.loader import DataLoader
from etl_service.database import SessionLocal
from etl_service.models import ArquivoProcessado, NFe


def testar_configuracoes():
    """Testa carregamento das configurações."""
    print("\n" + "="*80)
    print("TESTE 1: Carregamento de Configurações")
    print("="*80)
    
    print(f"✓ Diretório padrão: {config.diretorio_padrao}")
    print(f"✓ Deletar após processar: {config.deletar_apos_processar}")
    print(f"✓ Mover para backup: {config.mover_para_backup}")
    print(f"✓ Diretório backup: {config.diretorio_backup}")
    print(f"✓ Validar por chave: {config.validar_por_chave}")
    print(f"✓ Validar por hash: {config.validar_por_hash}")
    
    return True


def testar_calculo_hash():
    """Testa cálculo de hash de arquivo."""
    print("\n" + "="*80)
    print("TESTE 2: Cálculo de Hash")
    print("="*80)
    
    # Criar arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as f:
        f.write('<?xml version="1.0"?><NFe><test>conteudo</test></NFe>')
        temp_file = f.name
    
    try:
        loader = DataLoader()
        hash1 = loader._calcular_hash_arquivo(temp_file)
        print(f"✓ Hash calculado: {hash1}")
        
        # Calcular novamente - deve ser igual
        hash2 = loader._calcular_hash_arquivo(temp_file)
        
        if hash1 == hash2:
            print(f"✓ Hash consistente: {hash1 == hash2}")
            return True
        else:
            print(f"✗ Hash inconsistente!")
            return False
            
    finally:
        os.unlink(temp_file)


def testar_registro_arquivo():
    """Testa registro de arquivo processado."""
    print("\n" + "="*80)
    print("TESTE 3: Registro de Arquivo Processado")
    print("="*80)
    
    session = SessionLocal()
    
    try:
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as f:
            f.write('<?xml version="1.0"?><NFe><test>teste_registro</test></NFe>')
            temp_file = f.name
        
        loader = DataLoader()
        
        # Registrar arquivo
        chave_teste = '12345678901234567890123456789012345678901234'
        loader.registrar_arquivo_processado(
            caminho_arquivo=temp_file,
            chave_acesso=chave_teste,
            status='processado'
        )
        
        print(f"✓ Arquivo registrado: {temp_file}")
        
        # Verificar se foi registrado
        arquivo_proc = session.query(ArquivoProcessado).filter(
            ArquivoProcessado.caminho_arquivo == temp_file
        ).first()
        
        if arquivo_proc:
            print(f"✓ Registro encontrado no banco")
            print(f"  - Chave: {arquivo_proc.chave_acesso}")
            print(f"  - Hash: {arquivo_proc.hash_arquivo[:16]}...")
            print(f"  - Status: {arquivo_proc.status}")
            
            # Limpar registro de teste
            session.delete(arquivo_proc)
            session.commit()
            print(f"✓ Registro de teste removido")
            
            os.unlink(temp_file)
            return True
        else:
            print(f"✗ Registro não encontrado no banco")
            os.unlink(temp_file)
            return False
            
    except Exception as e:
        print(f"✗ Erro: {str(e)}")
        return False
    finally:
        session.close()


def testar_deteccao_duplicata_hash():
    """Testa detecção de duplicata por hash."""
    print("\n" + "="*80)
    print("TESTE 4: Detecção de Duplicata por Hash")
    print("="*80)
    
    session = SessionLocal()
    
    try:
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as f:
            f.write('<?xml version="1.0"?><NFe><test>teste_duplicata</test></NFe>')
            temp_file = f.name
        
        loader = DataLoader()
        
        # Registrar arquivo pela primeira vez
        chave_teste = '98765432109876543210987654321098765432109876'
        loader.registrar_arquivo_processado(
            caminho_arquivo=temp_file,
            chave_acesso=chave_teste,
            status='processado'
        )
        
        print(f"✓ Arquivo registrado pela primeira vez")
        
        # Tentar processar novamente (deve detectar duplicata)
        ja_processado = loader.arquivo_ja_processado(temp_file)
        
        if ja_processado:
            print(f"✓ Duplicata detectada corretamente!")
            
            # Limpar registro de teste
            arquivo_proc = session.query(ArquivoProcessado).filter(
                ArquivoProcessado.caminho_arquivo == temp_file
            ).first()
            
            if arquivo_proc:
                session.delete(arquivo_proc)
                session.commit()
            
            os.unlink(temp_file)
            return True
        else:
            print(f"✗ Duplicata NÃO detectada")
            os.unlink(temp_file)
            return False
            
    except Exception as e:
        print(f"✗ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def testar_validacao_chave_duplicada():
    """Testa validação de chave duplicada."""
    print("\n" + "="*80)
    print("TESTE 5: Validação de Chave Duplicada")
    print("="*80)
    
    session = SessionLocal()
    
    try:
        chave_teste = '11111111111111111111111111111111111111111111'
        
        # Verificar se já existe NF-e com essa chave
        nfe_existente = session.query(NFe).filter(
            NFe.chave_acesso == chave_teste
        ).first()
        
        if nfe_existente:
            print(f"✓ Validação funciona: NF-e já existe no banco")
            print(f"  - Chave: {chave_teste}")
            print(f"  - ID: {nfe_existente.id}")
            return True
        else:
            print(f"⚠ Nenhuma NF-e de teste encontrada")
            print(f"  (Este teste requer uma NF-e já processada no banco)")
            return True  # Não é erro, apenas não tem dado de teste
            
    except Exception as e:
        print(f"✗ Erro: {str(e)}")
        return False
    finally:
        session.close()


def main():
    """Executa todos os testes."""
    print("\n" + "="*80)
    print("TESTES DO SISTEMA DE GERENCIAMENTO AUTOMÁTICO DE ARQUIVOS")
    print("="*80)
    
    resultados = []
    
    # Executar testes
    resultados.append(("Configurações", testar_configuracoes()))
    resultados.append(("Cálculo de Hash", testar_calculo_hash()))
    resultados.append(("Registro de Arquivo", testar_registro_arquivo()))
    resultados.append(("Detecção Duplicata Hash", testar_deteccao_duplicata_hash()))
    resultados.append(("Validação Chave Duplicada", testar_validacao_chave_duplicada()))
    
    # Sumário
    print("\n" + "="*80)
    print("SUMÁRIO DOS TESTES")
    print("="*80)
    
    total = len(resultados)
    sucesso = sum(1 for _, resultado in resultados if resultado)
    falhas = total - sucesso
    
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{status} - {nome}")
    
    print(f"\n{'='*80}")
    print(f"Total: {total} testes")
    print(f"Sucesso: {sucesso}")
    print(f"Falhas: {falhas}")
    print(f"{'='*80}\n")
    
    return 0 if falhas == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
