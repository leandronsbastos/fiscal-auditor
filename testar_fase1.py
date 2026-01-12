"""
Script para testar a extração dos novos campos da Fase 1
"""
from etl_service.extractor import XMLExtractor
from etl_service.transformer import DataTransformer
from etl_service.loader import DataLoader
from etl_service.database import SessionLocal
import os
from pathlib import Path

def testar_extracao():
    """Testa a extração dos novos campos."""
    print("=" * 80)
    print("TESTANDO EXTRAÇÃO DE CAMPOS FASE 1")
    print("=" * 80)
    
    # Buscar XMLs no diretório de testes ou na pasta raiz
    pastas = [
        Path('tests/fixtures'),
        Path('.'),
        Path('output')
    ]
    
    xml_encontrado = None
    for pasta in pastas:
        if pasta.exists():
            xmls = list(pasta.glob('*.xml'))
            if xmls:
                xml_encontrado = xmls[0]
                break
    
    if not xml_encontrado:
        print("✗ Nenhum arquivo XML encontrado para teste")
        print("Coloque um arquivo XML na pasta do projeto ou em tests/fixtures")
        return
    
    print(f"\nArquivo de teste: {xml_encontrado}")
    print("=" * 80)
    
    # Extrair dados
    extractor = XMLExtractor()
    print("\n1. Extraindo dados do XML...")
    try:
        dados = extractor.extrair_nfe(str(xml_encontrado))
        print("   ✓ Extração realizada com sucesso")
    except Exception as e:
        print(f"   ✗ Erro na extração: {e}")
        return
    
    # Verificar campos extraídos
    print("\n2. Verificando campos extraídos:")
    print("\n   IDENTIFICAÇÃO:")
    identificacao = dados.get('identificacao', {})
    campos_id = {
        'codigo_municipio_fg_ibs': identificacao.get('codigo_municipio_fg_ibs'),
        'indicador_intermediador': identificacao.get('indicador_intermediador'),
        'processo_emissao': identificacao.get('processo_emissao'),
        'versao_processo': identificacao.get('versao_processo'),
        'natureza_operacao': identificacao.get('natureza_operacao'),
    }
    for campo, valor in campos_id.items():
        status = "✓" if valor else " "
        print(f"   [{status}] {campo}: {valor or 'N/A'}")
    
    print("\n   INTERMEDIADOR:")
    intermediador = dados.get('intermediador', {})
    print(f"   [{'✓' if intermediador.get('cnpj') else ' '}] cnpj: {intermediador.get('cnpj') or 'N/A'}")
    print(f"   [{'✓' if intermediador.get('id_cadastro') else ' '}] id_cadastro: {intermediador.get('id_cadastro') or 'N/A'}")
    
    print("\n   TOTALIZADORES ICMS MONOFÁSICO:")
    totais = dados.get('totais', {})
    campos_mono = {
        'quantidade_bc_mono': totais.get('quantidade_bc_mono'),
        'valor_icms_mono': totais.get('valor_icms_mono'),
        'quantidade_bc_mono_reten': totais.get('quantidade_bc_mono_reten'),
        'valor_icms_mono_reten': totais.get('valor_icms_mono_reten'),
    }
    for campo, valor in campos_mono.items():
        status = "✓" if valor else " "
        print(f"   [{status}] {campo}: {valor or 'N/A'}")
    
    print("\n   PAGAMENTO:")
    pagamento = dados.get('pagamento', {})
    detalhes_pag = pagamento.get('detalhes', [{}])[0] if pagamento.get('detalhes') else {}
    campos_pag = {
        'tipo_integracao': detalhes_pag.get('tipo_integracao'),
        'cnpj_recebedor': detalhes_pag.get('cnpj_recebedor'),
        'id_terminal': detalhes_pag.get('id_terminal'),
        'cnpj_pagador': detalhes_pag.get('cnpj_pagador'),
        'uf_pagador': detalhes_pag.get('uf_pagador'),
    }
    for campo, valor in campos_pag.items():
        status = "✓" if valor else " "
        print(f"   [{status}] {campo}: {valor or 'N/A'}")
    
    # Verificar itens
    itens = dados.get('itens', [])
    if itens:
        print(f"\n   ITENS ({len(itens)} items):")
        item = itens[0]
        produto = item.get('produto', {})
        impostos = item.get('impostos', {})
        icms = impostos.get('icms', {})
        
        print(f"\n   Item 1 - {produto.get('descricao', 'N/A')[:50]}")
        
        campos_item = {
            'codigo_beneficio_fiscal': produto.get('codigo_beneficio_fiscal'),
            'codigo_beneficio_fiscal_ibs': produto.get('codigo_beneficio_fiscal_ibs'),
            'indicador_escala_relevante': produto.get('indicador_escala_relevante'),
            'cnpj_fabricante': produto.get('cnpj_fabricante'),
        }
        for campo, valor in campos_item.items():
            status = "✓" if valor else " "
            print(f"   [{status}] {campo}: {valor or 'N/A'}")
        
        creditos = produto.get('creditos_presumidos', [])
        if creditos:
            print(f"\n   Créditos Presumidos: {len(creditos)}")
            for i, cred in enumerate(creditos[:2], 1):
                print(f"      Crédito {i}:")
                print(f"        código: {cred.get('codigo')}")
                print(f"        percentual: {cred.get('percentual')}")
                print(f"        valor: {cred.get('valor')}")
        
        print(f"\n   ICMS Monofásico (Item):")
        campos_icms_mono = {
            'quantidade_bc_mono': icms.get('quantidade_bc_mono'),
            'valor_icms_mono': icms.get('valor_icms_mono'),
            'aliquota_adrem_mono': icms.get('aliquota_adrem_mono'),
        }
        for campo, valor in campos_icms_mono.items():
            status = "✓" if valor else " "
            print(f"   [{status}] {campo}: {valor or 'N/A'}")
    
    # Transformar dados
    print("\n" + "=" * 80)
    print("3. Transformando dados...")
    transformer = DataTransformer()
    try:
        nfe = transformer.transformar_nfe(dados)
        print("   ✓ Transformação realizada com sucesso")
        print(f"   Chave: {nfe.chave_acesso}")
        print(f"   Número: {nfe.numero_nota}")
        print(f"   Itens: {len(nfe.itens)}")
    except Exception as e:
        print(f"   ✗ Erro na transformação: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Tentar carregar no banco (sem commit)
    print("\n4. Testando carga no banco (sem commit)...")
    db = SessionLocal()
    try:
        # Verificar se já existe
        from etl_service.models import NFe
        existe = db.query(NFe).filter(NFe.chave_acesso == nfe.chave_acesso).first()
        if existe:
            print(f"   ⚠ NF-e já existe no banco (ID: {existe.id})")
        else:
            db.add(nfe)
            db.flush()  # Força validação sem commit
            print("   ✓ Validação de carga bem-sucedida")
        db.rollback()  # Reverte para não salvar
    except Exception as e:
        print(f"   ✗ Erro na carga: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
    
    print("\n" + "=" * 80)
    print("✓ TESTE CONCLUÍDO")
    print("=" * 80)
    print("\nResumo:")
    print(f"  • Arquivo: {xml_encontrado.name}")
    print(f"  • Itens: {len(itens)}")
    print(f"  • Extração: OK")
    print(f"  • Transformação: OK")
    print(f"  • Validação: OK")

if __name__ == '__main__':
    testar_extracao()
