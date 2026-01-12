"""
Script para reprocessar NF-es existentes e atualizar com campos da Fase 1
"""
from etl_service.database import SessionLocal
from etl_service.models import NFe, NFeItem
from etl_service.extractor import XMLExtractor
from etl_service.transformer import DataTransformer
from datetime import datetime
import traceback

def reprocessar_nfes():
    """Reprocessa NF-es existentes para extrair campos da Fase 1."""
    print("=" * 80)
    print("REPROCESSAMENTO - CAMPOS FASE 1")
    print("=" * 80)
    
    db = SessionLocal()
    extractor = XMLExtractor()
    transformer = DataTransformer()
    
    try:
        # Buscar NF-es que têm XML completo
        nfes = db.query(NFe).filter(
            NFe.xml_completo.isnot(None)
        ).limit(10).all()  # Processar primeiras 10 para teste
        
        total = len(nfes)
        print(f"\nNF-es encontradas com XML: {total}")
        
        if total == 0:
            print("Nenhuma NF-e com XML disponível para reprocessar")
            return
        
        print("\nIniciando reprocessamento...\n")
        
        processadas = 0
        erros = 0
        atualizadas = 0
        
        for i, nfe in enumerate(nfes, 1):
            print(f"[{i}/{total}] Chave: {nfe.chave_acesso[:20]}...")
            
            try:
                # Criar arquivo temporário com o XML
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as tmp:
                    tmp.write(nfe.xml_completo)
                    tmp_path = tmp.name
                
                try:
                    # Extrair dados
                    dados = extractor.extrair_nfe(tmp_path)
                    
                    # Atualizar campos da Fase 1 na NFe
                    identificacao = dados.get('identificacao', {})
                    totais = dados.get('totais', {})
                    pagamento = dados.get('pagamento', {})
                    intermediador = dados.get('intermediador', {})
                    
                    # Atualizar NFe
                    campos_atualizados = []
                    
                    if identificacao.get('codigo_municipio_fg_ibs'):
                        nfe.codigo_municipio_fg_ibs = identificacao.get('codigo_municipio_fg_ibs')
                        campos_atualizados.append('codigo_municipio_fg_ibs')
                    
                    if identificacao.get('indicador_intermediador'):
                        nfe.indicador_intermediador = identificacao.get('indicador_intermediador')
                        campos_atualizados.append('indicador_intermediador')
                    
                    if identificacao.get('natureza_operacao'):
                        nfe.natureza_operacao = identificacao.get('natureza_operacao')
                        campos_atualizados.append('natureza_operacao')
                    
                    if identificacao.get('consumidor_final'):
                        nfe.indicador_final = identificacao.get('consumidor_final')
                        campos_atualizados.append('indicador_final')
                    
                    if identificacao.get('presenca_comprador'):
                        nfe.indicador_presenca = identificacao.get('presenca_comprador')
                        campos_atualizados.append('indicador_presenca')
                    
                    # ICMS Monofásico
                    if totais.get('quantidade_bc_mono'):
                        nfe.quantidade_bc_mono = transformer._to_decimal(totais.get('quantidade_bc_mono'))
                        campos_atualizados.append('quantidade_bc_mono')
                    
                    if totais.get('valor_icms_mono'):
                        nfe.valor_icms_mono = transformer._to_decimal(totais.get('valor_icms_mono'))
                        campos_atualizados.append('valor_icms_mono')
                    
                    # Pagamento
                    detalhes_pag = pagamento.get('detalhes', [{}])[0] if pagamento.get('detalhes') else {}
                    if detalhes_pag.get('tipo_integracao'):
                        nfe.tipo_integracao_pagamento = detalhes_pag.get('tipo_integracao')
                        campos_atualizados.append('tipo_integracao_pagamento')
                    
                    # Intermediador
                    if intermediador.get('cnpj'):
                        nfe.cnpj_intermediador = intermediador.get('cnpj')
                        campos_atualizados.append('cnpj_intermediador')
                    
                    # Atualizar itens
                    itens_data = dados.get('itens', [])
                    for item_data in itens_data:
                        numero_item = item_data.get('numero_item')
                        if not numero_item:
                            continue
                        
                        # Buscar item correspondente
                        item = next((i for i in nfe.itens if i.numero_item == int(numero_item)), None)
                        if not item:
                            continue
                        
                        produto = item_data.get('produto', {})
                        impostos = item_data.get('impostos', {})
                        icms = impostos.get('icms', {})
                        
                        # Benefício fiscal
                        if produto.get('codigo_beneficio_fiscal'):
                            item.codigo_beneficio_fiscal = produto.get('codigo_beneficio_fiscal')
                        
                        # ICMS Monofásico
                        if icms.get('quantidade_bc_mono'):
                            item.quantidade_bc_mono = transformer._to_decimal(icms.get('quantidade_bc_mono'))
                        
                        if icms.get('valor_icms_mono'):
                            item.valor_icms_mono = transformer._to_decimal(icms.get('valor_icms_mono'))
                        
                        # Crédito presumido
                        creditos = produto.get('creditos_presumidos', [])
                        if creditos:
                            primeiro = creditos[0]
                            item.codigo_credito_presumido = primeiro.get('codigo')
                            item.percentual_credito_presumido = transformer._to_decimal(primeiro.get('percentual'))
                            item.valor_credito_presumido = transformer._to_decimal(primeiro.get('valor'))
                    
                    if campos_atualizados:
                        db.commit()
                        print(f"  ✓ Atualizada - {len(campos_atualizados)} campos: {', '.join(campos_atualizados[:3])}")
                        atualizadas += 1
                    else:
                        print(f"  → Sem novos dados")
                    
                    processadas += 1
                    
                finally:
                    # Remover arquivo temporário
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
                    
            except Exception as e:
                print(f"  ✗ Erro: {str(e)[:60]}")
                db.rollback()
                erros += 1
        
        print("\n" + "=" * 80)
        print("RESUMO DO REPROCESSAMENTO")
        print("=" * 80)
        print(f"Total processadas: {processadas}/{total}")
        print(f"Atualizadas com novos campos: {atualizadas}")
        print(f"Sem alterações: {processadas - atualizadas}")
        print(f"Erros: {erros}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Erro geral: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    reprocessar_nfes()
