"""
Script para reprocessar TODAS as NF-es existentes com campos da Fase 1
"""
from etl_service.database import SessionLocal
from etl_service.models import NFe
from etl_service.extractor import XMLExtractor
from etl_service.transformer import DataTransformer
from datetime import datetime
import time

def reprocessar_todas_nfes():
    """Reprocessa todas as NF-es existentes para extrair campos da Fase 1."""
    print("=" * 80)
    print("REPROCESSAMENTO COMPLETO - CAMPOS FASE 1")
    print("=" * 80)
    
    db = SessionLocal()
    extractor = XMLExtractor()
    transformer = DataTransformer()
    
    inicio = time.time()
    
    try:
        # Contar total de NF-es com XML
        total = db.query(NFe).filter(NFe.xml_completo.isnot(None)).count()
        
        print(f"\nTotal de NF-es com XML: {total}")
        
        if total == 0:
            print("Nenhuma NF-e com XML disponível")
            return
        
        resposta = input(f"\nDeseja reprocessar todas as {total} NF-es? (s/n): ")
        if resposta.lower() != 's':
            print("Operação cancelada")
            return
        
        print("\nIniciando reprocessamento completo...\n")
        
        # Processar em lotes de 50
        lote_size = 50
        processadas = 0
        atualizadas = 0
        erros = 0
        
        for offset in range(0, total, lote_size):
            nfes = db.query(NFe).filter(
                NFe.xml_completo.isnot(None)
            ).offset(offset).limit(lote_size).all()
            
            for nfe in nfes:
                processadas += 1
                
                if processadas % 10 == 0:
                    tempo_decorrido = time.time() - inicio
                    velocidade = processadas / tempo_decorrido if tempo_decorrido > 0 else 0
                    tempo_restante = (total - processadas) / velocidade if velocidade > 0 else 0
                    print(f"Progresso: {processadas}/{total} ({processadas*100//total}%) - "
                          f"{velocidade:.1f} NF-es/s - Restante: {tempo_restante/60:.1f} min")
                
                try:
                    import tempfile
                    import os
                    
                    # Criar arquivo temporário
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as tmp:
                        tmp.write(nfe.xml_completo)
                        tmp_path = tmp.name
                    
                    try:
                        # Extrair dados
                        dados = extractor.extrair_nfe(tmp_path)
                        
                        identificacao = dados.get('identificacao', {})
                        totais = dados.get('totais', {})
                        pagamento = dados.get('pagamento', {})
                        intermediador = dados.get('intermediador', {})
                        
                        campos_modificados = False
                        
                        # Atualizar campos NFe
                        if identificacao.get('codigo_municipio_fg_ibs') and not nfe.codigo_municipio_fg_ibs:
                            nfe.codigo_municipio_fg_ibs = identificacao.get('codigo_municipio_fg_ibs')
                            campos_modificados = True
                        
                        if identificacao.get('indicador_intermediador') and not nfe.indicador_intermediador:
                            nfe.indicador_intermediador = identificacao.get('indicador_intermediador')
                            campos_modificados = True
                        
                        if identificacao.get('natureza_operacao') and not nfe.natureza_operacao:
                            nfe.natureza_operacao = identificacao.get('natureza_operacao')
                            campos_modificados = True
                        
                        if identificacao.get('consumidor_final') and not nfe.indicador_final:
                            nfe.indicador_final = identificacao.get('consumidor_final')
                            campos_modificados = True
                        
                        if identificacao.get('presenca_comprador') and not nfe.indicador_presenca:
                            nfe.indicador_presenca = identificacao.get('presenca_comprador')
                            campos_modificados = True
                        
                        if identificacao.get('processo_emissao') and not nfe.processo_emissao:
                            nfe.processo_emissao = identificacao.get('processo_emissao')
                            campos_modificados = True
                        
                        if identificacao.get('versao_processo') and not nfe.versao_processo:
                            nfe.versao_processo = identificacao.get('versao_processo')
                            campos_modificados = True
                        
                        # ICMS Monofásico
                        if totais.get('quantidade_bc_mono') and not nfe.quantidade_bc_mono:
                            nfe.quantidade_bc_mono = transformer._to_decimal(totais.get('quantidade_bc_mono'))
                            campos_modificados = True
                        
                        if totais.get('valor_icms_mono') and not nfe.valor_icms_mono:
                            nfe.valor_icms_mono = transformer._to_decimal(totais.get('valor_icms_mono'))
                            campos_modificados = True
                        
                        # Pagamento
                        detalhes_pag = pagamento.get('detalhes', [{}])[0] if pagamento.get('detalhes') else {}
                        if detalhes_pag.get('tipo_integracao') and not nfe.tipo_integracao_pagamento:
                            nfe.tipo_integracao_pagamento = detalhes_pag.get('tipo_integracao')
                            campos_modificados = True
                        
                        if detalhes_pag.get('cnpj_credenciadora') and not nfe.cnpj_instituicao_pagamento:
                            nfe.cnpj_instituicao_pagamento = detalhes_pag.get('cnpj_credenciadora')
                            campos_modificados = True
                        
                        # Intermediador
                        if intermediador.get('cnpj') and not nfe.cnpj_intermediador:
                            nfe.cnpj_intermediador = intermediador.get('cnpj')
                            campos_modificados = True
                        
                        if intermediador.get('id_cadastro') and not nfe.identificador_intermediador:
                            nfe.identificador_intermediador = intermediador.get('id_cadastro')
                            campos_modificados = True
                        
                        # Atualizar itens
                        itens_data = dados.get('itens', [])
                        for item_data in itens_data:
                            numero_item = item_data.get('numero_item')
                            if not numero_item:
                                continue
                            
                            item = next((i for i in nfe.itens if i.numero_item == int(numero_item)), None)
                            if not item:
                                continue
                            
                            produto = item_data.get('produto', {})
                            impostos = item_data.get('impostos', {})
                            icms = impostos.get('icms', {})
                            
                            if produto.get('codigo_beneficio_fiscal') and not item.codigo_beneficio_fiscal:
                                item.codigo_beneficio_fiscal = produto.get('codigo_beneficio_fiscal')
                                campos_modificados = True
                            
                            if produto.get('codigo_beneficio_fiscal_ibs') and not item.codigo_beneficio_fiscal_ibs:
                                item.codigo_beneficio_fiscal_ibs = produto.get('codigo_beneficio_fiscal_ibs')
                                campos_modificados = True
                            
                            if produto.get('indicador_escala_relevante') and not item.indicador_escala_relevante:
                                item.indicador_escala_relevante = produto.get('indicador_escala_relevante')
                                campos_modificados = True
                            
                            if produto.get('cnpj_fabricante') and not item.cnpj_fabricante:
                                item.cnpj_fabricante = produto.get('cnpj_fabricante')
                                campos_modificados = True
                            
                            if icms.get('quantidade_bc_mono') and not item.quantidade_bc_mono:
                                item.quantidade_bc_mono = transformer._to_decimal(icms.get('quantidade_bc_mono'))
                                campos_modificados = True
                            
                            if icms.get('valor_icms_mono') and not item.valor_icms_mono:
                                item.valor_icms_mono = transformer._to_decimal(icms.get('valor_icms_mono'))
                                campos_modificados = True
                            
                            creditos = produto.get('creditos_presumidos', [])
                            if creditos and not item.codigo_credito_presumido:
                                primeiro = creditos[0]
                                item.codigo_credito_presumido = primeiro.get('codigo')
                                item.percentual_credito_presumido = transformer._to_decimal(primeiro.get('percentual'))
                                item.valor_credito_presumido = transformer._to_decimal(primeiro.get('valor'))
                                campos_modificados = True
                        
                        if campos_modificados:
                            atualizadas += 1
                        
                    finally:
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass
                        
                except Exception as e:
                    erros += 1
                    if erros <= 5:  # Mostrar apenas primeiros 5 erros
                        print(f"  Erro na NF-e {nfe.chave_acesso[:15]}...: {str(e)[:50]}")
            
            # Commit a cada lote
            db.commit()
        
        tempo_total = time.time() - inicio
        
        print("\n" + "=" * 80)
        print("REPROCESSAMENTO COMPLETO FINALIZADO")
        print("=" * 80)
        print(f"Total processadas: {processadas}")
        print(f"Atualizadas: {atualizadas}")
        print(f"Sem alterações: {processadas - atualizadas - erros}")
        print(f"Erros: {erros}")
        print(f"Tempo total: {tempo_total/60:.1f} minutos")
        print(f"Velocidade média: {processadas/tempo_total:.1f} NF-es/segundo")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Erro geral: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    reprocessar_todas_nfes()
