"""
Transformador de dados - Módulo de Transformação do ETL.

Este módulo é responsável por transformar os dados extraídos dos XMLs
em objetos que podem ser persistidos no banco de dados.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
import json

from .models import NFe, NFeItem, NFeDuplicata


class DataTransformer:
    """
    Transformador de dados extraídos para modelos do banco de dados.
    
    Converte os dicionários retornados pelo extrator em objetos
    SQLAlchemy prontos para persistência.
    """

    def __init__(self):
        """Inicializa o transformador."""
        pass

    def transformar_nfe(self, dados_extraidos: Dict[str, Any]) -> NFe:
        """
        Transforma dados extraídos em objeto NFe.
        
        Args:
            dados_extraidos: Dicionário com dados extraídos do XML
            
        Returns:
            Objeto NFe pronto para persistir
        """
        identificacao = dados_extraidos.get('identificacao', {})
        emitente = dados_extraidos.get('emitente', {})
        destinatario = dados_extraidos.get('destinatario', {})
        totais = dados_extraidos.get('totais', {})
        transporte = dados_extraidos.get('transporte', {})
        cobranca = dados_extraidos.get('cobranca', {})
        pagamento = dados_extraidos.get('pagamento', {})
        info_adic = dados_extraidos.get('informacoes_adicionais', {})
        protocolo = dados_extraidos.get('protocolo', {})
        
        # Criar objeto NFe
        nfe = NFe(
            # Identificação
            chave_acesso=identificacao.get('chave_acesso'),
            numero_nota=identificacao.get('numero_nota'),
            serie=identificacao.get('serie'),
            modelo=identificacao.get('modelo'),
            tipo_emissao=identificacao.get('tipo_emissao'),
            tipo_operacao=identificacao.get('tipo_operacao'),
            finalidade_emissao=identificacao.get('finalidade_emissao'),
            
            # Datas
            data_emissao=identificacao.get('data_emissao'),
            data_saida_entrada=identificacao.get('data_saida_entrada'),
            data_autorizacao=protocolo.get('data_recebimento'),
            data_processamento_etl=datetime.now(),
            
            # Situação
            codigo_status=protocolo.get('codigo_status'),
            motivo_status=protocolo.get('motivo'),
            protocolo_autorizacao=protocolo.get('numero_protocolo'),
            situacao=self._determinar_situacao(protocolo.get('codigo_status')),
            
            # Emitente
            emitente_cnpj=emitente.get('cnpj'),
            emitente_cpf=emitente.get('cpf'),
            emitente_razao_social=emitente.get('razao_social'),
            emitente_nome_fantasia=emitente.get('nome_fantasia'),
            emitente_ie=emitente.get('inscricao_estadual'),
            emitente_im=emitente.get('inscricao_municipal'),
            emitente_cnae=emitente.get('cnae'),
            emitente_crt=emitente.get('regime_tributario'),
            emitente_logradouro=emitente.get('endereco', {}).get('logradouro'),
            emitente_numero=emitente.get('endereco', {}).get('numero'),
            emitente_complemento=emitente.get('endereco', {}).get('complemento'),
            emitente_bairro=emitente.get('endereco', {}).get('bairro'),
            emitente_codigo_municipio=emitente.get('endereco', {}).get('codigo_municipio'),
            emitente_municipio=emitente.get('endereco', {}).get('municipio'),
            emitente_uf=emitente.get('endereco', {}).get('uf'),
            emitente_cep=emitente.get('endereco', {}).get('cep'),
            emitente_telefone=emitente.get('endereco', {}).get('telefone'),
            
            # Destinatário
            destinatario_cnpj=destinatario.get('cnpj'),
            destinatario_cpf=destinatario.get('cpf'),
            destinatario_razao_social=destinatario.get('razao_social'),
            destinatario_ie=destinatario.get('inscricao_estadual'),
            destinatario_im=destinatario.get('inscricao_municipal'),
            destinatario_logradouro=destinatario.get('endereco', {}).get('logradouro'),
            destinatario_numero=destinatario.get('endereco', {}).get('numero'),
            destinatario_complemento=destinatario.get('endereco', {}).get('complemento'),
            destinatario_bairro=destinatario.get('endereco', {}).get('bairro'),
            destinatario_codigo_municipio=destinatario.get('endereco', {}).get('codigo_municipio'),
            destinatario_municipio=destinatario.get('endereco', {}).get('municipio'),
            destinatario_uf=destinatario.get('endereco', {}).get('uf'),
            destinatario_cep=destinatario.get('endereco', {}).get('cep'),
            destinatario_telefone=destinatario.get('endereco', {}).get('telefone'),
            destinatario_email=destinatario.get('email'),
            destinatario_indicador_ie=destinatario.get('indicador_ie'),
            
            # Totalizadores
            valor_produtos=self._to_decimal(totais.get('valor_produtos')),
            valor_frete=self._to_decimal(totais.get('valor_frete')),
            valor_seguro=self._to_decimal(totais.get('valor_seguro')),
            valor_desconto=self._to_decimal(totais.get('valor_desconto')),
            valor_outras_despesas=self._to_decimal(totais.get('valor_outras_despesas')),
            valor_ipi=self._to_decimal(totais.get('valor_ipi')),
            valor_total_nota=self._to_decimal(totais.get('valor_total_nota')),
            
            # ICMS
            base_calculo_icms=self._to_decimal(totais.get('base_calculo_icms')),
            valor_icms=self._to_decimal(totais.get('valor_icms')),
            valor_icms_desonerado=self._to_decimal(totais.get('valor_icms_desonerado')),
            base_calculo_icms_st=self._to_decimal(totais.get('base_calculo_icms_st')),
            valor_icms_st=self._to_decimal(totais.get('valor_icms_st')),
            valor_fcp=self._to_decimal(totais.get('valor_fcp')),
            valor_fcp_st=self._to_decimal(totais.get('valor_fcp_st')),
            valor_fcp_st_retido=self._to_decimal(totais.get('valor_fcp_st_retido')),
            
            # PIS/COFINS
            valor_pis=self._to_decimal(totais.get('valor_pis')),
            valor_cofins=self._to_decimal(totais.get('valor_cofins')),
            
            # Outros
            valor_aproximado_tributos=self._to_decimal(totais.get('valor_aproximado_tributos')),
            informacoes_adicionais_fisco=info_adic.get('informacoes_fisco'),
            informacoes_complementares=info_adic.get('informacoes_complementares'),
            
            # Transporte
            modalidade_frete=transporte.get('modalidade_frete'),
            transportadora_cnpj=transporte.get('transportadora', {}).get('cnpj'),
            transportadora_cpf=transporte.get('transportadora', {}).get('cpf'),
            transportadora_razao_social=transporte.get('transportadora', {}).get('razao_social'),
            transportadora_ie=transporte.get('transportadora', {}).get('inscricao_estadual'),
            transportadora_endereco=transporte.get('transportadora', {}).get('endereco'),
            transportadora_municipio=transporte.get('transportadora', {}).get('municipio'),
            transportadora_uf=transporte.get('transportadora', {}).get('uf'),
            veiculo_placa=transporte.get('veiculo', {}).get('placa'),
            veiculo_uf=transporte.get('veiculo', {}).get('uf'),
            veiculo_rntc=transporte.get('veiculo', {}).get('rntc'),
            
            # Volume
            quantidade_volumes=self._to_int(transporte.get('volumes', [{}])[0].get('quantidade')) if transporte.get('volumes') else None,
            especie_volumes=transporte.get('volumes', [{}])[0].get('especie') if transporte.get('volumes') else None,
            marca_volumes=transporte.get('volumes', [{}])[0].get('marca') if transporte.get('volumes') else None,
            numeracao_volumes=transporte.get('volumes', [{}])[0].get('numeracao') if transporte.get('volumes') else None,
            peso_liquido=self._to_decimal(transporte.get('volumes', [{}])[0].get('peso_liquido')) if transporte.get('volumes') else None,
            peso_bruto=self._to_decimal(transporte.get('volumes', [{}])[0].get('peso_bruto')) if transporte.get('volumes') else None,
            
            # Pagamento
            forma_pagamento=identificacao.get('forma_pagamento'),
            meio_pagamento=pagamento.get('detalhes', [{}])[0].get('forma') if pagamento.get('detalhes') else pagamento.get('forma'),
            valor_pagamento=self._to_decimal(pagamento.get('detalhes', [{}])[0].get('valor')) if pagamento.get('detalhes') else self._to_decimal(pagamento.get('valor')),
            
            # Cobrança
            numero_fatura=cobranca.get('fatura', {}).get('numero'),
            valor_original_fatura=self._to_decimal(cobranca.get('fatura', {}).get('valor_original')),
            valor_desconto_fatura=self._to_decimal(cobranca.get('fatura', {}).get('valor_desconto')),
            valor_liquido_fatura=self._to_decimal(cobranca.get('fatura', {}).get('valor_liquido')),
            
            # XML completo
            xml_completo=dados_extraidos.get('xml_completo'),
        )
        
        # Transformar itens
        itens_data = dados_extraidos.get('itens', [])
        nfe.itens = [self._transformar_item(item_data) for item_data in itens_data]
        
        # Transformar duplicatas
        duplicatas_data = cobranca.get('duplicatas', [])
        nfe.duplicatas = [self._transformar_duplicata(dup_data) for dup_data in duplicatas_data]
        
        return nfe

    def _transformar_item(self, item_data: Dict[str, Any]) -> NFeItem:
        """Transforma dados de um item em objeto NFeItem."""
        produto = item_data.get('produto', {})
        impostos = item_data.get('impostos', {})
        icms = impostos.get('icms', {})
        ipi = impostos.get('ipi', {})
        pis = impostos.get('pis', {})
        cofins = impostos.get('cofins', {})
        
        # Declaração de importação (pegar primeira se existir)
        di_list = produto.get('declaracoes_importacao', [])
        di = di_list[0] if di_list else {}
        
        item = NFeItem(
            # Identificação
            numero_item=self._to_int(item_data.get('numero_item')),
            codigo_produto=produto.get('codigo'),
            codigo_ean=produto.get('ean'),
            codigo_ean_tributavel=produto.get('ean_tributavel'),
            descricao=produto.get('descricao'),
            ncm=produto.get('ncm'),
            nve=produto.get('nve'),
            cest=produto.get('cest'),
            ex_tipi=produto.get('ex_tipi'),
            cfop=produto.get('cfop'),
            
            # Comercial
            unidade_comercial=produto.get('unidade_comercial'),
            quantidade_comercial=self._to_decimal(produto.get('quantidade_comercial')),
            valor_unitario_comercial=self._to_decimal(produto.get('valor_unitario_comercial')),
            valor_total_bruto=self._to_decimal(produto.get('valor_total')),
            
            # Tributável
            unidade_tributavel=produto.get('unidade_tributavel'),
            quantidade_tributavel=self._to_decimal(produto.get('quantidade_tributavel')),
            valor_unitario_tributavel=self._to_decimal(produto.get('valor_unitario_tributavel')),
            
            # Valores
            valor_frete=self._to_decimal(produto.get('valor_frete')),
            valor_seguro=self._to_decimal(produto.get('valor_seguro')),
            valor_desconto=self._to_decimal(produto.get('valor_desconto')),
            valor_outras_despesas=self._to_decimal(produto.get('valor_outras_despesas')),
            valor_total_item=self._to_decimal(produto.get('valor_total')),  # Valor total do produto
            indicador_total=produto.get('indicador_total'),
            
            # ICMS
            origem_mercadoria=icms.get('origem'),
            situacao_tributaria_icms=icms.get('situacao_tributaria'),
            modalidade_bc_icms=icms.get('modalidade_bc'),
            base_calculo_icms=self._to_decimal(icms.get('base_calculo')),
            aliquota_icms=self._to_decimal(icms.get('aliquota')),
            valor_icms=self._to_decimal(icms.get('valor')),
            percentual_reducao_bc_icms=self._to_decimal(icms.get('percentual_reducao_bc')),
            valor_icms_desonerado=self._to_decimal(icms.get('valor_desonerado')),
            motivo_desoneracao_icms=icms.get('motivo_desoneracao'),
            
            # ICMS ST
            modalidade_bc_icms_st=icms.get('modalidade_bc_st'),
            percentual_mva_st=self._to_decimal(icms.get('mva_st')),
            percentual_reducao_bc_icms_st=self._to_decimal(icms.get('reducao_bc_st')),
            base_calculo_icms_st=self._to_decimal(icms.get('base_calculo_st')),
            aliquota_icms_st=self._to_decimal(icms.get('aliquota_st')),
            valor_icms_st=self._to_decimal(icms.get('valor_st')),
            
            # FCP
            base_calculo_fcp=self._to_decimal(icms.get('base_calculo_fcp')),
            percentual_fcp=self._to_decimal(icms.get('percentual_fcp')),
            valor_fcp=self._to_decimal(icms.get('valor_fcp')),
            base_calculo_fcp_st=self._to_decimal(icms.get('base_calculo_fcp_st')),
            percentual_fcp_st=self._to_decimal(icms.get('percentual_fcp_st')),
            valor_fcp_st=self._to_decimal(icms.get('valor_fcp_st')),
            
            # IPI
            situacao_tributaria_ipi=ipi.get('situacao_tributaria'),
            classe_enquadramento_ipi=ipi.get('classe_enquadramento'),
            codigo_enquadramento_ipi=ipi.get('codigo_enquadramento'),
            cnpj_produtor=ipi.get('cnpj_produtor'),
            codigo_selo_ipi=ipi.get('codigo_selo'),
            quantidade_selo_ipi=self._to_int(ipi.get('quantidade_selo')),
            base_calculo_ipi=self._to_decimal(ipi.get('base_calculo')),
            aliquota_ipi=self._to_decimal(ipi.get('aliquota')),
            valor_ipi=self._to_decimal(ipi.get('valor')),
            
            # PIS
            situacao_tributaria_pis=pis.get('situacao_tributaria'),
            base_calculo_pis=self._to_decimal(pis.get('base_calculo')),
            aliquota_pis=self._to_decimal(pis.get('aliquota')),
            valor_pis=self._to_decimal(pis.get('valor')),
            quantidade_vendida_pis=self._to_decimal(pis.get('quantidade_vendida')),
            aliquota_pis_reais=self._to_decimal(pis.get('aliquota_reais')),
            
            # COFINS
            situacao_tributaria_cofins=cofins.get('situacao_tributaria'),
            base_calculo_cofins=self._to_decimal(cofins.get('base_calculo')),
            aliquota_cofins=self._to_decimal(cofins.get('aliquota')),
            valor_cofins=self._to_decimal(cofins.get('valor')),
            quantidade_vendida_cofins=self._to_decimal(cofins.get('quantidade_vendida')),
            aliquota_cofins_reais=self._to_decimal(cofins.get('aliquota_reais')),
            
            # Importação
            numero_di=di.get('numero'),
            data_di=self._to_date(di.get('data')),
            local_desembaraco=di.get('local_desembaraco'),
            uf_desembaraco=di.get('uf_desembaraco'),
            data_desembaraco=self._to_date(di.get('data_desembaraco')),
            via_transporte=di.get('via_transporte'),
            valor_afrmm=self._to_decimal(di.get('valor_afrmm')),
            forma_intermediacao=di.get('forma_intermediacao'),
            
            # Informações adicionais
            informacoes_adicionais=item_data.get('informacoes_adicionais'),
        )
        
        return item

    def _transformar_duplicata(self, dup_data: Dict[str, Any]) -> NFeDuplicata:
        """Transforma dados de uma duplicata em objeto NFeDuplicata."""
        return NFeDuplicata(
            numero_duplicata=dup_data.get('numero'),
            data_vencimento=self._to_date(dup_data.get('data_vencimento')),
            valor_duplicata=self._to_decimal(dup_data.get('valor')),
        )

    def _determinar_situacao(self, codigo_status: Optional[str]) -> Optional[str]:
        """Determina a situação da NF-e baseado no código de status."""
        if not codigo_status:
            return None
        
        codigo = codigo_status.strip()
        
        if codigo == '100':
            return 'Autorizada'
        elif codigo in ['101', '151', '155']:
            return 'Cancelada'
        elif codigo in ['110', '205', '301', '302', '303']:
            return 'Denegada'
        elif codigo in ['217', '218']:
            return 'Inutilizada'
        else:
            return 'Rejeitada'

    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """Converte valor para Decimal."""
        if value is None or value == '':
            return None
        try:
            return Decimal(str(value))
        except:
            return None

    def _to_int(self, value: Any) -> Optional[int]:
        """Converte valor para int."""
        if value is None or value == '':
            return None
        try:
            return int(float(str(value)))
        except:
            return None

    def _to_date(self, value: Any) -> Optional[date]:
        """Converte valor para date."""
        if value is None or value == '':
            return None
        
        if isinstance(value, datetime):
            return value.date()
        
        if isinstance(value, date):
            return value
        
        try:
            # Formato: 2024-01-01
            return datetime.strptime(str(value), '%Y-%m-%d').date()
        except:
            return None
