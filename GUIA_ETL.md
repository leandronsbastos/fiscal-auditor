# Guia Rápido - Serviço ETL

## 🚀 Início Rápido

### 1. Instalar Dependências
```bash
pip install sqlalchemy psycopg2-binary lxml
```

### 2. Configurar Banco de Dados
Crie o banco PostgreSQL:
```sql
CREATE DATABASE fiscal_datalake;
```

Ou configure a variável de ambiente:
```bash
set ETL_DATABASE_URL=postgresql://usuario:senha@host:porta/banco
```

### 3. Executar Setup
```bash
python setup_etl.py
```

### 4. Inicializar Banco
```bash
python run_etl.py --init-db
```

### 5. Processar XMLs
```bash
python run_etl.py --diretorio "C:\XMLs"
```

## 📁 Estrutura Criada

```
fiscal-auditor/
├── etl_service/              # Serviço ETL
│   ├── __init__.py           # Inicialização
│   ├── database.py           # Configuração do banco
│   ├── models.py             # Modelos do datalake
│   ├── extractor.py          # Extração de XMLs
│   ├── transformer.py        # Transformação de dados
│   ├── loader.py             # Carregamento no banco
│   ├── pipeline.py           # Pipeline completo
│   ├── requirements.txt      # Dependências
│   ├── README.md             # Documentação completa
│   └── consultas_uteis.sql   # Consultas SQL úteis
├── run_etl.py                # Script principal
├── setup_etl.py              # Configuração inicial
└── exemplo_etl.py            # Exemplos de uso
```

## 🎯 Funcionalidades

### ✅ Extração Completa
- Todos os campos da NF-e e NFC-e
- Identificação, Emitente, Destinatário
- Itens e Impostos detalhados
- Transporte, Pagamento, Cobrança
- XML completo preservado

### ✅ Datalake Estruturado
- Tabelas relacionais normalizadas
- Índices otimizados
- Suporte a consultas complexas
- Histórico completo de processamento

### ✅ Recursos Avançados
- Detecção de duplicatas
- Processamento em lote
- Logs detalhados
- Controle de erros
- Estatísticas de processamento

## 📊 Tabelas do Datalake

### `nfe`
Dados principais das notas fiscais (91 campos)

### `nfe_item`
Itens das notas (67 campos por item)

### `nfe_duplicata`
Duplicatas/Parcelas de pagamento

### `etl_processamento`
Histórico de execuções do ETL

### `etl_log_processamento`
Log detalhado de cada arquivo

## 💡 Exemplos de Uso

### Processar Diretório
```bash
python run_etl.py --diretorio "C:\XMLs\2024"
```

### Processar Arquivos Específicos
```bash
python run_etl.py --arquivos "nota1.xml" "nota2.xml"
```

### Sem Recursão
```bash
python run_etl.py --diretorio "C:\XMLs" --no-recursivo
```

### Ver Opções
```bash
python run_etl.py --help
```

## 🔍 Consultas Úteis

### Total de Notas
```sql
SELECT COUNT(*) FROM nfe;
```

### Últimas Notas
```sql
SELECT numero_nota, serie, emitente_razao_social, valor_total_nota
FROM nfe
ORDER BY data_processamento_etl DESC
LIMIT 10;
```

### Buscar por CNPJ
```sql
SELECT * FROM nfe WHERE emitente_cnpj = '12345678000190';
```

### Produtos Mais Vendidos
```sql
SELECT descricao, COUNT(*) as vendas, SUM(valor_total_bruto) as valor
FROM nfe_item
GROUP BY descricao
ORDER BY vendas DESC
LIMIT 20;
```

Mais consultas em: `etl_service/consultas_uteis.sql`

## 📈 Monitoramento

### Status do ETL
```sql
SELECT * FROM etl_processamento ORDER BY data_processamento DESC;
```

### Arquivos com Erro
```sql
SELECT * FROM etl_log_processamento WHERE status = 'erro';
```

### Estatísticas
```sql
SELECT 
    COUNT(*) as total_notas,
    SUM(valor_total_nota) as valor_total
FROM nfe;
```

## 🔧 Configuração

### Variável de Ambiente
```bash
set ETL_DATABASE_URL=postgresql://usuario:senha@localhost:5432/fiscal_datalake
```

### Banco Padrão
```
postgresql://postgres:postgres@localhost:5432/fiscal_datalake
```

## 📚 Documentação

- **Documentação Completa**: `etl_service/README.md`
- **Exemplos de Código**: `exemplo_etl.py`
- **Consultas SQL**: `etl_service/consultas_uteis.sql`

## ⚙️ Requisitos

- Python 3.8+
- PostgreSQL 12+
- SQLAlchemy 2.0+
- psycopg2-binary
- lxml

## 🆘 Suporte

### Erro de Conexão
Verifique se PostgreSQL está rodando e credenciais estão corretas.

### Erro ao Processar XML
Verifique se o arquivo é um XML válido de NF-e.

### Duplicatas
O sistema automaticamente ignora notas já processadas.

## 🎓 Características Técnicas

- **Arquitetura**: ETL (Extract, Transform, Load)
- **Padrão**: Pipeline modular e extensível
- **Banco**: PostgreSQL com SQLAlchemy ORM
- **Parser XML**: lxml com suporte a namespaces
- **Transações**: Atômicas com rollback automático
- **Performance**: Processamento em lote otimizado
- **Logs**: Detalhados com timestamps e métricas
- **Segurança**: SQL Injection protegido pelo ORM

## 📦 Campos Armazenados

### NF-e Principal
- Identificação (chave, número, série, modelo, tipo)
- Emitente (dados completos + endereço)
- Destinatário (dados completos + endereço)
- Totalizadores (valores e impostos)
- Transporte (transportadora, veículo, volumes)
- Pagamento (formas e valores)
- Cobrança (fatura e duplicatas)
- XML completo

### Itens
- Produto (código, descrição, NCM, CEST, CFOP)
- Quantidades e valores
- ICMS (completo + ST + FCP)
- IPI (completo)
- PIS/COFINS (completo)
- Importação (DI completa)

---

**Versão**: 1.0.0  
**Data**: Janeiro 2026
