# Fiscal Auditor

Sistema modular para auditoria e apuração tributária com base em arquivos XML de documentos fiscais eletrônicos (NF-e, NFC-e, CT-e e NFS-e).

## Descrição

Este sistema é responsável por:
- Classificar documentos fiscais como entradas ou saídas
- Validar a conformidade tributária
- Calcular a apuração dos tributos incidentes
- Gerar relatórios estruturados em formato JSON

## Módulos

### 1. Leitura e Classificação de XML (`xml_reader.py`)
- Leitura de arquivos XML contendo documentos fiscais eletrônicos
- Identificação automática se o arquivo representa uma "Entrada" ou "Saída" com base em CNPJ, tpNF, CFOP e outros indicadores

### 2. Validador Tributário (`validator.py`)
- Verifica conformidade tributária dos documentos
- Confirma CST, CFOP, NCM e outros campos para calcular corretamente débitos e créditos fiscais
- Identifica créditos aproveitáveis, indevidos e glosáveis

### 3. Apurador Tributário (`calculator.py`)
- Realiza a apuração de tributos separadamente (ICMS, IPI, PIS, COFINS, IBS/CBS)
- Fórmula: Apuração = Débitos de Saída - Créditos de Entrada
- Mantém memória de cálculo para rastreabilidade

### 4. Gerador de Relatórios (`reports.py`)
- Geração de relatórios estruturados:
  - Demonstrativo de Entradas
  - Demonstrativo de Saídas
  - Mapa de Apuração
  - Relatório de Validação
- Exportação em formato JSON

### 5. Estruturas de Dados (`models.py`)
- Modelos de dados para documentos, tributos e cálculos
- Cada cálculo e validação documentado com memória de cálculo

## Instalação

```bash
pip install -r requirements.txt
```

Ou instalar o pacote:

```bash
pip install -e .
```

## Uso Básico

```python
from fiscal_auditor import (
    XMLReader,
    ValidadorTributario,
    ApuradorTributario,
    GeradorRelatorios
)

# 1. Configurar leitor XML com CNPJ da empresa
cnpj_empresa = "12.345.678/0001-90"
reader = XMLReader(cnpj_empresa)

# 2. Ler documento XML
documento = reader.ler_xml("caminho/para/nfe.xml")

# 3. Validar documento
validador = ValidadorTributario()
resultado_validacao = validador.validar_documento(documento)

# 4. Apurar tributos
apurador = ApuradorTributario()
apurador.adicionar_documento(documento)
mapa = apurador.apurar(periodo="01/2024")

# 5. Gerar relatórios
gerador = GeradorRelatorios()
relatorio_completo = gerador.gerar_relatorio_completo(
    documentos=[documento],
    mapa=mapa,
    validacoes=[resultado_validacao]
)

# 6. Exportar para JSON
gerador.exportar_json(relatorio_completo, "relatorio.json")
```

## Exemplo Completo

```python
from fiscal_auditor import XMLReader, ValidadorTributario, ApuradorTributario, GeradorRelatorios
import os

# Configuração
cnpj_empresa = "12345678000190"
diretorio_xmls = "xmls/"
periodo = "01/2024"

# Inicializar componentes
reader = XMLReader(cnpj_empresa)
validador = ValidadorTributario()
apurador = ApuradorTributario()
gerador = GeradorRelatorios()

# Processar todos os XMLs
documentos = []
validacoes = []

for arquivo in os.listdir(diretorio_xmls):
    if arquivo.endswith('.xml'):
        caminho = os.path.join(diretorio_xmls, arquivo)
        
        # Ler XML
        doc = reader.ler_xml(caminho)
        documentos.append(doc)
        
        # Validar
        validacao = validador.validar_documento(doc)
        validacoes.append(validacao)
        
        # Adicionar para apuração
        apurador.adicionar_documento(doc)

# Realizar apuração
mapa = apurador.apurar(periodo)

# Gerar relatório completo
relatorio = gerador.gerar_relatorio_completo(
    documentos=documentos,
    mapa=mapa,
    validacoes=validacoes
)

# Exportar
gerador.exportar_json(relatorio, f"relatorio_{periodo.replace('/', '_')}.json")

# Gerar relatórios individuais
demo_entradas = gerador.gerar_demonstrativo_entradas(documentos)
gerador.exportar_json(demo_entradas, "demonstrativo_entradas.json")

demo_saidas = gerador.gerar_demonstrativo_saidas(documentos)
gerador.exportar_json(demo_saidas, "demonstrativo_saidas.json")
```

## Estrutura de Dados

### DocumentoFiscal
Representa um documento fiscal eletrônico completo:
- Tipo (NF-e, NFC-e, CT-e, NFS-e)
- Chave de acesso
- Dados do emitente e destinatário
- Tipo de movimento (Entrada/Saída)
- Lista de itens com tributos

### Tributo
Representa um tributo com:
- Tipo (ICMS, IPI, PIS, COFINS, IBS, CBS)
- Base de cálculo
- Alíquota
- Valor
- CST
- Memória de cálculo

### MapaApuracao
Resultado da apuração contendo:
- Período
- Lista de apurações por tributo
- Débitos, créditos e saldo de cada tributo
- Memória de cálculo

## Requisitos

- Python >= 3.8
- lxml >= 4.9.0
- pydantic >= 2.0.0

## Desenvolvimento

Para executar os testes:

```bash
pytest
```

## Licença

Este projeto está sob licença MIT.
=======
# fiscal-auditor

