"""
Tests for validator module.
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
from fiscal_auditor.validator import ValidadorTributario


def test_validador_cfop_entrada():
    """Test CFOP validation for entrada."""
    validador = ValidadorTributario()
    
    doc = DocumentoFiscal(
        tipo=TipoDocumento.NFE,
        chave="12345678901234567890123456789012345678901234",
        numero="123",
        serie="1",
        data_emissao=datetime.now(),
        cnpj_emitente="12345678000190",
        cnpj_destinatario="98765432000110",
        tipo_movimento=TipoMovimento.ENTRADA,
        valor_total=Decimal("1000.00")
    )
    
    # Item com CFOP correto para entrada
    item1 = Item(
        codigo="001",
        descricao="Produto",
        ncm="12345678",
        cfop="1101",  # CFOP de entrada
        quantidade=Decimal("10"),
        valor_unitario=Decimal("100"),
        valor_total=Decimal("1000")
    )
    doc.items.append(item1)
    
    resultado = validador.validar_documento(doc)
    assert resultado.valido


def test_validador_cfop_saida():
    """Test CFOP validation for saída."""
    validador = ValidadorTributario()
    
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
    
    # Item com CFOP correto para saída
    item1 = Item(
        codigo="001",
        descricao="Produto",
        ncm="12345678",
        cfop="5101",  # CFOP de saída
        quantidade=Decimal("10"),
        valor_unitario=Decimal("100"),
        valor_total=Decimal("1000")
    )
    doc.items.append(item1)
    
    resultado = validador.validar_documento(doc)
    assert resultado.valido


def test_validador_cfop_inconsistente():
    """Test CFOP inconsistent with movement type."""
    validador = ValidadorTributario()
    
    doc = DocumentoFiscal(
        tipo=TipoDocumento.NFE,
        chave="12345678901234567890123456789012345678901234",
        numero="123",
        serie="1",
        data_emissao=datetime.now(),
        cnpj_emitente="12345678000190",
        cnpj_destinatario="98765432000110",
        tipo_movimento=TipoMovimento.ENTRADA,
        valor_total=Decimal("1000.00")
    )
    
    # Item com CFOP de saída em documento de entrada
    item1 = Item(
        codigo="001",
        descricao="Produto",
        ncm="12345678",
        cfop="5101",  # CFOP de saída (inconsistente)
        quantidade=Decimal("10"),
        valor_unitario=Decimal("100"),
        valor_total=Decimal("1000")
    )
    doc.items.append(item1)
    
    resultado = validador.validar_documento(doc)
    assert not resultado.valido
    assert any("inconsistente" in msg.lower() for msg in resultado.mensagens)


def test_classificacao_credito_icms_aproveitavel():
    """Test ICMS credit classification as aproveitável."""
    validador = ValidadorTributario()
    
    doc = DocumentoFiscal(
        tipo=TipoDocumento.NFE,
        chave="12345678901234567890123456789012345678901234",
        numero="123",
        serie="1",
        data_emissao=datetime.now(),
        cnpj_emitente="12345678000190",
        cnpj_destinatario="98765432000110",
        tipo_movimento=TipoMovimento.ENTRADA,
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
        cfop="1101",  # CFOP que gera crédito
        quantidade=Decimal("10"),
        valor_unitario=Decimal("100"),
        valor_total=Decimal("1000"),
        tributos=[tributo]
    )
    doc.items.append(item)
    
    resultado = validador.validar_documento(doc)
    assert len(resultado.creditos_aproveitaveis) > 0


def test_calculo_tributo_correto():
    """Test correct tax calculation validation."""
    validador = ValidadorTributario()
    
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
    
    # Tributo calculado corretamente: 1000 * 18% = 180
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
    
    resultado = validador.validar_documento(doc)
    # Não deve haver mensagem de inconsistência no cálculo
    assert not any("inconsistente" in msg.lower() and "valor de icms" in msg.lower() 
                   for msg in resultado.mensagens)


def test_validar_cst():
    """Test CST validation."""
    validador = ValidadorTributario()
    
    assert validador.validar_cst("00", TipoTributo.ICMS)
    assert validador.validar_cst("101", TipoTributo.ICMS)  # CSOSN
    assert validador.validar_cst("50", TipoTributo.PIS)
    assert not validador.validar_cst("", TipoTributo.ICMS)


def test_validar_cfop_ncm():
    """Test CFOP and NCM validation."""
    validador = ValidadorTributario()
    
    assert validador.validar_cfop_ncm("5101", "12345678")
    assert validador.validar_cfop_ncm("1101", "1234567890")  # NCM com 10 dígitos
    assert not validador.validar_cfop_ncm("", "12345678")
    assert not validador.validar_cfop_ncm("5101", "123")  # NCM inválido
