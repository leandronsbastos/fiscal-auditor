"""
Integração entre o sistema fiscal-auditor e o datalake ETL.

Este módulo permite buscar dados já processados do datalake em vez de 
reprocessar arquivos XML.
"""
from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal
import os

# Importar modelos do ETL
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "etl_service"))

from etl_service.models import NFe, NFeItem, NFeDuplicata
from etl_service.database import engine as etl_engine, SessionLocal as ETLSessionLocal

# Importar modelos do fiscal-auditor
from fiscal_auditor.models import DocumentoFiscal, Item, Tributo, TipoTributo, TipoDocumento, TipoMovimento



def converter_nfe_para_documento(nfe: NFe, itens: List[NFeItem] = None) -> DocumentoFiscal:
    """
    Converte um registro NFe do datalake para o modelo DocumentoFiscal.
    
    Args:
        nfe: Objeto NFe do datalake
        itens: Lista opcional de itens da NF-e
        
    Returns:
        Objeto DocumentoFiscal compatível com o fiscal-auditor
    """
    # Determinar tipo de movimento
    tipo_movimento = TipoMovimento.ENTRADA if nfe.tipo_operacao == '0' else TipoMovimento.SAIDA
    
    # Criar documento com campos obrigatórios
    doc = DocumentoFiscal(
        tipo=TipoDocumento.NFE,
        chave=nfe.chave_acesso,
        numero=nfe.numero_nota,
        serie=nfe.serie,
        data_emissao=nfe.data_emissao,
        cnpj_emitente=nfe.emitente_cnpj or '',
        cnpj_destinatario=nfe.destinatario_cnpj or '',
        tipo_movimento=tipo_movimento,
        valor_total=Decimal(str(nfe.valor_total_nota)) if nfe.valor_total_nota else Decimal('0')
    )
    
    # Campos opcionais
    doc.tp_nf = nfe.tipo_operacao  # 0=Entrada, 1=Saída
    
    # Itens
    if itens:
        doc.items = []
        for item_nfe in itens:
            item = Item(
                codigo=item_nfe.codigo_produto,
                descricao=item_nfe.descricao,
                ncm=item_nfe.ncm or '',
                cfop=item_nfe.cfop or '',
                quantidade=Decimal(str(item_nfe.quantidade_comercial)) if item_nfe.quantidade_comercial else Decimal('0'),
                valor_unitario=Decimal(str(item_nfe.valor_unitario_comercial)) if item_nfe.valor_unitario_comercial else Decimal('0'),
                valor_total=Decimal(str(item_nfe.valor_total_bruto)) if item_nfe.valor_total_bruto else Decimal('0')
            )
            
            # Tributos
            item.tributos = []
            
            # ICMS
            if item_nfe.valor_icms and float(item_nfe.valor_icms) > 0:
                tributo_icms = Tributo(
                    tipo=TipoTributo.ICMS,
                    cst=item_nfe.situacao_tributaria_icms or '',
                    base_calculo=Decimal(str(item_nfe.base_calculo_icms)) if item_nfe.base_calculo_icms else Decimal('0'),
                    aliquota=Decimal(str(item_nfe.aliquota_icms)) if item_nfe.aliquota_icms else Decimal('0'),
                    valor=Decimal(str(item_nfe.valor_icms))
                )
                item.tributos.append(tributo_icms)
            
            # IPI
            if item_nfe.valor_ipi and float(item_nfe.valor_ipi) > 0:
                tributo_ipi = Tributo(
                    tipo=TipoTributo.IPI,
                    cst=item_nfe.situacao_tributaria_ipi or '',
                    base_calculo=Decimal('0'),
                    aliquota=Decimal(str(item_nfe.aliquota_ipi)) if item_nfe.aliquota_ipi else Decimal('0'),
                    valor=Decimal(str(item_nfe.valor_ipi))
                )
                item.tributos.append(tributo_ipi)
            
            # PIS
            if item_nfe.valor_pis and float(item_nfe.valor_pis) > 0:
                tributo_pis = Tributo(
                    tipo=TipoTributo.PIS,
                    cst=item_nfe.situacao_tributaria_pis or '',
                    base_calculo=Decimal('0'),
                    aliquota=Decimal(str(item_nfe.aliquota_pis)) if item_nfe.aliquota_pis else Decimal('0'),
                    valor=Decimal(str(item_nfe.valor_pis))
                )
                item.tributos.append(tributo_pis)
            
            # COFINS
            if item_nfe.valor_cofins and float(item_nfe.valor_cofins) > 0:
                tributo_cofins = Tributo(
                    tipo=TipoTributo.COFINS,
                    cst=item_nfe.situacao_tributaria_cofins or '',
                    base_calculo=Decimal('0'),
                    aliquota=Decimal(str(item_nfe.aliquota_cofins)) if item_nfe.aliquota_cofins else Decimal('0'),
                    valor=Decimal(str(item_nfe.valor_cofins))
                )
                item.tributos.append(tributo_cofins)
            
            doc.items.append(item)
    
    return doc


def buscar_documentos_periodo(
    cnpj: str,
    data_inicio: date,
    data_fim: date,
    tipo_data: str = 'emissao',
    tipo_operacao: Optional[str] = None,
    incluir_itens: bool = True
) -> List[DocumentoFiscal]:
    """
    Busca documentos fiscais do datalake para um CNPJ e período específicos.
    
    Args:
        cnpj: CNPJ da empresa (apenas números)
        data_inicio: Data inicial do período
        data_fim: Data final do período
        tipo_data: Tipo de data para filtrar ('emissao', 'autorizacao', 'saida_entrada')
        tipo_operacao: Filtrar por tipo ('E' para entrada, 'S' para saída, None para ambos)
        incluir_itens: Se deve incluir os itens dos documentos
        
    Returns:
        Lista de objetos DocumentoFiscal
    """
    session = ETLSessionLocal()
    
    try:
        # Limpar CNPJ
        cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        # Construir query base
        query = session.query(NFe)
        
        # Filtrar por CNPJ (pode ser emitente ou destinatário)
        query = query.filter(
            or_(
                NFe.emitente_cnpj == cnpj_limpo,
                NFe.destinatario_cnpj == cnpj_limpo
            )
        )
        
        # Filtrar por data
        if tipo_data == 'autorizacao':
            query = query.filter(
                and_(
                    NFe.data_autorizacao >= datetime.combine(data_inicio, datetime.min.time()),
                    NFe.data_autorizacao <= datetime.combine(data_fim, datetime.max.time())
                )
            )
        elif tipo_data == 'saida_entrada':
            query = query.filter(
                and_(
                    NFe.data_saida_entrada >= datetime.combine(data_inicio, datetime.min.time()),
                    NFe.data_saida_entrada <= datetime.combine(data_fim, datetime.max.time())
                )
            )
        else:  # emissao (padrão)
            query = query.filter(
                and_(
                    NFe.data_emissao >= datetime.combine(data_inicio, datetime.min.time()),
                    NFe.data_emissao <= datetime.combine(data_fim, datetime.max.time())
                )
            )
        
        # Filtrar por tipo de operação
        if tipo_operacao == 'E':  # Entrada
            query = query.filter(NFe.tipo_operacao == '0')
        elif tipo_operacao == 'S':  # Saída
            query = query.filter(NFe.tipo_operacao == '1')
        
        # Ordenar por data
        if tipo_data == 'autorizacao':
            query = query.order_by(NFe.data_autorizacao)
        elif tipo_data == 'saida_entrada':
            query = query.order_by(NFe.data_saida_entrada)
        else:
            query = query.order_by(NFe.data_emissao)
        
        # Executar query
        nfes = query.all()
        
        # Converter para DocumentoFiscal
        documentos = []
        for nfe in nfes:
            itens = None
            if incluir_itens:
                itens = session.query(NFeItem).filter(
                    NFeItem.nfe_id == nfe.id
                ).order_by(NFeItem.numero_item).all()
            
            doc = converter_nfe_para_documento(nfe, itens)
            documentos.append(doc)
        
        return documentos
        
    finally:
        session.close()


def obter_estatisticas_datalake(cnpj: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtém estatísticas do datalake.
    
    Args:
        cnpj: CNPJ para filtrar (opcional)
        
    Returns:
        Dicionário com estatísticas
    """
    session = ETLSessionLocal()
    
    try:
        query = session.query(NFe)
        
        if cnpj:
            cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")
            query = query.filter(
                or_(
                    NFe.emitente_cnpj == cnpj_limpo,
                    NFe.destinatario_cnpj == cnpj_limpo
                )
            )
        
        total_documentos = query.count()
        total_entradas = query.filter(NFe.tipo_operacao == '0').count()
        total_saidas = query.filter(NFe.tipo_operacao == '1').count()
        
        # Datas
        data_mais_antiga = session.query(func.min(NFe.data_emissao)).filter(
            query.whereclause if hasattr(query, 'whereclause') else True
        ).scalar()
        
        data_mais_recente = session.query(func.max(NFe.data_emissao)).filter(
            query.whereclause if hasattr(query, 'whereclause') else True
        ).scalar()
        
        return {
            'total_documentos': total_documentos,
            'total_entradas': total_entradas,
            'total_saidas': total_saidas,
            'data_mais_antiga': data_mais_antiga,
            'data_mais_recente': data_mais_recente
        }
        
    finally:
        session.close()


def verificar_documentos_disponiveis(
    cnpj: str,
    data_inicio: date,
    data_fim: date
) -> Dict[str, int]:
    """
    Verifica quantos documentos estão disponíveis no datalake para um período.
    
    Args:
        cnpj: CNPJ da empresa
        data_inicio: Data inicial
        data_fim: Data final
        
    Returns:
        Dicionário com contagens
    """
    session = ETLSessionLocal()
    
    try:
        cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        query = session.query(NFe).filter(
            or_(
                NFe.emitente_cnpj == cnpj_limpo,
                NFe.destinatario_cnpj == cnpj_limpo
            ),
            and_(
                NFe.data_emissao >= datetime.combine(data_inicio, datetime.min.time()),
                NFe.data_emissao <= datetime.combine(data_fim, datetime.max.time())
            )
        )
        
        total = query.count()
        entradas = query.filter(NFe.tipo_operacao == '0').count()
        saidas = query.filter(NFe.tipo_operacao == '1').count()
        
        return {
            'total': total,
            'entradas': entradas,
            'saidas': saidas
        }
        
    finally:
        session.close()
