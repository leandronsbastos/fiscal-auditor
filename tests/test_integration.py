"""
Integration tests using sample XML files.
"""
import os
from decimal import Decimal
from fiscal_auditor import (
    XMLReader,
    ValidadorTributario,
    ApuradorTributario,
    GeradorRelatorios,
    TipoMovimento,
    TipoTributo
)


def test_ler_nfe_saida():
    """Test reading NF-e de saída."""
    # CNPJ da empresa emitente
    cnpj_empresa = "12345678000190"
    reader = XMLReader(cnpj_empresa)
    
    # Caminho para o XML de teste
    base_path = os.path.dirname(__file__)
    xml_path = os.path.join(base_path, "fixtures", "nfe_saida.xml")
    
    # Lê o XML
    doc = reader.ler_xml(xml_path)
    
    # Verifica dados do documento
    assert doc.numero == "123"
    assert doc.serie == "1"
    assert doc.cnpj_emitente == "12345678000190"
    assert doc.cnpj_destinatario == "98765432000110"
    assert doc.tipo_movimento == TipoMovimento.SAIDA
    assert doc.valor_total == Decimal("1372.50")
    
    # Verifica itens
    assert len(doc.items) == 1
    item = doc.items[0]
    assert item.codigo == "001"
    assert item.ncm == "12345678"
    assert item.cfop == "5101"
    
    # Verifica tributos
    assert len(item.tributos) == 4  # ICMS, IPI, PIS, COFINS
    
    # Verifica ICMS
    icms = next((t for t in item.tributos if t.tipo == TipoTributo.ICMS), None)
    assert icms is not None
    assert icms.valor == Decimal("180.00")
    assert icms.aliquota == Decimal("18.00")


def test_ler_nfe_entrada():
    """Test reading NF-e de entrada."""
    # CNPJ da empresa destinatária
    cnpj_empresa = "12345678000190"
    reader = XMLReader(cnpj_empresa)
    
    # Caminho para o XML de teste
    base_path = os.path.dirname(__file__)
    xml_path = os.path.join(base_path, "fixtures", "nfe_entrada.xml")
    
    # Lê o XML
    doc = reader.ler_xml(xml_path)
    
    # Verifica dados do documento
    assert doc.numero == "456"
    assert doc.cnpj_emitente == "98765432000110"
    assert doc.cnpj_destinatario == "12345678000190"
    assert doc.tipo_movimento == TipoMovimento.ENTRADA
    
    # Verifica itens
    assert len(doc.items) == 1
    item = doc.items[0]
    assert item.cfop == "1101"
    
    # Verifica tributos
    assert len(item.tributos) == 4


def test_validacao_completa():
    """Test complete validation process."""
    cnpj_empresa = "12345678000190"
    reader = XMLReader(cnpj_empresa)
    validador = ValidadorTributario()
    
    base_path = os.path.dirname(__file__)
    
    # Lê e valida NF-e de entrada
    xml_entrada = os.path.join(base_path, "fixtures", "nfe_entrada.xml")
    doc_entrada = reader.ler_xml(xml_entrada)
    resultado_entrada = validador.validar_documento(doc_entrada)
    
    assert resultado_entrada.valido
    # Deve ter créditos aproveitáveis (entrada com CFOP 1101 e CST 00)
    assert len(resultado_entrada.creditos_aproveitaveis) > 0
    
    # Lê e valida NF-e de saída
    xml_saida = os.path.join(base_path, "fixtures", "nfe_saida.xml")
    doc_saida = reader.ler_xml(xml_saida)
    resultado_saida = validador.validar_documento(doc_saida)
    
    assert resultado_saida.valido


def test_apuracao_completa():
    """Test complete tax calculation."""
    cnpj_empresa = "12345678000190"
    reader = XMLReader(cnpj_empresa)
    apurador = ApuradorTributario()
    
    base_path = os.path.dirname(__file__)
    
    # Lê NF-e de entrada
    xml_entrada = os.path.join(base_path, "fixtures", "nfe_entrada.xml")
    doc_entrada = reader.ler_xml(xml_entrada)
    apurador.adicionar_documento(doc_entrada)
    
    # Lê NF-e de saída
    xml_saida = os.path.join(base_path, "fixtures", "nfe_saida.xml")
    doc_saida = reader.ler_xml(xml_saida)
    apurador.adicionar_documento(doc_saida)
    
    # Realiza apuração
    mapa = apurador.apurar("01/2024")
    
    assert mapa.periodo == "01/2024"
    assert len(mapa.apuracoes) > 0
    
    # Verifica apuração do ICMS
    apuracao_icms = next((a for a in mapa.apuracoes if a.tipo == TipoTributo.ICMS), None)
    assert apuracao_icms is not None
    assert apuracao_icms.debitos == Decimal("180.00")  # Da saída
    assert apuracao_icms.creditos == Decimal("90.00")  # Da entrada
    assert apuracao_icms.saldo == Decimal("90.00")  # 180 - 90


def test_geracao_relatorio_completo():
    """Test complete report generation."""
    cnpj_empresa = "12345678000190"
    reader = XMLReader(cnpj_empresa)
    validador = ValidadorTributario()
    apurador = ApuradorTributario()
    gerador = GeradorRelatorios()
    
    base_path = os.path.dirname(__file__)
    
    documentos = []
    validacoes = []
    
    # Processa NF-e de entrada
    xml_entrada = os.path.join(base_path, "fixtures", "nfe_entrada.xml")
    doc_entrada = reader.ler_xml(xml_entrada)
    documentos.append(doc_entrada)
    validacoes.append(validador.validar_documento(doc_entrada))
    apurador.adicionar_documento(doc_entrada)
    
    # Processa NF-e de saída
    xml_saida = os.path.join(base_path, "fixtures", "nfe_saida.xml")
    doc_saida = reader.ler_xml(xml_saida)
    documentos.append(doc_saida)
    validacoes.append(validador.validar_documento(doc_saida))
    apurador.adicionar_documento(doc_saida)
    
    # Gera mapa de apuração
    mapa = apurador.apurar("01/2024")
    
    # Gera relatório completo
    relatorio = gerador.gerar_relatorio_completo(documentos, mapa, validacoes)
    
    assert relatorio["tipo"] == "Relatório Completo de Auditoria Fiscal"
    assert relatorio["periodo"] == "01/2024"
    assert "demonstrativo_entradas" in relatorio
    assert "demonstrativo_saidas" in relatorio
    assert "mapa_apuracao" in relatorio
    assert "validacao" in relatorio
    
    # Verifica demonstrativo de entradas
    demo_entradas = relatorio["demonstrativo_entradas"]
    assert demo_entradas["quantidade_documentos"] == 1
    
    # Verifica demonstrativo de saídas
    demo_saidas = relatorio["demonstrativo_saidas"]
    assert demo_saidas["quantidade_documentos"] == 1
    
    # Testa exportação para JSON string
    json_str = gerador.exportar_json_str(relatorio)
    assert len(json_str) > 0
    assert "Relatório Completo de Auditoria Fiscal" in json_str
