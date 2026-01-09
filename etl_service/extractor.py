"""
Extrator de dados XML - Módulo de Extração do ETL.

Este módulo é responsável por extrair todos os dados dos arquivos XML
de NF-e e NFC-e, sem fazer nenhuma transformação.
"""
from lxml import etree
from typing import Dict, Any, List, Optional
from datetime import datetime
import os


class XMLExtractor:
    """
    Extrator de dados de arquivos XML fiscais.
    
    Extrai todos os campos disponíveis nos XMLs de NF-e e NFC-e,
    mantendo a estrutura hierárquica dos dados.
    """

    # Namespaces comuns
    NAMESPACES = {
        'nfe': 'http://www.portalfiscal.inf.br/nfe',
    }

    def __init__(self):
        """Inicializa o extrator XML."""
        pass

    def extrair_nfe(self, caminho_arquivo: str) -> Dict[str, Any]:
        """
        Extrai todos os dados de um arquivo XML de NF-e ou NFC-e.
        
        Args:
            caminho_arquivo: Caminho para o arquivo XML
            
        Returns:
            Dicionário com todos os dados extraídos
            
        Raises:
            ValueError: Se o arquivo não for um XML válido de NF-e
        """
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(caminho_arquivo):
                raise ValueError(f"Arquivo não encontrado: {caminho_arquivo}")
            
            # Verificar se é um arquivo (não diretório)
            if os.path.isdir(caminho_arquivo):
                raise ValueError(f"O caminho informado é um DIRETÓRIO, não um arquivo: {caminho_arquivo}")
            
            # Verificar extensão
            if not caminho_arquivo.lower().endswith('.xml'):
                raise ValueError(f"O arquivo não tem extensão .xml: {caminho_arquivo}")
            
            tree = etree.parse(caminho_arquivo)
            root = tree.getroot()
            
            # Verificar se é NF-e
            nfe_proc = root.find('.//nfe:NFe', self.NAMESPACES)
            if nfe_proc is None:
                nfe_proc = root.find('.//nfe:nfeProc/nfe:NFe', self.NAMESPACES)
            if nfe_proc is None:
                raise ValueError("Arquivo não é uma NF-e válida")
            
            # Extrair dados
            dados = {
                'arquivo_original': caminho_arquivo,
                'tamanho_arquivo': os.path.getsize(caminho_arquivo) if os.path.exists(caminho_arquivo) else 0,
                'data_extracao': datetime.now(),
                'xml_completo': etree.tostring(root, encoding='unicode'),
            }
            
            # Extrair identificação
            dados['identificacao'] = self._extrair_identificacao(root)
            
            # Extrair emitente
            dados['emitente'] = self._extrair_emitente(root)
            
            # Extrair destinatário
            dados['destinatario'] = self._extrair_destinatario(root)
            
            # Extrair itens
            dados['itens'] = self._extrair_itens(root)
            
            # Extrair totais
            dados['totais'] = self._extrair_totais(root)
            
            # Extrair transporte
            dados['transporte'] = self._extrair_transporte(root)
            
            # Extrair cobrança
            dados['cobranca'] = self._extrair_cobranca(root)
            
            # Extrair pagamento
            dados['pagamento'] = self._extrair_pagamento(root)
            
            # Extrair informações adicionais
            dados['informacoes_adicionais'] = self._extrair_informacoes_adicionais(root)
            
            # Extrair protocolo de autorização
            dados['protocolo'] = self._extrair_protocolo(root)
            
            return dados
            
        except Exception as e:
            raise ValueError(f"Erro ao extrair dados do XML: {str(e)}")

    def _extrair_identificacao(self, root) -> Dict[str, Any]:
        """Extrai dados de identificação da NF-e."""
        ide = root.find('.//nfe:ide', self.NAMESPACES)
        if ide is None:
            return {}
        
        return {
            'chave_acesso': self._get_text(root, './/nfe:infNFe', 'Id', self.NAMESPACES, '').replace('NFe', ''),
            'codigo_uf': self._get_text(ide, 'nfe:cUF', namespaces=self.NAMESPACES),
            'codigo_nf': self._get_text(ide, 'nfe:cNF', namespaces=self.NAMESPACES),
            'natureza_operacao': self._get_text(ide, 'nfe:natOp', namespaces=self.NAMESPACES),
            'forma_pagamento': self._get_text(ide, 'nfe:indPag', namespaces=self.NAMESPACES),
            'modelo': self._get_text(ide, 'nfe:mod', namespaces=self.NAMESPACES),
            'serie': self._get_text(ide, 'nfe:serie', namespaces=self.NAMESPACES),
            'numero_nota': self._get_text(ide, 'nfe:nNF', namespaces=self.NAMESPACES),
            'data_emissao': self._parse_datetime(self._get_text(ide, 'nfe:dhEmi', namespaces=self.NAMESPACES)),
            'data_saida_entrada': self._parse_datetime(self._get_text(ide, 'nfe:dhSaiEnt', namespaces=self.NAMESPACES)),
            'tipo_operacao': self._get_text(ide, 'nfe:tpNF', namespaces=self.NAMESPACES),
            'codigo_municipio': self._get_text(ide, 'nfe:cMunFG', namespaces=self.NAMESPACES),
            'tipo_impressao': self._get_text(ide, 'nfe:tpImp', namespaces=self.NAMESPACES),
            'tipo_emissao': self._get_text(ide, 'nfe:tpEmis', namespaces=self.NAMESPACES),
            'digito_verificador': self._get_text(ide, 'nfe:cDV', namespaces=self.NAMESPACES),
            'ambiente': self._get_text(ide, 'nfe:tpAmb', namespaces=self.NAMESPACES),
            'finalidade_emissao': self._get_text(ide, 'nfe:finNFe', namespaces=self.NAMESPACES),
            'consumidor_final': self._get_text(ide, 'nfe:indFinal', namespaces=self.NAMESPACES),
            'presenca_comprador': self._get_text(ide, 'nfe:indPres', namespaces=self.NAMESPACES),
            'processo_emissao': self._get_text(ide, 'nfe:procEmi', namespaces=self.NAMESPACES),
            'versao_processo': self._get_text(ide, 'nfe:verProc', namespaces=self.NAMESPACES),
        }

    def _extrair_emitente(self, root) -> Dict[str, Any]:
        """Extrai dados do emitente."""
        emit = root.find('.//nfe:emit', self.NAMESPACES)
        if emit is None:
            return {}
        
        endereco = emit.find('nfe:enderEmit', self.NAMESPACES)
        
        return {
            'cnpj': self._get_text(emit, 'nfe:CNPJ', namespaces=self.NAMESPACES),
            'cpf': self._get_text(emit, 'nfe:CPF', namespaces=self.NAMESPACES),
            'razao_social': self._get_text(emit, 'nfe:xNome', namespaces=self.NAMESPACES),
            'nome_fantasia': self._get_text(emit, 'nfe:xFant', namespaces=self.NAMESPACES),
            'inscricao_estadual': self._get_text(emit, 'nfe:IE', namespaces=self.NAMESPACES),
            'inscricao_estadual_st': self._get_text(emit, 'nfe:IEST', namespaces=self.NAMESPACES),
            'inscricao_municipal': self._get_text(emit, 'nfe:IM', namespaces=self.NAMESPACES),
            'cnae': self._get_text(emit, 'nfe:CNAE', namespaces=self.NAMESPACES),
            'regime_tributario': self._get_text(emit, 'nfe:CRT', namespaces=self.NAMESPACES),
            'endereco': {
                'logradouro': self._get_text(endereco, 'nfe:xLgr', namespaces=self.NAMESPACES) if endereco is not None else None,
                'numero': self._get_text(endereco, 'nfe:nro', namespaces=self.NAMESPACES) if endereco is not None else None,
                'complemento': self._get_text(endereco, 'nfe:xCpl', namespaces=self.NAMESPACES) if endereco is not None else None,
                'bairro': self._get_text(endereco, 'nfe:xBairro', namespaces=self.NAMESPACES) if endereco is not None else None,
                'codigo_municipio': self._get_text(endereco, 'nfe:cMun', namespaces=self.NAMESPACES) if endereco is not None else None,
                'municipio': self._get_text(endereco, 'nfe:xMun', namespaces=self.NAMESPACES) if endereco is not None else None,
                'uf': self._get_text(endereco, 'nfe:UF', namespaces=self.NAMESPACES) if endereco is not None else None,
                'cep': self._get_text(endereco, 'nfe:CEP', namespaces=self.NAMESPACES) if endereco is not None else None,
                'codigo_pais': self._get_text(endereco, 'nfe:cPais', namespaces=self.NAMESPACES) if endereco is not None else None,
                'pais': self._get_text(endereco, 'nfe:xPais', namespaces=self.NAMESPACES) if endereco is not None else None,
                'telefone': self._get_text(endereco, 'nfe:fone', namespaces=self.NAMESPACES) if endereco is not None else None,
            }
        }

    def _extrair_destinatario(self, root) -> Dict[str, Any]:
        """Extrai dados do destinatário."""
        dest = root.find('.//nfe:dest', self.NAMESPACES)
        if dest is None:
            return {}
        
        endereco = dest.find('nfe:enderDest', self.NAMESPACES)
        
        return {
            'cnpj': self._get_text(dest, 'nfe:CNPJ', namespaces=self.NAMESPACES),
            'cpf': self._get_text(dest, 'nfe:CPF', namespaces=self.NAMESPACES),
            'id_estrangeiro': self._get_text(dest, 'nfe:idEstrangeiro', namespaces=self.NAMESPACES),
            'razao_social': self._get_text(dest, 'nfe:xNome', namespaces=self.NAMESPACES),
            'inscricao_estadual': self._get_text(dest, 'nfe:IE', namespaces=self.NAMESPACES),
            'inscricao_suframa': self._get_text(dest, 'nfe:ISUF', namespaces=self.NAMESPACES),
            'inscricao_municipal': self._get_text(dest, 'nfe:IM', namespaces=self.NAMESPACES),
            'email': self._get_text(dest, 'nfe:email', namespaces=self.NAMESPACES),
            'indicador_ie': self._get_text(dest, 'nfe:indIEDest', namespaces=self.NAMESPACES),
            'endereco': {
                'logradouro': self._get_text(endereco, 'nfe:xLgr', namespaces=self.NAMESPACES) if endereco is not None else None,
                'numero': self._get_text(endereco, 'nfe:nro', namespaces=self.NAMESPACES) if endereco is not None else None,
                'complemento': self._get_text(endereco, 'nfe:xCpl', namespaces=self.NAMESPACES) if endereco is not None else None,
                'bairro': self._get_text(endereco, 'nfe:xBairro', namespaces=self.NAMESPACES) if endereco is not None else None,
                'codigo_municipio': self._get_text(endereco, 'nfe:cMun', namespaces=self.NAMESPACES) if endereco is not None else None,
                'municipio': self._get_text(endereco, 'nfe:xMun', namespaces=self.NAMESPACES) if endereco is not None else None,
                'uf': self._get_text(endereco, 'nfe:UF', namespaces=self.NAMESPACES) if endereco is not None else None,
                'cep': self._get_text(endereco, 'nfe:CEP', namespaces=self.NAMESPACES) if endereco is not None else None,
                'codigo_pais': self._get_text(endereco, 'nfe:cPais', namespaces=self.NAMESPACES) if endereco is not None else None,
                'pais': self._get_text(endereco, 'nfe:xPais', namespaces=self.NAMESPACES) if endereco is not None else None,
                'telefone': self._get_text(endereco, 'nfe:fone', namespaces=self.NAMESPACES) if endereco is not None else None,
            }
        }

    def _extrair_itens(self, root) -> List[Dict[str, Any]]:
        """Extrai todos os itens da NF-e."""
        itens = []
        det_list = root.findall('.//nfe:det', self.NAMESPACES)
        
        for det in det_list:
            item = {
                'numero_item': self._get_text(det, '.', 'nItem', self.NAMESPACES),
            }
            
            # Produto
            prod = det.find('nfe:prod', self.NAMESPACES)
            if prod is not None:
                item['produto'] = {
                    'codigo': self._get_text(prod, 'nfe:cProd', namespaces=self.NAMESPACES),
                    'ean': self._get_text(prod, 'nfe:cEAN', namespaces=self.NAMESPACES),
                    'descricao': self._get_text(prod, 'nfe:xProd', namespaces=self.NAMESPACES),
                    'ncm': self._get_text(prod, 'nfe:NCM', namespaces=self.NAMESPACES),
                    'nve': self._get_text(prod, 'nfe:NVE', namespaces=self.NAMESPACES),
                    'cest': self._get_text(prod, 'nfe:CEST', namespaces=self.NAMESPACES),
                    'ex_tipi': self._get_text(prod, 'nfe:EXTIPI', namespaces=self.NAMESPACES),
                    'cfop': self._get_text(prod, 'nfe:CFOP', namespaces=self.NAMESPACES),
                    'unidade_comercial': self._get_text(prod, 'nfe:uCom', namespaces=self.NAMESPACES),
                    'quantidade_comercial': self._get_text(prod, 'nfe:qCom', namespaces=self.NAMESPACES),
                    'valor_unitario_comercial': self._get_text(prod, 'nfe:vUnCom', namespaces=self.NAMESPACES),
                    'valor_total': self._get_text(prod, 'nfe:vProd', namespaces=self.NAMESPACES),
                    'ean_tributavel': self._get_text(prod, 'nfe:cEANTrib', namespaces=self.NAMESPACES),
                    'unidade_tributavel': self._get_text(prod, 'nfe:uTrib', namespaces=self.NAMESPACES),
                    'quantidade_tributavel': self._get_text(prod, 'nfe:qTrib', namespaces=self.NAMESPACES),
                    'valor_unitario_tributavel': self._get_text(prod, 'nfe:vUnTrib', namespaces=self.NAMESPACES),
                    'valor_frete': self._get_text(prod, 'nfe:vFrete', namespaces=self.NAMESPACES),
                    'valor_seguro': self._get_text(prod, 'nfe:vSeg', namespaces=self.NAMESPACES),
                    'valor_desconto': self._get_text(prod, 'nfe:vDesc', namespaces=self.NAMESPACES),
                    'valor_outras_despesas': self._get_text(prod, 'nfe:vOutro', namespaces=self.NAMESPACES),
                    'indicador_total': self._get_text(prod, 'nfe:indTot', namespaces=self.NAMESPACES),
                    'numero_pedido': self._get_text(prod, 'nfe:xPed', namespaces=self.NAMESPACES),
                    'item_pedido': self._get_text(prod, 'nfe:nItemPed', namespaces=self.NAMESPACES),
                    'numero_fci': self._get_text(prod, 'nfe:nFCI', namespaces=self.NAMESPACES),
                }
                
                # DI - Declaração de Importação
                di_list = prod.findall('nfe:DI', self.NAMESPACES)
                if di_list:
                    item['produto']['declaracoes_importacao'] = []
                    for di in di_list:
                        item['produto']['declaracoes_importacao'].append({
                            'numero': self._get_text(di, 'nfe:nDI', namespaces=self.NAMESPACES),
                            'data': self._get_text(di, 'nfe:dDI', namespaces=self.NAMESPACES),
                            'local_desembaraco': self._get_text(di, 'nfe:xLocDesemb', namespaces=self.NAMESPACES),
                            'uf_desembaraco': self._get_text(di, 'nfe:UFDesemb', namespaces=self.NAMESPACES),
                            'data_desembaraco': self._get_text(di, 'nfe:dDesemb', namespaces=self.NAMESPACES),
                            'via_transporte': self._get_text(di, 'nfe:tpViaTransp', namespaces=self.NAMESPACES),
                            'valor_afrmm': self._get_text(di, 'nfe:vAFRMM', namespaces=self.NAMESPACES),
                            'forma_intermediacao': self._get_text(di, 'nfe:tpIntermedio', namespaces=self.NAMESPACES),
                            'cnpj_adquirente': self._get_text(di, 'nfe:CNPJAdquirente', namespaces=self.NAMESPACES),
                            'uf_adquirente': self._get_text(di, 'nfe:UFTerceiro', namespaces=self.NAMESPACES),
                            'codigo_exportador': self._get_text(di, 'nfe:cExportador', namespaces=self.NAMESPACES),
                        })
            
            # Impostos
            imposto = det.find('nfe:imposto', self.NAMESPACES)
            if imposto is not None:
                item['impostos'] = self._extrair_impostos_item(imposto)
            
            # Informações adicionais do item
            item['informacoes_adicionais'] = self._get_text(det, 'nfe:infAdProd', namespaces=self.NAMESPACES)
            
            itens.append(item)
        
        return itens

    def _extrair_impostos_item(self, imposto) -> Dict[str, Any]:
        """Extrai informações de impostos de um item."""
        impostos_data = {
            'valor_aproximado_tributos': self._get_text(imposto, 'nfe:vTotTrib', namespaces=self.NAMESPACES),
        }
        
        # ICMS
        icms = imposto.find('nfe:ICMS', self.NAMESPACES)
        if icms is not None:
            # Pode ser vários tipos: ICMS00, ICMS10, ICMS20, etc ou ICMSSN101, etc
            icms_tipo = None
            for child in icms:
                if child.tag.endswith('}ICMS00') or child.tag.endswith('}ICMS10') or \
                   child.tag.endswith('}ICMS20') or child.tag.endswith('}ICMS30') or \
                   child.tag.endswith('}ICMS40') or child.tag.endswith('}ICMS51') or \
                   child.tag.endswith('}ICMS60') or child.tag.endswith('}ICMS70') or \
                   child.tag.endswith('}ICMS90') or 'ICMSSN' in child.tag:
                    icms_tipo = child
                    break
            
            if icms_tipo is not None:
                impostos_data['icms'] = {
                    'origem': self._get_text(icms_tipo, 'nfe:orig', namespaces=self.NAMESPACES),
                    'situacao_tributaria': self._get_text(icms_tipo, 'nfe:CST', namespaces=self.NAMESPACES) or \
                                         self._get_text(icms_tipo, 'nfe:CSOSN', namespaces=self.NAMESPACES),
                    'modalidade_bc': self._get_text(icms_tipo, 'nfe:modBC', namespaces=self.NAMESPACES),
                    'base_calculo': self._get_text(icms_tipo, 'nfe:vBC', namespaces=self.NAMESPACES),
                    'aliquota': self._get_text(icms_tipo, 'nfe:pICMS', namespaces=self.NAMESPACES),
                    'valor': self._get_text(icms_tipo, 'nfe:vICMS', namespaces=self.NAMESPACES),
                    'percentual_reducao_bc': self._get_text(icms_tipo, 'nfe:pRedBC', namespaces=self.NAMESPACES),
                    'valor_desonerado': self._get_text(icms_tipo, 'nfe:vICMSDeson', namespaces=self.NAMESPACES),
                    'motivo_desoneracao': self._get_text(icms_tipo, 'nfe:motDesICMS', namespaces=self.NAMESPACES),
                    # ST
                    'modalidade_bc_st': self._get_text(icms_tipo, 'nfe:modBCST', namespaces=self.NAMESPACES),
                    'mva_st': self._get_text(icms_tipo, 'nfe:pMVAST', namespaces=self.NAMESPACES),
                    'reducao_bc_st': self._get_text(icms_tipo, 'nfe:pRedBCST', namespaces=self.NAMESPACES),
                    'base_calculo_st': self._get_text(icms_tipo, 'nfe:vBCST', namespaces=self.NAMESPACES),
                    'aliquota_st': self._get_text(icms_tipo, 'nfe:pICMSST', namespaces=self.NAMESPACES),
                    'valor_st': self._get_text(icms_tipo, 'nfe:vICMSST', namespaces=self.NAMESPACES),
                    # FCP
                    'base_calculo_fcp': self._get_text(icms_tipo, 'nfe:vBCFCP', namespaces=self.NAMESPACES),
                    'percentual_fcp': self._get_text(icms_tipo, 'nfe:pFCP', namespaces=self.NAMESPACES),
                    'valor_fcp': self._get_text(icms_tipo, 'nfe:vFCP', namespaces=self.NAMESPACES),
                    'base_calculo_fcp_st': self._get_text(icms_tipo, 'nfe:vBCFCPST', namespaces=self.NAMESPACES),
                    'percentual_fcp_st': self._get_text(icms_tipo, 'nfe:pFCPST', namespaces=self.NAMESPACES),
                    'valor_fcp_st': self._get_text(icms_tipo, 'nfe:vFCPST', namespaces=self.NAMESPACES),
                    # Crédito SN
                    'percentual_credito_sn': self._get_text(icms_tipo, 'nfe:pCredSN', namespaces=self.NAMESPACES),
                    'valor_credito_sn': self._get_text(icms_tipo, 'nfe:vCredICMSSN', namespaces=self.NAMESPACES),
                }
        
        # IPI
        ipi = imposto.find('nfe:IPI', self.NAMESPACES)
        if ipi is not None:
            ipi_trib = ipi.find('nfe:IPITrib', self.NAMESPACES)
            ipi_nt = ipi.find('nfe:IPINT', self.NAMESPACES)
            ipi_data = ipi_trib if ipi_trib is not None else ipi_nt
            
            if ipi_data is not None:
                impostos_data['ipi'] = {
                    'classe_enquadramento': self._get_text(ipi, 'nfe:clEnq', namespaces=self.NAMESPACES),
                    'cnpj_produtor': self._get_text(ipi, 'nfe:CNPJProd', namespaces=self.NAMESPACES),
                    'codigo_selo': self._get_text(ipi, 'nfe:cSelo', namespaces=self.NAMESPACES),
                    'quantidade_selo': self._get_text(ipi, 'nfe:qSelo', namespaces=self.NAMESPACES),
                    'codigo_enquadramento': self._get_text(ipi, 'nfe:cEnq', namespaces=self.NAMESPACES),
                    'situacao_tributaria': self._get_text(ipi_data, 'nfe:CST', namespaces=self.NAMESPACES),
                    'base_calculo': self._get_text(ipi_data, 'nfe:vBC', namespaces=self.NAMESPACES),
                    'aliquota': self._get_text(ipi_data, 'nfe:pIPI', namespaces=self.NAMESPACES),
                    'valor': self._get_text(ipi_data, 'nfe:vIPI', namespaces=self.NAMESPACES),
                }
        
        # PIS
        pis = imposto.find('nfe:PIS', self.NAMESPACES)
        if pis is not None:
            pis_tipo = None
            for child in pis:
                if 'PISAliq' in child.tag or 'PISQtde' in child.tag or 'PISNT' in child.tag or \
                   'PISOutr' in child.tag:
                    pis_tipo = child
                    break
            
            if pis_tipo is not None:
                impostos_data['pis'] = {
                    'situacao_tributaria': self._get_text(pis_tipo, 'nfe:CST', namespaces=self.NAMESPACES),
                    'base_calculo': self._get_text(pis_tipo, 'nfe:vBC', namespaces=self.NAMESPACES),
                    'aliquota': self._get_text(pis_tipo, 'nfe:pPIS', namespaces=self.NAMESPACES),
                    'valor': self._get_text(pis_tipo, 'nfe:vPIS', namespaces=self.NAMESPACES),
                    'quantidade_vendida': self._get_text(pis_tipo, 'nfe:qBCProd', namespaces=self.NAMESPACES),
                    'aliquota_reais': self._get_text(pis_tipo, 'nfe:vAliqProd', namespaces=self.NAMESPACES),
                }
        
        # COFINS
        cofins = imposto.find('nfe:COFINS', self.NAMESPACES)
        if cofins is not None:
            cofins_tipo = None
            for child in cofins:
                if 'COFINSAliq' in child.tag or 'COFINSQtde' in child.tag or 'COFINSNT' in child.tag or \
                   'COFINSOutr' in child.tag:
                    cofins_tipo = child
                    break
            
            if cofins_tipo is not None:
                impostos_data['cofins'] = {
                    'situacao_tributaria': self._get_text(cofins_tipo, 'nfe:CST', namespaces=self.NAMESPACES),
                    'base_calculo': self._get_text(cofins_tipo, 'nfe:vBC', namespaces=self.NAMESPACES),
                    'aliquota': self._get_text(cofins_tipo, 'nfe:pCOFINS', namespaces=self.NAMESPACES),
                    'valor': self._get_text(cofins_tipo, 'nfe:vCOFINS', namespaces=self.NAMESPACES),
                    'quantidade_vendida': self._get_text(cofins_tipo, 'nfe:qBCProd', namespaces=self.NAMESPACES),
                    'aliquota_reais': self._get_text(cofins_tipo, 'nfe:vAliqProd', namespaces=self.NAMESPACES),
                }
        
        return impostos_data

    def _extrair_totais(self, root) -> Dict[str, Any]:
        """Extrai totalizadores da NF-e."""
        total = root.find('.//nfe:total/nfe:ICMSTot', self.NAMESPACES)
        if total is None:
            return {}
        
        return {
            'base_calculo_icms': self._get_text(total, 'nfe:vBC', namespaces=self.NAMESPACES),
            'valor_icms': self._get_text(total, 'nfe:vICMS', namespaces=self.NAMESPACES),
            'valor_icms_desonerado': self._get_text(total, 'nfe:vICMSDeson', namespaces=self.NAMESPACES),
            'base_calculo_icms_st': self._get_text(total, 'nfe:vBCST', namespaces=self.NAMESPACES),
            'valor_icms_st': self._get_text(total, 'nfe:vST', namespaces=self.NAMESPACES),
            'valor_produtos': self._get_text(total, 'nfe:vProd', namespaces=self.NAMESPACES),
            'valor_frete': self._get_text(total, 'nfe:vFrete', namespaces=self.NAMESPACES),
            'valor_seguro': self._get_text(total, 'nfe:vSeg', namespaces=self.NAMESPACES),
            'valor_desconto': self._get_text(total, 'nfe:vDesc', namespaces=self.NAMESPACES),
            'valor_ipi': self._get_text(total, 'nfe:vIPI', namespaces=self.NAMESPACES),
            'valor_pis': self._get_text(total, 'nfe:vPIS', namespaces=self.NAMESPACES),
            'valor_cofins': self._get_text(total, 'nfe:vCOFINS', namespaces=self.NAMESPACES),
            'valor_outras_despesas': self._get_text(total, 'nfe:vOutro', namespaces=self.NAMESPACES),
            'valor_total_nota': self._get_text(total, 'nfe:vNF', namespaces=self.NAMESPACES),
            'valor_aproximado_tributos': self._get_text(total, 'nfe:vTotTrib', namespaces=self.NAMESPACES),
            'valor_fcp': self._get_text(total, 'nfe:vFCP', namespaces=self.NAMESPACES),
            'valor_fcp_st': self._get_text(total, 'nfe:vFCPST', namespaces=self.NAMESPACES),
            'valor_fcp_st_retido': self._get_text(total, 'nfe:vFCPSTRet', namespaces=self.NAMESPACES),
        }

    def _extrair_transporte(self, root) -> Dict[str, Any]:
        """Extrai dados de transporte."""
        transp = root.find('.//nfe:transp', self.NAMESPACES)
        if transp is None:
            return {}
        
        transportadora = transp.find('nfe:transporta', self.NAMESPACES)
        veiculo = transp.find('nfe:veicTransp', self.NAMESPACES)
        volumes = transp.findall('nfe:vol', self.NAMESPACES)
        
        data = {
            'modalidade_frete': self._get_text(transp, 'nfe:modFrete', namespaces=self.NAMESPACES),
        }
        
        if transportadora is not None:
            data['transportadora'] = {
                'cnpj': self._get_text(transportadora, 'nfe:CNPJ', namespaces=self.NAMESPACES),
                'cpf': self._get_text(transportadora, 'nfe:CPF', namespaces=self.NAMESPACES),
                'razao_social': self._get_text(transportadora, 'nfe:xNome', namespaces=self.NAMESPACES),
                'inscricao_estadual': self._get_text(transportadora, 'nfe:IE', namespaces=self.NAMESPACES),
                'endereco': self._get_text(transportadora, 'nfe:xEnder', namespaces=self.NAMESPACES),
                'municipio': self._get_text(transportadora, 'nfe:xMun', namespaces=self.NAMESPACES),
                'uf': self._get_text(transportadora, 'nfe:UF', namespaces=self.NAMESPACES),
            }
        
        if veiculo is not None:
            data['veiculo'] = {
                'placa': self._get_text(veiculo, 'nfe:placa', namespaces=self.NAMESPACES),
                'uf': self._get_text(veiculo, 'nfe:UF', namespaces=self.NAMESPACES),
                'rntc': self._get_text(veiculo, 'nfe:RNTC', namespaces=self.NAMESPACES),
            }
        
        if volumes:
            data['volumes'] = []
            for vol in volumes:
                data['volumes'].append({
                    'quantidade': self._get_text(vol, 'nfe:qVol', namespaces=self.NAMESPACES),
                    'especie': self._get_text(vol, 'nfe:esp', namespaces=self.NAMESPACES),
                    'marca': self._get_text(vol, 'nfe:marca', namespaces=self.NAMESPACES),
                    'numeracao': self._get_text(vol, 'nfe:nVol', namespaces=self.NAMESPACES),
                    'peso_liquido': self._get_text(vol, 'nfe:pesoL', namespaces=self.NAMESPACES),
                    'peso_bruto': self._get_text(vol, 'nfe:pesoB', namespaces=self.NAMESPACES),
                })
        
        return data

    def _extrair_cobranca(self, root) -> Dict[str, Any]:
        """Extrai dados de cobrança."""
        cobr = root.find('.//nfe:cobr', self.NAMESPACES)
        if cobr is None:
            return {}
        
        fat = cobr.find('nfe:fat', self.NAMESPACES)
        duplicatas = cobr.findall('nfe:dup', self.NAMESPACES)
        
        data = {}
        
        if fat is not None:
            data['fatura'] = {
                'numero': self._get_text(fat, 'nfe:nFat', namespaces=self.NAMESPACES),
                'valor_original': self._get_text(fat, 'nfe:vOrig', namespaces=self.NAMESPACES),
                'valor_desconto': self._get_text(fat, 'nfe:vDesc', namespaces=self.NAMESPACES),
                'valor_liquido': self._get_text(fat, 'nfe:vLiq', namespaces=self.NAMESPACES),
            }
        
        if duplicatas:
            data['duplicatas'] = []
            for dup in duplicatas:
                data['duplicatas'].append({
                    'numero': self._get_text(dup, 'nfe:nDup', namespaces=self.NAMESPACES),
                    'data_vencimento': self._get_text(dup, 'nfe:dVenc', namespaces=self.NAMESPACES),
                    'valor': self._get_text(dup, 'nfe:vDup', namespaces=self.NAMESPACES),
                })
        
        return data

    def _extrair_pagamento(self, root) -> Dict[str, Any]:
        """Extrai dados de pagamento."""
        pagamentos = root.findall('.//nfe:pag/nfe:detPag', self.NAMESPACES)
        if not pagamentos:
            # Formato antigo
            pag = root.find('.//nfe:pag', self.NAMESPACES)
            if pag is not None:
                return {
                    'forma': self._get_text(pag, 'nfe:tPag', namespaces=self.NAMESPACES),
                    'valor': self._get_text(pag, 'nfe:vPag', namespaces=self.NAMESPACES),
                }
            return {}
        
        data = {'detalhes': []}
        for pag in pagamentos:
            data['detalhes'].append({
                'forma': self._get_text(pag, 'nfe:tPag', namespaces=self.NAMESPACES),
                'valor': self._get_text(pag, 'nfe:vPag', namespaces=self.NAMESPACES),
                'cnpj_credenciadora': self._get_text(pag, 'nfe:card/nfe:CNPJ', namespaces=self.NAMESPACES),
                'bandeira': self._get_text(pag, 'nfe:card/nfe:tBand', namespaces=self.NAMESPACES),
                'autorizacao': self._get_text(pag, 'nfe:card/nfe:cAut', namespaces=self.NAMESPACES),
            })
        
        # Troco
        troco = root.find('.//nfe:pag/nfe:vTroco', self.NAMESPACES)
        if troco is not None:
            data['troco'] = troco.text
        
        return data

    def _extrair_informacoes_adicionais(self, root) -> Dict[str, Any]:
        """Extrai informações adicionais."""
        inf_adic = root.find('.//nfe:infAdic', self.NAMESPACES)
        if inf_adic is None:
            return {}
        
        return {
            'informacoes_fisco': self._get_text(inf_adic, 'nfe:infAdFisco', namespaces=self.NAMESPACES),
            'informacoes_complementares': self._get_text(inf_adic, 'nfe:infCpl', namespaces=self.NAMESPACES),
        }

    def _extrair_protocolo(self, root) -> Dict[str, Any]:
        """Extrai dados do protocolo de autorização."""
        prot = root.find('.//nfe:protNFe/nfe:infProt', self.NAMESPACES)
        if prot is None:
            return {}
        
        return {
            'ambiente': self._get_text(prot, 'nfe:tpAmb', namespaces=self.NAMESPACES),
            'versao_aplicativo': self._get_text(prot, 'nfe:verAplic', namespaces=self.NAMESPACES),
            'chave_acesso': self._get_text(prot, 'nfe:chNFe', namespaces=self.NAMESPACES),
            'data_recebimento': self._parse_datetime(self._get_text(prot, 'nfe:dhRecbto', namespaces=self.NAMESPACES)),
            'numero_protocolo': self._get_text(prot, 'nfe:nProt', namespaces=self.NAMESPACES),
            'digest_value': self._get_text(prot, 'nfe:digVal', namespaces=self.NAMESPACES),
            'codigo_status': self._get_text(prot, 'nfe:cStat', namespaces=self.NAMESPACES),
            'motivo': self._get_text(prot, 'nfe:xMotivo', namespaces=self.NAMESPACES),
        }

    def _get_text(self, element, path: str, attr: Optional[str] = None, 
                  namespaces: Optional[Dict] = None, default: str = '') -> Optional[str]:
        """
        Obtém o texto de um elemento XML.
        
        Args:
            element: Elemento XML
            path: XPath para o elemento
            attr: Atributo a ser obtido (opcional)
            namespaces: Namespaces XML
            default: Valor padrão se não encontrado
            
        Returns:
            Texto do elemento ou None
        """
        if element is None:
            return default or None
        
        if path == '.':
            elem = element
        else:
            elem = element.find(path, namespaces) if namespaces else element.find(path)
        
        if elem is None:
            return default or None
        
        if attr:
            return elem.get(attr, default) or None
        
        return elem.text if elem.text else (default or None)

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Converte string de data/hora para datetime.
        
        Args:
            date_str: String da data/hora
            
        Returns:
            Objeto datetime ou None
        """
        if not date_str:
            return None
        
        try:
            import re
            # Formato: 2024-01-01T10:00:00-03:00 ou 2024-01-01T10:00:00+00:00
            if 'T' in date_str:
                # Remove timezone (parte após +/- no final)
                date_str_clean = re.sub(r'[+-]\d{2}:\d{2}$', '', date_str)
                # Converte T para espaço
                date_str_clean = date_str_clean.replace('T', ' ')
                return datetime.strptime(date_str_clean, '%Y-%m-%d %H:%M:%S')
            
            # Formato: 2024-01-01
            return datetime.strptime(date_str, '%Y-%m-%d')
        except Exception:
            return None
