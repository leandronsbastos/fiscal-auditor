"""
Tests for calculator module.
"""
from datetime import datetime
from decimal import Decimal
from fiscal_auditor.models import (
    DocumentoFiscal,
    Item,
    Tributo,
    TipoDocumento,
    TipoMovimento,
    TipoTributo
)
from fiscal_auditor.calculator import ApuradorTributario


def test_adicionar_documento():
    """Test adding documents to calculator."""
    apurador = ApuradorTributario()
    
    doc = DocumentoFiscal(
        tipo=TipoDocumento.NFE,
        chave="12345678901234567890123456789012345678901234",
        numero="123",
        serie="1",
        data_emissao=datetime.now(),
        cnpj_emitente="12345678000190",
        cnpj_destinatario="98765432000110",
        tipo_movimento=TipoMovimento.SAIDA,
        valor_total=Decimal("1000.00")
    )
    
    apurador.adicionar_documento(doc)
    assert len(apurador.documentos) == 1


def test_calcular_debitos():
    """Test calculating debits."""
    apurador = ApuradorTributario()
    
    # Documento de saída com ICMS
    doc = DocumentoFiscal(
        tipo=TipoDocumento.NFE,
        chave="12345678901234567890123456789012345678901234",
        numero="123",
        serie="1",
        data_emissao=datetime.now(),
        cnpj_emitente="12345678000190",
        cnpj_destinatario="98765432000110",
        tipo_movimento=TipoMovimento.SAIDA,
        valor_total=Decimal("1000.00")
    )
    
    tributo = Tributo(
        tipo=TipoTributo.ICMS,
        base_calculo=Decimal("1000.00"),
        aliquota=Decimal("18.00"),
        valor=Decimal("180.00"),
        cst="00"
    )
    
    item = Item(
        codigo="001",
        descricao="Produto",
        ncm="12345678",
        cfop="5101",
        quantidade=Decimal("10"),
        valor_unitario=Decimal("100"),
        valor_total=Decimal("1000"),
        tributos=[tributo]
    )
    doc.items.append(item)
    
    apurador.adicionar_documento(doc)
    
    total_debitos = apurador.calcular_total_debitos(TipoTributo.ICMS)
    assert total_debitos == Decimal("180.00")


def test_calcular_creditos():
    """Test calculating credits."""
    apurador = ApuradorTributario()
    
    # Documento de entrada com ICMS
    doc = DocumentoFiscal(
        tipo=TipoDocumento.NFE,
        chave="12345678901234567890123456789012345678901234",
        numero="123",
        serie="1",
        data_emissao=datetime.now(),
        cnpj_emitente="12345678000190",
        cnpj_destinatario="98765432000110",
        tipo_movimento=TipoMovimento.ENTRADA,
        valor_total=Decimal("500.00")
    )
    
    tributo = Tributo(
        tipo=TipoTributo.ICMS,
        base_calculo=Decimal("500.00"),
        aliquota=Decimal("18.00"),
        valor=Decimal("90.00"),
        cst="00"
    )
    
    item = Item(
        codigo="001",
        descricao="Produto",
        ncm="12345678",
        cfop="1101",
        quantidade=Decimal("5"),
        valor_unitario=Decimal("100"),
        valor_total=Decimal("500"),
        tributos=[tributo]
    )
    doc.items.append(item)
    
    apurador.adicionar_documento(doc)
    
    total_creditos = apurador.calcular_total_creditos(TipoTributo.ICMS)
    assert total_creditos == Decimal("90.00")


def test_apuracao_completa():
    """Test complete tax calculation."""
    apurador = ApuradorTributario()
    
    # Documento de saída
    doc_saida = DocumentoFiscal(
        tipo=TipoDocumento.NFE,
        chave="12345678901234567890123456789012345678901234",
        numero="123",
        serie="1",
        data_emissao=datetime.now(),
        cnpj_emitente="12345678000190",
        cnpj_destinatario="98765432000110",
        tipo_movimento=TipoMovimento.SAIDA,
        valor_total=Decimal("1000.00")
    )
    
    tributo_saida = Tributo(
        tipo=TipoTributo.ICMS,
        base_calculo=Decimal("1000.00"),
        aliquota=Decimal("18.00"),
        valor=Decimal("180.00"),
        cst="00"
    )
    
    item_saida = Item(
        codigo="001",
        descricao="Produto",
        ncm="12345678",
        cfop="5101",
        quantidade=Decimal("10"),
        valor_unitario=Decimal("100"),
        valor_total=Decimal("1000"),
        tributos=[tributo_saida]
    )
    doc_saida.items.append(item_saida)
    
    # Documento de entrada
    doc_entrada = DocumentoFiscal(
        tipo=TipoDocumento.NFE,
        chave="98765432109876543210987654321098765432109876",
        numero="456",
        serie="1",
        data_emissao=datetime.now(),
        cnpj_emitente="98765432000110",
        cnpj_destinatario="12345678000190",
        tipo_movimento=TipoMovimento.ENTRADA,
        valor_total=Decimal("500.00")
    )
    
    tributo_entrada = Tributo(
        tipo=TipoTributo.ICMS,
        base_calculo=Decimal("500.00"),
        aliquota=Decimal("18.00"),
        valor=Decimal("90.00"),
        cst="00"
    )
    
    item_entrada = Item(
        codigo="002",
        descricao="Produto",
        ncm="12345678",
        cfop="1101",
        quantidade=Decimal("5"),
        valor_unitario=Decimal("100"),
        valor_total=Decimal("500"),
        tributos=[tributo_entrada]
    )
    doc_entrada.items.append(item_entrada)
    
    # Adiciona documentos
    apurador.adicionar_documentos([doc_saida, doc_entrada])
    
    # Realiza apuração
    mapa = apurador.apurar("01/2024")
    
    assert mapa.periodo == "01/2024"
    assert len(mapa.apuracoes) > 0
    
    # Encontra apuração do ICMS
    apuracao_icms = next((a for a in mapa.apuracoes if a.tipo == TipoTributo.ICMS), None)
    assert apuracao_icms is not None
    assert apuracao_icms.debitos == Decimal("180.00")
    assert apuracao_icms.creditos == Decimal("90.00")
    assert apuracao_icms.saldo == Decimal("90.00")  # 180 - 90


def test_obter_documentos_por_tipo():
    """Test filtering documents by type."""
    apurador = ApuradorTributario()
    
    doc_entrada = DocumentoFiscal(
        tipo=TipoDocumento.NFE,
        chave="123",
        numero="123",
        serie="1",
        data_emissao=datetime.now(),
        cnpj_emitente="12345678000190",
        cnpj_destinatario="98765432000110",
        tipo_movimento=TipoMovimento.ENTRADA,
        valor_total=Decimal("500.00")
    )
    
    doc_saida = DocumentoFiscal(
        tipo=TipoDocumento.NFE,
        chave="456",
        numero="456",
        serie="1",
        data_emissao=datetime.now(),
        cnpj_emitente="98765432000110",
        cnpj_destinatario="12345678000190",
        tipo_movimento=TipoMovimento.SAIDA,
        valor_total=Decimal("1000.00")
    )
    
    apurador.adicionar_documentos([doc_entrada, doc_saida])
    
    entradas = apurador.obter_documentos_por_tipo(TipoMovimento.ENTRADA)
    saidas = apurador.obter_documentos_por_tipo(TipoMovimento.SAIDA)
    
    assert len(entradas) == 1
    assert len(saidas) == 1


def test_limpar_documentos():
    """Test clearing documents."""
    apurador = ApuradorTributario()
    
    doc = DocumentoFiscal(
        tipo=TipoDocumento.NFE,
        chave="123",
        numero="123",
        serie="1",
        data_emissao=datetime.now(),
        cnpj_emitente="12345678000190",
        cnpj_destinatario="98765432000110",
        tipo_movimento=TipoMovimento.ENTRADA,
        valor_total=Decimal("500.00")
    )
    
    apurador.adicionar_documento(doc)
    assert len(apurador.documentos) == 1
    
    apurador.limpar_documentos()
    assert len(apurador.documentos) == 0
