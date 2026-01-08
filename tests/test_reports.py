"""
Tests for reports module.
"""
import json
from datetime import datetime
from decimal import Decimal
from fiscal_auditor.models import (
    DocumentoFiscal,
    Item,
    Tributo,
    TipoDocumento,
    TipoMovimento,
    TipoTributo,
    ResultadoValidacao,
    MapaApuracao,
    ApuracaoTributo,
    MemoriaCalculo
)
from fiscal_auditor.reports import GeradorRelatorios


def test_gerar_demonstrativo_entradas():
    """Test generating entradas report."""
    gerador = GeradorRelatorios()
    
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
        cfop="1101",
        quantidade=Decimal("10"),
        valor_unitario=Decimal("100"),
        valor_total=Decimal("1000"),
        tributos=[tributo]
    )
    doc.items.append(item)
    
    relatorio = gerador.gerar_demonstrativo_entradas([doc])
    
    assert relatorio["tipo"] == "Demonstrativo de Entradas"
    assert relatorio["quantidade_documentos"] == 1
    assert relatorio["valor_total"] == "1000.00"
    assert "tributos_totais" in relatorio
    assert "ICMS" in relatorio["tributos_totais"]


def test_gerar_demonstrativo_saidas():
    """Test generating saídas report."""
    gerador = GeradorRelatorios()
    
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
    
    relatorio = gerador.gerar_demonstrativo_saidas([doc])
    
    assert relatorio["tipo"] == "Demonstrativo de Saídas"
    assert relatorio["quantidade_documentos"] == 1
    assert relatorio["valor_total"] == "1000.00"


def test_gerar_mapa_apuracao():
    """Test generating mapa de apuração report."""
    gerador = GeradorRelatorios()
    
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
    
    relatorio = gerador.gerar_mapa_apuracao(mapa)
    
    assert relatorio["periodo"] == "01/2024"
    assert len(relatorio["apuracoes"]) == 1


def test_gerar_relatorio_validacao():
    """Test generating validation report."""
    gerador = GeradorRelatorios()
    
    tributo_aproveitavel = Tributo(
        tipo=TipoTributo.ICMS,
        base_calculo=Decimal("1000.00"),
        aliquota=Decimal("18.00"),
        valor=Decimal("180.00"),
        cst="00"
    )
    
    tributo_indevido = Tributo(
        tipo=TipoTributo.ICMS,
        base_calculo=Decimal("500.00"),
        aliquota=Decimal("18.00"),
        valor=Decimal("90.00"),
        cst="40"
    )
    
    validacao = ResultadoValidacao(valido=True)
    validacao.creditos_aproveitaveis.append(tributo_aproveitavel)
    validacao.creditos_indevidos.append(tributo_indevido)
    
    relatorio = gerador.gerar_relatorio_validacao([validacao])
    
    assert relatorio["tipo"] == "Relatório de Validação"
    assert relatorio["total_validacoes"] == 1
    assert "resumo_creditos" in relatorio
    assert relatorio["resumo_creditos"]["aproveitaveis"]["quantidade"] == 1
    assert relatorio["resumo_creditos"]["indevidos"]["quantidade"] == 1


def test_gerar_relatorio_completo():
    """Test generating complete report."""
    gerador = GeradorRelatorios()
    
    # Documento
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
    
    # Mapa de apuração
    memoria = MemoriaCalculo(
        descricao="Apuração ICMS",
        valores={"debitos": Decimal("180"), "creditos": Decimal("0")},
        formula="Saldo = Débitos - Créditos",
        resultado=Decimal("180")
    )
    
    apuracao = ApuracaoTributo(
        tipo=TipoTributo.ICMS,
        debitos=Decimal("180.00"),
        creditos=Decimal("0.00"),
        saldo=Decimal("180.00"),
        memoria_calculo=memoria
    )
    
    mapa = MapaApuracao(periodo="01/2024")
    mapa.apuracoes.append(apuracao)
    
    # Validação
    validacao = ResultadoValidacao(valido=True)
    
    # Gera relatório completo
    relatorio = gerador.gerar_relatorio_completo([doc], mapa, [validacao])
    
    assert relatorio["tipo"] == "Relatório Completo de Auditoria Fiscal"
    assert relatorio["periodo"] == "01/2024"
    assert "demonstrativo_entradas" in relatorio
    assert "demonstrativo_saidas" in relatorio
    assert "mapa_apuracao" in relatorio
    assert "validacao" in relatorio


def test_exportar_json_str():
    """Test exporting report as JSON string."""
    gerador = GeradorRelatorios()
    
    relatorio = {
        "tipo": "Test",
        "valor": "1000.00"
    }
    
    json_str = gerador.exportar_json_str(relatorio)
    
    # Verifica se é um JSON válido
    parsed = json.loads(json_str)
    assert parsed["tipo"] == "Test"
    assert parsed["valor"] == "1000.00"
