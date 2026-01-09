# Guia de Configuração do ETL

## Arquivo de Configuração (.env.etl)

O ETL utiliza um arquivo `.env.etl` para configuração. Copie o arquivo de exemplo e ajuste conforme necessário:

```bash
cp .env.etl.example .env.etl
```

## Configurações Disponíveis

### 1. Diretório Padrão

Define o diretório que será monitorado/processado quando nenhum diretório for especificado:

```env
DIRETORIO_PADRAO=C:\SISTEMA\RENSYS\NFC-E Exportadas\02277201000166
```

**Uso:**
```bash
# Processa o diretório padrão configurado
python run_etl.py

# Sobrescreve com diretório específico
python run_etl.py --diretorio "C:\Outro\Diretorio"
```

### 2. Gerenciamento de Arquivos

#### Deletar Após Processamento

Remove os arquivos XML após processamento bem-sucedido:

```env
DELETAR_APOS_PROCESSAR=true
```

- `true`: Arquivos serão **deletados** após processamento
- `false`: Arquivos serão **mantidos** no diretório original

**Sobrescrever via CLI:**
```bash
# Não deletar arquivos mesmo com DELETAR_APOS_PROCESSAR=true
python run_etl.py --no-delete
```

#### Mover para Backup

Alternativa ao deletar - move os arquivos para um diretório de backup:

```env
MOVER_PARA_BACKUP=false
DIRETORIO_BACKUP=C:\Backup\XMLs
```

- Se `MOVER_PARA_BACKUP=true`, os arquivos são **movidos** para o diretório de backup
- Se `DELETAR_APOS_PROCESSAR=true`, tem **prioridade** sobre mover para backup
- Arquivos duplicados com mesmo nome recebem timestamp: `arquivo_20250101_153045.xml`

### 3. Validação de Duplicatas

#### Validação por Chave de Acesso

Verifica se a NF-e já existe no banco pela chave de acesso (44 caracteres):

```env
VALIDAR_POR_CHAVE=true
```

- `true`: Não processa NF-es com chave já existente no banco
- `false`: Desativa validação por chave (pode gerar erros de integridade)

**Recomendação:** Manter sempre `true`

#### Validação por Hash

Verifica se o arquivo XML **exato** já foi processado anteriormente (mesmo conteúdo):

```env
VALIDAR_POR_HASH=true
```

- `true`: Calcula hash SHA256 do arquivo e verifica se já foi processado
- `false`: Não valida por hash do arquivo

**Vantagens:**
- Detecta reprocessamento de arquivos mesmo com nomes diferentes
- Evita processar XMLs duplicados baixados de fontes diferentes
- Hash é armazenado na tabela `arquivos_processados`

**Desvantagens:**
- Pequena sobrecarga de performance no cálculo do hash
- Recomendável quando há risco de receber mesmos XMLs com nomes diferentes

## Comportamento do Sistema

### Arquivo Novo
1. Extração dos dados do XML
2. Transformação para modelo do banco
3. Verificação de duplicatas (hash + chave)
4. Inserção no banco de dados
5. Registro na tabela `arquivos_processados`
6. Deleção ou movimentação do arquivo (conforme configuração)

### Arquivo Duplicado (Hash)
1. Detecta que arquivo já foi processado
2. **Não** tenta inserir no banco
3. Registra log de duplicata
4. Deleta arquivo (se configurado)
5. Retorna resultado "duplicado"

### Arquivo com Chave Duplicada
1. Extrai dados do XML
2. Detecta que chave de acesso já existe no banco
3. **Não** insere no banco
4. Registra na tabela `arquivos_processados` como "duplicado"
5. Deleta arquivo (se configurado)
6. Retorna resultado "duplicado"

### Arquivo com Erro
1. Tenta processar o arquivo
2. Captura exceção
3. Registra na tabela `arquivos_processados` como "erro"
4. **NÃO** deleta o arquivo (mantém para análise)
5. Registra log com detalhes do erro

## Tabela: arquivos_processados

Armazena histórico de todos os arquivos processados:

```sql
CREATE TABLE arquivos_processados (
    id SERIAL PRIMARY KEY,
    caminho_arquivo VARCHAR(500),      -- Caminho original do arquivo
    hash_arquivo VARCHAR(64),           -- Hash SHA256 do conteúdo
    chave_acesso VARCHAR(44),           -- Chave de acesso da NF-e
    status VARCHAR(20),                 -- processado, duplicado, erro
    data_processamento TIMESTAMP,       -- Data/hora do processamento
    deletado BOOLEAN DEFAULT false,     -- Se o arquivo foi deletado
    caminho_backup VARCHAR(500)         -- Caminho do backup (se movido)
);
```

### Consultas Úteis

```sql
-- Arquivos processados hoje
SELECT * FROM arquivos_processados 
WHERE DATE(data_processamento) = CURRENT_DATE;

-- Arquivos duplicados
SELECT * FROM arquivos_processados 
WHERE status = 'duplicado';

-- Arquivos com erro
SELECT * FROM arquivos_processados 
WHERE status = 'erro';

-- Verificar se arquivo específico já foi processado
SELECT * FROM arquivos_processados 
WHERE caminho_arquivo = 'C:\caminho\arquivo.xml';

-- Verificar se hash já foi processado
SELECT * FROM arquivos_processados 
WHERE hash_arquivo = 'a1b2c3d4...';
```

## Exemplos de Uso

### Processamento Diário Automático

```bash
# Processar diretório padrão e deletar arquivos
python run_etl.py

# Agendar no Windows Task Scheduler:
# Comando: C:\caminho\python.exe
# Argumentos: C:\caminho\run_etl.py
# Diretório: C:\caminho\fiscal-auditor
# Gatilho: Diário às 23:00
```

### Processamento com Backup

```env
DELETAR_APOS_PROCESSAR=false
MOVER_PARA_BACKUP=true
DIRETORIO_BACKUP=D:\Backup\XMLs
```

```bash
python run_etl.py
```

### Processamento Manual (Manter Arquivos)

```bash
# Processa mas não deleta (independente da configuração)
python run_etl.py --no-delete
```

### Reprocessar Diretório Específico

```bash
# Processa outro diretório mantendo validação de duplicatas
python run_etl.py --diretorio "C:\XMLs\Antigos"
```

## Troubleshooting

### Problema: "Nenhum diretório especificado"

**Solução 1:** Configure no `.env.etl`:
```env
DIRETORIO_PADRAO=C:\Seu\Diretorio\XMLs
```

**Solução 2:** Especifique na linha de comando:
```bash
python run_etl.py --diretorio "C:\Seu\Diretorio\XMLs"
```

### Problema: Arquivos não estão sendo deletados

**Verificar:**
1. Configuração no `.env.etl`:
   ```env
   DELETAR_APOS_PROCESSAR=true
   ```

2. Não está usando `--no-delete`:
   ```bash
   # Errado
   python run_etl.py --no-delete
   
   # Correto
   python run_etl.py
   ```

3. Permissões de escrita no diretório

### Problema: Muitos arquivos "duplicados"

**Causas possíveis:**
1. Arquivos já foram processados anteriormente (comportamento correto)
2. Mesma chave de acesso em múltiplos arquivos (NF-e já no banco)
3. Mesmo XML salvo com nomes diferentes (hash detecta duplicata)

**Verificar histórico:**
```sql
SELECT caminho_arquivo, chave_acesso, hash_arquivo, status, data_processamento
FROM arquivos_processados
WHERE status = 'duplicado'
ORDER BY data_processamento DESC
LIMIT 20;
```

### Problema: Arquivos com erro não são deletados

**Comportamento esperado:** Arquivos com erro são **mantidos** propositalmente para análise.

**Verificar logs:**
```sql
SELECT caminho_arquivo, status, data_processamento
FROM log_processamento
WHERE status = 'erro'
ORDER BY data_processamento DESC;
```

## Migrações

Se você já tem um sistema funcionando e quer adicionar o arquivo de configuração:

1. Criar arquivo `.env.etl`:
   ```env
   DIRETORIO_PADRAO=C:\Seu\Diretorio
   DELETAR_APOS_PROCESSAR=false
   VALIDAR_POR_CHAVE=true
   VALIDAR_POR_HASH=true
   ```

2. Criar tabela `arquivos_processados`:
   ```sql
   CREATE TABLE arquivos_processados (
       id SERIAL PRIMARY KEY,
       caminho_arquivo VARCHAR(500),
       hash_arquivo VARCHAR(64),
       chave_acesso VARCHAR(44),
       status VARCHAR(20),
       data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       deletado BOOLEAN DEFAULT false,
       caminho_backup VARCHAR(500)
   );
   
   CREATE INDEX idx_arquivo_caminho ON arquivos_processados(caminho_arquivo);
   CREATE INDEX idx_arquivo_hash ON arquivos_processados(hash_arquivo);
   CREATE INDEX idx_arquivo_chave ON arquivos_processados(chave_acesso);
   ```

3. Atualizar sistema gradualmente:
   - Primeiro executar sem deletar: `DELETAR_APOS_PROCESSAR=false`
   - Validar processamento por alguns dias
   - Habilitar deleção: `DELETAR_APOS_PROCESSAR=true`

## Segurança

### Backup Antes de Deletar

**Recomendação:** Sempre faça backup antes de habilitar deleção automática:

```env
# Período de testes
DELETAR_APOS_PROCESSAR=false
MOVER_PARA_BACKUP=true
DIRETORIO_BACKUP=C:\Backup\XMLs
```

Após validar o sistema por algumas semanas:

```env
# Produção
DELETAR_APOS_PROCESSAR=true
MOVER_PARA_BACKUP=false
```

### Recuperação de Arquivos

A tabela `arquivos_processados` mantém registro de todos os arquivos, mesmo após deleção:

```sql
-- Listar arquivos deletados nos últimos 7 dias
SELECT caminho_arquivo, chave_acesso, data_processamento
FROM arquivos_processados
WHERE deletado = true
  AND data_processamento > CURRENT_DATE - INTERVAL '7 days';
```

Se tiver backup, pode recuperar pela chave de acesso.
