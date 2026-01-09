# Serviço ETL - Documentos Fiscais

## 📋 Visão Geral

Este é um serviço ETL (Extract, Transform, Load) completo e independente para processamento de arquivos XML de NF-e e NFC-e. O serviço extrai todos os campos dos documentos fiscais e os armazena em um banco de dados PostgreSQL, criando um datalake estruturado.

## 🎯 Características

- **Extração Completa**: Lê todos os campos disponíveis nos XMLs de NF-e e NFC-e
- **Datalake Estruturado**: Armazena dados em tabelas relacionais normalizadas
- **Processamento em Lote**: Capaz de processar grandes volumes de arquivos
- **Controle de Duplicatas**: Detecta e ignora documentos já processados
- **Logs Detalhados**: Registra todo o histórico de processamento
- **Independente**: Funciona de forma autônoma, separado do sistema principal

## 🏗️ Arquitetura

### Estrutura do Serviço

```
etl_service/
├── __init__.py           # Inicialização do módulo
├── database.py           # Configuração do banco de dados
├── models.py             # Modelos SQLAlchemy (datalake)
├── extractor.py          # Extração de dados dos XMLs
├── transformer.py        # Transformação dos dados
├── loader.py             # Carregamento no banco de dados
└── pipeline.py           # Pipeline completo de ETL
```

### Fluxo de Dados

```
XML Files → Extractor → Transformer → Loader → PostgreSQL
                                                    ↓
                                                Datalake
```

## 📊 Modelo de Dados

O datalake é composto pelas seguintes tabelas principais:

### Tabela: `nfe`
Armazena dados principais da NF-e/NFC-e:
- Identificação (chave, número, série, modelo)
- Emitente (CNPJ, razão social, endereço)
- Destinatário (CNPJ, razão social, endereço)
- Totalizadores (valores, impostos)
- Transporte
- Pagamento
- XML completo

### Tabela: `nfe_item`
Armazena itens das notas fiscais:
- Produtos (código, descrição, NCM, CEST)
- Quantidades e valores
- Impostos detalhados (ICMS, IPI, PIS, COFINS)
- Importação

### Tabela: `nfe_duplicata`
Armazena duplicatas/parcelas:
- Número da duplicata
- Data de vencimento
- Valor

### Tabelas de Controle
- `etl_processamento`: Registros de execuções do ETL
- `etl_log_processamento`: Log detalhado de cada arquivo processado

## 🚀 Instalação

### 1. Instalar Dependências

```bash
pip install sqlalchemy psycopg2-binary lxml
```

### 2. Configurar Banco de Dados

Por padrão, o serviço usa:
```
postgresql://postgres:postgres@localhost:5432/fiscal_datalake
```

Para usar outra configuração, defina a variável de ambiente:
```bash
set ETL_DATABASE_URL=postgresql://usuario:senha@host:porta/banco
```

### 3. Inicializar o Banco

```bash
python run_etl.py --init-db
```

Isso criará todas as tabelas necessárias no banco de dados.

## 💻 Uso

### Linha de Comando

#### Processar um Diretório Completo

```bash
python run_etl.py --diretorio "C:\XMLs\2024"
```

#### Processar sem Recursão (apenas pasta principal)

```bash
python run_etl.py --diretorio "C:\XMLs\2024" --no-recursivo
```

#### Processar Arquivos Específicos

```bash
python run_etl.py --arquivos "nota1.xml" "nota2.xml" "nota3.xml"
```

#### Ver Todas as Opções

```bash
python run_etl.py --help
```

### Uso Programático

```python
from etl_service.pipeline import ETLPipeline, inicializar_banco

# Inicializar banco (primeira vez)
inicializar_banco()

# Criar pipeline
pipeline = ETLPipeline()

# Processar um diretório
stats = pipeline.processar_diretorio(
    diretorio="C:/XMLs/2024",
    tipo_processamento="completo",
    recursivo=True
)

print(f"Processados: {stats['processados']}")
print(f"Erros: {stats['erros']}")
```

### Processar Arquivo Único

```python
from etl_service.pipeline import ETLPipeline

pipeline = ETLPipeline()
resultado = pipeline.processar_arquivo("caminho/para/nota.xml")

if resultado['sucesso']:
    print(f"Sucesso! Chave: {resultado['chave_acesso']}")
else:
    print(f"Erro: {resultado['mensagem']}")
```

## 📈 Monitoramento

### Consultar Processamentos

```sql
-- Ver histórico de processamentos
SELECT 
    id,
    data_processamento,
    tipo_processamento,
    status,
    arquivos_processados,
    arquivos_erro,
    tempo_execucao
FROM etl_processamento
ORDER BY data_processamento DESC;
```

### Consultar Logs Detalhados

```sql
-- Ver log de processamento de arquivos
SELECT 
    data_hora,
    arquivo,
    chave_acesso,
    status,
    mensagem,
    tempo_processamento
FROM etl_log_processamento
WHERE status = 'erro'
ORDER BY data_hora DESC;
```

### Consultar NF-es Processadas

```sql
-- Ver últimas notas processadas
SELECT 
    chave_acesso,
    numero_nota,
    serie,
    data_emissao,
    emitente_razao_social,
    destinatario_razao_social,
    valor_total_nota,
    data_processamento_etl
FROM nfe
ORDER BY data_processamento_etl DESC
LIMIT 100;
```

### Estatísticas

```sql
-- Estatísticas gerais
SELECT 
    COUNT(*) as total_notas,
    SUM(valor_total_nota) as valor_total,
    COUNT(DISTINCT emitente_cnpj) as total_emitentes,
    COUNT(DISTINCT destinatario_cnpj) as total_destinatarios,
    MIN(data_emissao) as data_mais_antiga,
    MAX(data_emissao) as data_mais_recente
FROM nfe;

-- Total por mês
SELECT 
    DATE_TRUNC('month', data_emissao) as mes,
    COUNT(*) as quantidade,
    SUM(valor_total_nota) as valor_total
FROM nfe
GROUP BY DATE_TRUNC('month', data_emissao)
ORDER BY mes DESC;
```

## 🔧 Configurações Avançadas

### Variáveis de Ambiente

- `ETL_DATABASE_URL`: URL de conexão do banco de dados
- Exemplo: `postgresql://user:pass@localhost:5432/datalake`

### Personalização do Extrator

O extrator pode ser estendido para capturar campos adicionais:

```python
from etl_service.extractor import XMLExtractor

class CustomExtractor(XMLExtractor):
    def extrair_nfe(self, caminho_arquivo):
        dados = super().extrair_nfe(caminho_arquivo)
        # Adicionar extrações customizadas
        dados['campo_custom'] = self._extrair_campo_custom(root)
        return dados
```

## 🐛 Troubleshooting

### Erro de Conexão com Banco

```
Erro: could not connect to server
```
**Solução**: Verifique se o PostgreSQL está rodando e as credenciais estão corretas.

### Erro ao Processar XML

```
Erro ao extrair dados do XML
```
**Solução**: Verifique se o arquivo é um XML válido de NF-e. Use um validador XML.

### Duplicatas não Detectadas

```
IntegrityError: duplicate key value
```
**Solução**: A chave de acesso já existe. O sistema normalmente detecta isso, mas se ocorrer o erro, verifique a constraint no banco.

## 📝 Exemplos de Consultas Úteis

### Buscar por CNPJ

```sql
-- Buscar todas as notas de um emitente
SELECT * FROM nfe WHERE emitente_cnpj = '12345678000190';

-- Buscar todas as compras de um destinatário
SELECT * FROM nfe WHERE destinatario_cnpj = '12345678000190';
```

### Análise de Produtos

```sql
-- Produtos mais vendidos
SELECT 
    descricao,
    COUNT(*) as quantidade_vendas,
    SUM(valor_total_bruto) as valor_total
FROM nfe_item
GROUP BY descricao
ORDER BY quantidade_vendas DESC
LIMIT 20;
```

### Análise de Impostos

```sql
-- Total de impostos por tipo
SELECT 
    SUM(valor_icms) as total_icms,
    SUM(valor_ipi) as total_ipi,
    SUM(valor_pis) as total_pis,
    SUM(valor_cofins) as total_cofins
FROM nfe;
```

## 🔄 Integração com Sistema Principal

O serviço ETL é independente mas pode ser integrado:

```python
# No sistema principal
from etl_service.pipeline import ETLPipeline

def importar_xmls(diretorio):
    pipeline = ETLPipeline()
    return pipeline.processar_diretorio(diretorio)
```

## 📊 Performance

- **Velocidade**: ~2-5 arquivos/segundo (depende da complexidade)
- **Memória**: ~50-100MB para processamento normal
- **Lotes**: Commits a cada 100 registros por padrão

## 🛡️ Segurança

- Todas as transações são atômicas
- Logs de auditoria completos
- XML original preservado para conferência
- Detecção automática de duplicatas

## 🤝 Contribuindo

Para adicionar novos campos ao datalake:

1. Atualizar `models.py` com novos campos
2. Atualizar `extractor.py` para extrair os campos
3. Atualizar `transformer.py` para transformar os dados
4. Executar migração do banco

## 📄 Licença

Este serviço faz parte do sistema Fiscal Auditor.

## 📞 Suporte

Para dúvidas ou problemas:
- Consulte a documentação completa
- Verifique os logs de processamento
- Revise as mensagens de erro detalhadas

---

**Versão**: 1.0.0
**Última Atualização**: Janeiro 2026
