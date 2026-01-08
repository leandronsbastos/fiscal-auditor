"""
Tests for data models.
"""
from datetime import datetime
from decimal import Decimal
from fiscal_auditor.models import (
    TipoDocumento,
    TipoMovimento,
    TipoTributo,
    DocumentoFiscal,
    Item,
    Tributo,
    MemoriaCalculo,
    ApuracaoTributo,
    MapaApuracao
)


def test_memoria_calculo_to_dict():
    """Test MemoriaCalculo serialization."""
    memoria = MemoriaCalculo(
        descricao="Test calculation",
        valores={"valor1": Decimal("100.50"), "valor2": 50},
        formula="valor1 + valor2",
        resultado=Decimal("150.50")
    )
    
    result = memoria.to_dict()
    assert result["descricao"] == "Test calculation"
    assert result["valores"]["valor1"] == "100.50"
    assert result["valores"]["valor2"] == 50
    assert result["formula"] == "valor1 + valor2"
    assert result["resultado"] == "150.50"


def test_tributo_creation():
    """Test Tributo creation."""
    tributo = Tributo(
        tipo=TipoTributo.ICMS,
        base_calculo=Decimal("1000.00"),
        aliquota=Decimal("18.00"),
        valor=Decimal("180.00"),
        cst="00"
    )
    
    assert tributo.tipo == TipoTributo.ICMS
    assert tributo.base_calculo == Decimal("1000.00")
    assert tributo.aliquota == Decimal("18.00")
    assert tributo.valor == Decimal("180.00")
    assert tributo.cst == "00"


def test_item_creation():
    """Test Item creation."""
    item = Item(
        codigo="001",
        descricao="Produto Teste",
        ncm="12345678",
        cfop="5101",
        quantidade=Decimal("10.00"),
        valor_unitario=Decimal("100.00"),
        valor_total=Decimal("1000.00")
    )
    
    assert item.codigo == "001"
    assert item.ncm == "12345678"
    assert item.cfop == "5101"


def test_documento_fiscal_creation():
    """Test DocumentoFiscal creation."""
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
    
    assert doc.tipo == TipoDocumento.NFE
    assert doc.tipo_movimento == TipoMovimento.SAIDA
    assert doc.valor_total == Decimal("1000.00")


def test_apuracao_tributo():
    """Test ApuracaoTributo."""
    memoria = MemoriaCalculo(
        descricao="Apuração ICMS",
        valores={"debitos": Decimal("1000"), "creditos": Decimal("300")},
        formula="Saldo = Débitos - Créditos",
        resultado=Decimal("700")
    )
    
    apuracao = ApuracaoTributo(
        tipo=TipoTributo.ICMS,
        debitos=Decimal("1000.00"),
        creditos=Decimal("300.00"),
        saldo=Decimal("700.00"),
        memoria_calculo=memoria
    )
    
    assert apuracao.tipo == TipoTributo.ICMS
    assert apuracao.saldo == Decimal("700.00")


def test_mapa_apuracao():
    """Test MapaApuracao."""
    memoria = MemoriaCalculo(
        descricao="Apuração ICMS",
        valores={"debitos": Decimal("1000"), "creditos": Decimal("300")},
        formula="Saldo = Débitos - Créditos",
        resultado=Decimal("700")
    )
    
    apuracao = ApuracaoTributo(
        tipo=TipoTributo.ICMS,
        debitos=Decimal("1000.00"),
        creditos=Decimal("300.00"),
        saldo=Decimal("700.00"),
        memoria_calculo=memoria
    )
    
    mapa = MapaApuracao(periodo="01/2024")
    mapa.apuracoes.append(apuracao)
    
    assert mapa.periodo == "01/2024"
    assert len(mapa.apuracoes) == 1
    
    result = mapa.to_dict()
    assert result["periodo"] == "01/2024"
    assert len(result["apuracoes"]) == 1
