"""
Módulo para leitura e classificação de arquivos XML de documentos fiscais.
"""
from datetime import datetime
from decimal import Decimal
from lxml import etree
from typing import Optional
from .models import DocumentoFiscal, Item, Tributo, TipoDocumento, TipoMovimento, TipoTributo


class XMLReader:
    """Leitor de arquivos XML de documentos fiscais eletrônicos."""

    # Namespaces comuns em documentos fiscais
    NAMESPACES = {
        'nfe': 'http://www.portalfiscal.inf.br/nfe',
        'cte': 'http://www.portalfiscal.inf.br/cte',
    }

    def __init__(self, cnpj_empresa: str):
        """
        Inicializa o leitor XML.
        
        Args:
            cnpj_empresa: CNPJ da empresa auditada (para classificação entrada/saída)
        """
        self.cnpj_empresa = cnpj_empresa.replace(".", "").replace("/", "").replace("-", "")

    def ler_xml(self, caminho_arquivo: str) -> DocumentoFiscal:
        """
        Lê um arquivo XML e retorna um DocumentoFiscal.
        
        Args:
            caminho_arquivo: Caminho para o arquivo XML
            
        Returns:
            DocumentoFiscal com os dados extraídos
        """
        tree = etree.parse(caminho_arquivo)
        root = tree.getroot()

        # Identifica o tipo de documento
        tipo_doc = self._identificar_tipo_documento(root)
        
        if tipo_doc == TipoDocumento.NFE or tipo_doc == TipoDocumento.NFCE:
            return self._ler_nfe(root)
        elif tipo_doc == TipoDocumento.CTE:
            return self._ler_cte(root)
        else:
            raise ValueError(f"Tipo de documento não suportado: {tipo_doc}")

    def _identificar_tipo_documento(self, root) -> TipoDocumento:
        """Identifica o tipo de documento fiscal pelo XML."""
        # Verifica pelos namespaces ou tags raiz
        if root.tag.endswith('nfeProc') or root.tag.endswith('NFe'):
            # Pode ser NFe ou NFCe - verificar depois pelo modelo
            return TipoDocumento.NFE
        elif root.tag.endswith('cteProc') or root.tag.endswith('CTe'):
            return TipoDocumento.CTE
        else:
            # Tenta detectar pelo namespace
            ns_str = str(root.nsmap.get(None, ''))
            if 'nfe' in ns_str:
                return TipoDocumento.NFE
            elif 'cte' in ns_str:
                return TipoDocumento.CTE
        
        raise ValueError("Tipo de documento não identificado")

    def _ler_nfe(self, root) -> DocumentoFiscal:
        """Lê dados de uma NF-e ou NFC-e."""
        # Busca o nó infNFe
        nfe = root.find('.//nfe:infNFe', self.NAMESPACES)
        if nfe is None:
            # Tenta sem namespace
            nfe = root.find('.//infNFe')
        
        if nfe is None:
            raise ValueError("Estrutura de NF-e inválida")

        # Dados da identificação
        ide = nfe.find('.//nfe:ide', self.NAMESPACES)
        if ide is None:
            ide = nfe.find('.//ide')
        chave = nfe.get('Id', '').replace('NFe', '')
        numero = ide.findtext('.//nfe:nNF', namespaces=self.NAMESPACES) or ide.findtext('.//nNF') or ""
        serie = ide.findtext('.//nfe:serie', namespaces=self.NAMESPACES) or ide.findtext('.//serie') or ""
        data_emissao_str = ide.findtext('.//nfe:dhEmi', namespaces=self.NAMESPACES) or ide.findtext('.//dhEmi') or ""
        tp_nf = ide.findtext('.//nfe:tpNF', namespaces=self.NAMESPACES) or ide.findtext('.//tpNF') or ""
        mod = ide.findtext('.//nfe:mod', namespaces=self.NAMESPACES) or ide.findtext('.//mod') or ""

        # Determina se é NFe ou NFCe pelo modelo
        tipo_doc = TipoDocumento.NFCE if mod == "65" else TipoDocumento.NFE

        # Parse da data
        data_emissao = datetime.fromisoformat(data_emissao_str.replace('Z', '+00:00')) if data_emissao_str else datetime.now()

        # Dados do emitente
        emit = nfe.find('.//nfe:emit', self.NAMESPACES)
        if emit is None:
            emit = nfe.find('.//emit')
        cnpj_emit = emit.findtext('.//nfe:CNPJ', namespaces=self.NAMESPACES) or emit.findtext('.//CNPJ') or ""

        # Dados do destinatário
        dest = nfe.find('.//nfe:dest', self.NAMESPACES)
        if dest is None:
            dest = nfe.find('.//dest')
        cnpj_dest = ""
        if dest is not None:
            cnpj_dest = dest.findtext('.//nfe:CNPJ', namespaces=self.NAMESPACES) or dest.findtext('.//CNPJ') or ""

        # Total da nota
        total = nfe.find('.//nfe:total', self.NAMESPACES)
        if total is None:
            total = nfe.find('.//total')
        icms_tot = total.find('.//nfe:ICMSTot', self.NAMESPACES)
        if icms_tot is None:
            icms_tot = total.find('.//ICMSTot')
        valor_total = Decimal(icms_tot.findtext('.//nfe:vNF', namespaces=self.NAMESPACES) or icms_tot.findtext('.//vNF') or "0")

        # Pega CFOP do primeiro item para ajudar na classificação
        cfop_doc = ""
        det_list = nfe.findall('.//nfe:det', self.NAMESPACES) or nfe.findall('.//det')
        if det_list:
            primeiro_det = det_list[0]
            prod_primeiro = primeiro_det.find('.//nfe:prod', self.NAMESPACES)
            if prod_primeiro is None:
                prod_primeiro = primeiro_det.find('.//prod')
            if prod_primeiro is not None:
                cfop_doc = prod_primeiro.findtext('.//nfe:CFOP', namespaces=self.NAMESPACES) or prod_primeiro.findtext('.//CFOP') or ""

        # Classifica como entrada ou saída
        tipo_movimento = self._classificar_movimento(cnpj_emit, cnpj_dest, tp_nf, cfop_doc)

        # Cria documento
        doc = DocumentoFiscal(
            tipo=tipo_doc,
            chave=chave,
            numero=numero,
            serie=serie,
            data_emissao=data_emissao,
            cnpj_emitente=cnpj_emit,
            cnpj_destinatario=cnpj_dest,
            tipo_movimento=tipo_movimento,
            valor_total=valor_total,
            tp_nf=tp_nf,
            items=[]
        )

        # Lê os itens
        det_list = nfe.findall('.//nfe:det', self.NAMESPACES) or nfe.findall('.//det')
        for det in det_list:
            item = self._ler_item_nfe(det)
            doc.items.append(item)

        return doc

    def _ler_item_nfe(self, det) -> Item:
        """Lê um item de NF-e."""
        prod = det.find('.//nfe:prod', self.NAMESPACES)
        if prod is None:
            prod = det.find('.//prod')
        
        codigo = prod.findtext('.//nfe:cProd', namespaces=self.NAMESPACES) or prod.findtext('.//cProd') or ""
        descricao = prod.findtext('.//nfe:xProd', namespaces=self.NAMESPACES) or prod.findtext('.//xProd') or ""
        ncm = prod.findtext('.//nfe:NCM', namespaces=self.NAMESPACES) or prod.findtext('.//NCM') or ""
        cfop = prod.findtext('.//nfe:CFOP', namespaces=self.NAMESPACES) or prod.findtext('.//CFOP') or ""
        quantidade = Decimal(prod.findtext('.//nfe:qCom', namespaces=self.NAMESPACES) or prod.findtext('.//qCom') or "0")
        valor_unitario = Decimal(prod.findtext('.//nfe:vUnCom', namespaces=self.NAMESPACES) or prod.findtext('.//vUnCom') or "0")
        valor_total = Decimal(prod.findtext('.//nfe:vProd', namespaces=self.NAMESPACES) or prod.findtext('.//vProd') or "0")

        item = Item(
            codigo=codigo,
            descricao=descricao,
            ncm=ncm,
            cfop=cfop,
            quantidade=quantidade,
            valor_unitario=valor_unitario,
            valor_total=valor_total,
            tributos=[]
        )

        # Lê tributos
        imposto = det.find('.//nfe:imposto', self.NAMESPACES)
        if imposto is None:
            imposto = det.find('.//imposto')
        if imposto is not None:
            item.tributos.extend(self._ler_tributos_item(imposto))

        return item

    def _ler_tributos_item(self, imposto) -> list:
        """Lê tributos de um item."""
        tributos = []

        # ICMS
        icms = imposto.find('.//nfe:ICMS', self.NAMESPACES)
        if icms is None:
            icms = imposto.find('.//ICMS')
        if icms is not None:
            # Pode ter vários tipos: ICMS00, ICMS10, etc.
            for child in icms:
                cst = child.findtext('.//nfe:CST', namespaces=self.NAMESPACES) or child.findtext('.//CST') or \
                      child.findtext('.//nfe:CSOSN', namespaces=self.NAMESPACES) or child.findtext('.//CSOSN') or ""
                v_bc = Decimal(child.findtext('.//nfe:vBC', namespaces=self.NAMESPACES) or child.findtext('.//vBC') or "0")
                p_icms = Decimal(child.findtext('.//nfe:pICMS', namespaces=self.NAMESPACES) or child.findtext('.//pICMS') or "0")
                v_icms = Decimal(child.findtext('.//nfe:vICMS', namespaces=self.NAMESPACES) or child.findtext('.//vICMS') or "0")
                
                if v_icms > 0:
                    tributos.append(Tributo(
                        tipo=TipoTributo.ICMS,
                        base_calculo=v_bc,
                        aliquota=p_icms,
                        valor=v_icms,
                        cst=cst
                    ))

        # IPI
        ipi = imposto.find('.//nfe:IPI', self.NAMESPACES)
        if ipi is None:
            ipi = imposto.find('.//IPI')
        if ipi is not None:
            ipi_trib = ipi.find('.//nfe:IPITrib', self.NAMESPACES)
            if ipi_trib is None:
                ipi_trib = ipi.find('.//IPITrib')
            if ipi_trib is not None:
                cst = ipi_trib.findtext('.//nfe:CST', namespaces=self.NAMESPACES) or ipi_trib.findtext('.//CST') or ""
                v_bc = Decimal(ipi_trib.findtext('.//nfe:vBC', namespaces=self.NAMESPACES) or ipi_trib.findtext('.//vBC') or "0")
                p_ipi = Decimal(ipi_trib.findtext('.//nfe:pIPI', namespaces=self.NAMESPACES) or ipi_trib.findtext('.//pIPI') or "0")
                v_ipi = Decimal(ipi_trib.findtext('.//nfe:vIPI', namespaces=self.NAMESPACES) or ipi_trib.findtext('.//vIPI') or "0")
                
                if v_ipi > 0:
                    tributos.append(Tributo(
                        tipo=TipoTributo.IPI,
                        base_calculo=v_bc,
                        aliquota=p_ipi,
                        valor=v_ipi,
                        cst=cst
                    ))

        # PIS
        pis = imposto.find('.//nfe:PIS', self.NAMESPACES)
        if pis is None:
            pis = imposto.find('.//PIS')
        if pis is not None:
            for child in pis:
                cst = child.findtext('.//nfe:CST', namespaces=self.NAMESPACES) or child.findtext('.//CST') or ""
                v_bc = Decimal(child.findtext('.//nfe:vBC', namespaces=self.NAMESPACES) or child.findtext('.//vBC') or "0")
                p_pis = Decimal(child.findtext('.//nfe:pPIS', namespaces=self.NAMESPACES) or child.findtext('.//pPIS') or "0")
                v_pis = Decimal(child.findtext('.//nfe:vPIS', namespaces=self.NAMESPACES) or child.findtext('.//vPIS') or "0")
                
                if v_pis > 0:
                    tributos.append(Tributo(
                        tipo=TipoTributo.PIS,
                        base_calculo=v_bc,
                        aliquota=p_pis,
                        valor=v_pis,
                        cst=cst
                    ))

        # COFINS
        cofins = imposto.find('.//nfe:COFINS', self.NAMESPACES)
        if cofins is None:
            cofins = imposto.find('.//COFINS')
        if cofins is not None:
            for child in cofins:
                cst = child.findtext('.//nfe:CST', namespaces=self.NAMESPACES) or child.findtext('.//CST') or ""
                v_bc = Decimal(child.findtext('.//nfe:vBC', namespaces=self.NAMESPACES) or child.findtext('.//vBC') or "0")
                p_cofins = Decimal(child.findtext('.//nfe:pCOFINS', namespaces=self.NAMESPACES) or child.findtext('.//pCOFINS') or "0")
                v_cofins = Decimal(child.findtext('.//nfe:vCOFINS', namespaces=self.NAMESPACES) or child.findtext('.//vCOFINS') or "0")
                
                if v_cofins > 0:
                    tributos.append(Tributo(
                        tipo=TipoTributo.COFINS,
                        base_calculo=v_bc,
                        aliquota=p_cofins,
                        valor=v_cofins,
                        cst=cst
                    ))

        # IBS e CBS (Reforma Tributária)
        ibscbs = imposto.find('.//nfe:IBSCBS', self.NAMESPACES)
        if ibscbs is None:
            ibscbs = imposto.find('.//IBSCBS')
        if ibscbs is not None:
            cst = ibscbs.findtext('.//nfe:CST', namespaces=self.NAMESPACES) or ibscbs.findtext('.//CST') or ""
            
            # Lê informações de IBS e CBS
            g_ibscbs = ibscbs.find('.//nfe:gIBSCBS', self.NAMESPACES)
            if g_ibscbs is None:
                g_ibscbs = ibscbs.find('.//gIBSCBS')
            
            if g_ibscbs is not None:
                # Base de cálculo comum
                v_bc = Decimal(g_ibscbs.findtext('.//nfe:vBC', namespaces=self.NAMESPACES) or g_ibscbs.findtext('.//vBC') or "0")
                
                # IBS (Imposto sobre Bens e Serviços)
                v_ibs = Decimal(g_ibscbs.findtext('.//nfe:vIBS', namespaces=self.NAMESPACES) or g_ibscbs.findtext('.//vIBS') or "0")
                
                # Lê alíquotas de IBS (UF + Municipal)
                g_ibs_uf = g_ibscbs.find('.//nfe:gIBSUF', self.NAMESPACES)
                if g_ibs_uf is None:
                    g_ibs_uf = g_ibscbs.find('.//gIBSUF')
                p_ibs_uf = Decimal((g_ibs_uf.findtext('.//nfe:pIBSUF', namespaces=self.NAMESPACES) or g_ibs_uf.findtext('.//pIBSUF') or "0") if g_ibs_uf is not None else "0")
                
                g_ibs_mun = g_ibscbs.find('.//nfe:gIBSMun', self.NAMESPACES)
                if g_ibs_mun is None:
                    g_ibs_mun = g_ibscbs.find('.//gIBSMun')
                p_ibs_mun = Decimal((g_ibs_mun.findtext('.//nfe:pIBSMun', namespaces=self.NAMESPACES) or g_ibs_mun.findtext('.//pIBSMun') or "0") if g_ibs_mun is not None else "0")
                
                p_ibs = p_ibs_uf + p_ibs_mun
                
                if v_ibs > 0:
                    tributos.append(Tributo(
                        tipo=TipoTributo.IBS,
                        base_calculo=v_bc,
                        aliquota=p_ibs,
                        valor=v_ibs,
                        cst=cst
                    ))
                
                # CBS (Contribuição sobre Bens e Serviços)
                g_cbs = g_ibscbs.find('.//nfe:gCBS', self.NAMESPACES)
                if g_cbs is None:
                    g_cbs = g_ibscbs.find('.//gCBS')
                
                if g_cbs is not None:
                    p_cbs = Decimal(g_cbs.findtext('.//nfe:pCBS', namespaces=self.NAMESPACES) or g_cbs.findtext('.//pCBS') or "0")
                    v_cbs = Decimal(g_cbs.findtext('.//nfe:vCBS', namespaces=self.NAMESPACES) or g_cbs.findtext('.//vCBS') or "0")
                    
                    if v_cbs > 0:
                        tributos.append(Tributo(
                            tipo=TipoTributo.CBS,
                            base_calculo=v_bc,
                            aliquota=p_cbs,
                            valor=v_cbs,
                            cst=cst
                        ))

        return tributos

    def _ler_cte(self, root) -> DocumentoFiscal:
        """Lê dados de um CT-e."""
        # Busca o nó infCte
        cte = root.find('.//cte:infCte', self.NAMESPACES)
        if cte is None:
            cte = root.find('.//infCte')
        
        if cte is None:
            raise ValueError("Estrutura de CT-e inválida")

        # Dados da identificação
        ide = cte.find('.//cte:ide', self.NAMESPACES) or cte.find('.//ide')
        chave = cte.get('Id', '').replace('CTe', '')
        numero = ide.findtext('.//cte:nCT', namespaces=self.NAMESPACES) or ide.findtext('.//nCT') or ""
        serie = ide.findtext('.//cte:serie', namespaces=self.NAMESPACES) or ide.findtext('.//serie') or ""
        data_emissao_str = ide.findtext('.//cte:dhEmi', namespaces=self.NAMESPACES) or ide.findtext('.//dhEmi') or ""
        tp_ct = ide.findtext('.//cte:tpCTe', namespaces=self.NAMESPACES) or ide.findtext('.//tpCTe') or ""
        cfop = ide.findtext('.//cte:CFOP', namespaces=self.NAMESPACES) or ide.findtext('.//CFOP') or ""

        data_emissao = datetime.fromisoformat(data_emissao_str.replace('Z', '+00:00')) if data_emissao_str else datetime.now()

        # Dados do emitente
        emit = cte.find('.//cte:emit', self.NAMESPACES) or cte.find('.//emit')
        cnpj_emit = emit.findtext('.//cte:CNPJ', namespaces=self.NAMESPACES) or emit.findtext('.//CNPJ') or ""

        # Dados do destinatário
        dest = cte.find('.//cte:dest', self.NAMESPACES) or cte.find('.//dest')
        cnpj_dest = ""
        if dest is not None:
            cnpj_dest = dest.findtext('.//cte:CNPJ', namespaces=self.NAMESPACES) or dest.findtext('.//CNPJ') or ""

        # Valor total
        vPrest = cte.find('.//cte:vPrest', self.NAMESPACES) or cte.find('.//vPrest')
        valor_total = Decimal(vPrest.findtext('.//cte:vTPrest', namespaces=self.NAMESPACES) or vPrest.findtext('.//vTPrest') or "0")

        # Classifica movimento baseado em CFOP e CNPJs
        tp_nf = "0" if cfop.startswith(("1", "2", "3")) else "1"
        tipo_movimento = self._classificar_movimento(cnpj_emit, cnpj_dest, tp_nf)

        doc = DocumentoFiscal(
            tipo=TipoDocumento.CTE,
            chave=chave,
            numero=numero,
            serie=serie,
            data_emissao=data_emissao,
            cnpj_emitente=cnpj_emit,
            cnpj_destinatario=cnpj_dest,
            tipo_movimento=tipo_movimento,
            valor_total=valor_total,
            tp_nf=tp_nf,
            items=[]
        )

        return doc

    def _classificar_movimento(self, cnpj_emit: str, cnpj_dest: str, tp_nf: str, cfop: str = "") -> TipoMovimento:
        """
        Classifica o documento como Entrada ou Saída.
        
        Critérios (em ordem de prioridade):
        1. Se CFOP começa com 1, 2, 3: Entrada (MAIS CONFIÁVEL)
        2. Se CFOP começa com 5, 6, 7: Saída (MAIS CONFIÁVEL)
        3. Se CNPJ empresa = CNPJ destinatário: Entrada
        4. Se CNPJ empresa = CNPJ emitente: Saída
        5. Se tpNF = 0: Entrada
        6. Se tpNF = 1: Saída
        """
        # Critério 1 e 2: Verifica pelo CFOP (MAIS CONFIÁVEL)
        if cfop:
            primeiro_digito = cfop[0] if len(cfop) > 0 else ""
            if primeiro_digito in ["1", "2", "3"]:
                return TipoMovimento.ENTRADA
            elif primeiro_digito in ["5", "6", "7"]:
                return TipoMovimento.SAIDA

        # Normaliza CNPJs
        cnpj_emit_norm = cnpj_emit.replace(".", "").replace("/", "").replace("-", "").strip()
        cnpj_dest_norm = cnpj_dest.replace(".", "").replace("/", "").replace("-", "").strip()
        cnpj_empresa_norm = self.cnpj_empresa.strip()

        # Critério 3 e 4: Verifica pelo CNPJ
        if cnpj_dest_norm and cnpj_dest_norm == cnpj_empresa_norm:
            return TipoMovimento.ENTRADA
        elif cnpj_emit_norm and cnpj_emit_norm == cnpj_empresa_norm:
            return TipoMovimento.SAIDA

        # Critério 5 e 6: Verifica pelo tpNF
        if tp_nf == "0":
            return TipoMovimento.ENTRADA
        elif tp_nf == "1":
            return TipoMovimento.SAIDA

        # Default: considera entrada se não conseguiu determinar
        # (melhor errar para o lado conservador)
        return TipoMovimento.ENTRADA
