# Troubleshooting - Serviço ETL

## ❌ Problema: Não Está Gravando no Banco de Dados

### ✅ Correções Aplicadas:

#### 1. **Commit Faltando no Loader**
**Problema**: O método `carregar_nfe` não estava fazendo commit após adicionar a NF-e ao banco.

**Solução**: Adicionado `session.flush()` e `session.commit()` explícito após adicionar a NF-e.

#### 2. **Parse de DateTime com Timezone**
**Problema**: O método `_parse_datetime` estava falhando ao remover timezone dos XMLs.

**Solução**: Implementado regex para remover corretamente timezone no formato `+HH:MM` ou `-HH:MM`.

#### 3. **Campo valor_total_item Faltando**
**Problema**: O transformer não estava mapeando o campo `valor_total_item` do produto.

**Solução**: Adicionado mapeamento correto de `valor_total` para `valor_total_item`.

### 🔍 Como Testar:

#### 1. Usar Script de Teste:
```bash
python testar_etl.py
```

Este script vai:
- Verificar conexão com banco
- Mostrar NF-es já gravadas
- Permitir teste de gravação de um arquivo
- Confirmar se a gravação funcionou

#### 2. Processar um Arquivo:
```bash
python run_etl.py --arquivos "caminho/arquivo.xml"
```

#### 3. Verificar no Banco:
```sql
-- Ver total de registros
SELECT COUNT(*) FROM nfe;

-- Ver últimas notas
SELECT 
    chave_acesso,
    numero_nota,
    serie,
    data_emissao,
    valor_total_nota,
    data_processamento_etl
FROM nfe
ORDER BY data_processamento_etl DESC
LIMIT 10;
```

### 🐛 Problemas Comuns:

#### Problema 1: Erro de Conexão
```
could not connect to server
```

**Solução**:
1. Verifique se PostgreSQL está rodando
2. Teste a conexão:
```bash
psql -h localhost -U postgres -d fiscal_datalake
```
3. Verifique a variável `ETL_DATABASE_URL`

#### Problema 2: Banco Não Existe
```
database "fiscal_datalake" does not exist
```

**Solução**:
```sql
CREATE DATABASE fiscal_datalake;
```

Depois:
```bash
python run_etl.py --init-db
```

#### Problema 3: XML Inválido
```
Arquivo não é uma NF-e válida
```

**Solução**:
1. Verifique se o arquivo é realmente um XML de NF-e
2. Valide o XML:
```bash
python -c "from lxml import etree; etree.parse('arquivo.xml')"
```

#### Problema 3.1: Caminho é um Diretório
```
O caminho informado é um DIRETÓRIO, não um arquivo
```

**Solução**: Você precisa informar o caminho completo do arquivo XML, não apenas o diretório.

**Errado**:
```
C:\XMLs\NFC-E Exportadas\02277201000166\30_12_2025
```

**Correto**:
```
C:\XMLs\NFC-E Exportadas\02277201000166\30_12_2025\35240112345678000165650010000123451234567890-nfe.xml
```

**Dica**: Para processar todos os XMLs de um diretório:
```bash
python run_etl.py --diretorio "C:\XMLs\NFC-E Exportadas\02277201000166\30_12_2025"
```

#### Problema 4: Erro ao Processar Data
```
Error processing datetime
```

**Solução**: Já corrigido na versão atual. O parser de datetime agora trata corretamente:
- `2024-01-01T10:00:00-03:00`
- `2024-01-01T10:00:00+00:00`
- `2024-01-01`

#### Problema 5: Chave Duplicada
```
IntegrityError: duplicate key value
```

**Solução**: Normal! O sistema detecta duplicatas automaticamente e as ignora. A mensagem será:
```
⚠ Duplicado - Chave: 35240...
```

#### Problema 6: Objeto Desvinculado da Sessão
```
Instance <NFe> is not bound to a Session
```

**Causa**: Tentou acessar atributos de um objeto SQLAlchemy depois que a sessão foi fechada.

**Solução**: Sempre salve os valores necessários antes de fechar a sessão:
```python
# ERRADO - Objeto pode ser desvinculado
nfe = transformer.transformar_nfe(dados)
loader.carregar_nfe(nfe, arquivo)
print(nfe.chave_acesso)  # ❌ Erro!

# CORRETO - Salvar valor antes
nfe = transformer.transformar_nfe(dados)
chave = nfe.chave_acesso  # ✅ Salvar antes de gravar
loader.carregar_nfe(nfe, arquivo)
print(chave)  # ✅ OK
```

### 📊 Logs e Debug:

#### Ver Logs do ETL:
```sql
-- Últimos processamentos
SELECT * FROM etl_processamento 
ORDER BY data_processamento DESC 
LIMIT 5;

-- Arquivos com erro
SELECT * FROM etl_log_processamento 
WHERE status = 'erro' 
ORDER BY data_hora DESC;

-- Estatísticas
SELECT 
    status,
    COUNT(*) as quantidade,
    AVG(tempo_processamento) as tempo_medio
FROM etl_log_processamento
GROUP BY status;
```

#### Modo Debug (Python):
```python
from etl_service.pipeline import ETLPipeline

pipeline = ETLPipeline()
resultado = pipeline.processar_arquivo("arquivo.xml")

print(f"Sucesso: {resultado['sucesso']}")
print(f"Mensagem: {resultado['mensagem']}")
print(f"Chave: {resultado['chave_acesso']}")
```

### ✅ Checklist de Verificação:

- [ ] PostgreSQL está rodando?
- [ ] Banco `fiscal_datalake` existe?
- [ ] Tabelas foram criadas? (`python run_etl.py --init-db`)
- [ ] Arquivo XML é válido?
- [ ] Credenciais do banco estão corretas?
- [ ] Há espaço em disco?
- [ ] Permissões do usuário do banco estão OK?

### 🔧 Comandos Úteis:

#### Limpar Banco (CUIDADO!):
```sql
TRUNCATE TABLE nfe_item CASCADE;
TRUNCATE TABLE nfe_duplicata CASCADE;
TRUNCATE TABLE nfe CASCADE;
TRUNCATE TABLE etl_log_processamento CASCADE;
TRUNCATE TABLE etl_processamento CASCADE;
```

#### Verificar Estrutura:
```sql
-- Listar tabelas
\dt

-- Descrever tabela
\d nfe

-- Ver índices
\di
```

#### Recriar Banco:
```bash
# No PostgreSQL
DROP DATABASE fiscal_datalake;
CREATE DATABASE fiscal_datalake;

# No terminal
python run_etl.py --init-db
```

### 📞 Suporte Adicional:

Se o problema persistir:

1. **Ative modo verbose** no Python para ver detalhes:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Capture o erro completo**:
```bash
python run_etl.py --arquivos "arquivo.xml" 2>&1 | tee erro.log
```

3. **Teste componente por componente**:
```python
# Testar extrator
from etl_service.extractor import XMLExtractor
extractor = XMLExtractor()
dados = extractor.extrair_nfe("arquivo.xml")
print(dados['identificacao'])

# Testar transformer
from etl_service.transformer import DataTransformer
transformer = DataTransformer()
nfe = transformer.transformar_nfe(dados)
print(f"NF-e: {nfe.numero_nota}")

# Testar loader
from etl_service.loader import DataLoader
loader = DataLoader()
resultado = loader.carregar_nfe(nfe, "arquivo.xml")
print(resultado)
```

---

**Última Atualização**: 09/01/2026 - Correções aplicadas para garantir gravação no banco
