# 🚀 Sistema de Gerenciamento Automático de Arquivos - ETL

## ✨ Novas Funcionalidades

O ETL agora possui um sistema completo de gerenciamento automático de arquivos com:

✅ **Configuração de Diretório Padrão** - Execute sem argumentos usando diretório configurado  
✅ **Deleção Automática** - Remove XMLs após processamento bem-sucedido  
✅ **Validação de Duplicatas** - Detecta arquivos já processados (hash + chave)  
✅ **Histórico Completo** - Rastreia todos os arquivos processados  
✅ **Backup Opcional** - Mova arquivos para backup em vez de deletar  
✅ **Proteção de Erros** - Arquivos com erro são mantidos para análise  

---

## 📋 Início Rápido

### 1. Configuração Inicial

Copie o arquivo de exemplo e edite:

```bash
cp .env.etl.example .env.etl
```

Edite `.env.etl`:

```env
# Seu diretório com XMLs
DIRETORIO_PADRAO=C:\SISTEMA\RENSYS\NFC-E Exportadas\02277201000166

# Deletar após processar? (true/false)
DELETAR_APOS_PROCESSAR=true

# Validações (recomendado: ambos true)
VALIDAR_POR_CHAVE=true
VALIDAR_POR_HASH=true
```

### 2. Criar Tabela de Controle

Execute a migração SQL:

```bash
psql -U postgres -d fiscal_datalake -f etl_service/migrations/001_criar_tabela_arquivos_processados.sql
```

### 3. Executar ETL

```bash
# Processar diretório padrão
python run_etl.py

# Processar outro diretório
python run_etl.py --diretorio "C:\Outro\Diretorio"

# Processar sem deletar (manter arquivos)
python run_etl.py --no-delete
```

---

## 🎯 Casos de Uso

### Processamento Automático Diário

**Cenário:** Processar XMLs que chegam diariamente e deletar após importação

```env
# .env.etl
DIRETORIO_PADRAO=C:\Sistema\XMLs\Entrada
DELETAR_APOS_PROCESSAR=true
VALIDAR_POR_CHAVE=true
VALIDAR_POR_HASH=true
```

```bash
# Agendar no Windows Task Scheduler (diário às 23:00)
python run_etl.py
```

**Resultado:**
- Processa todos os XMLs do diretório
- Valida duplicatas (não reprocessa)
- Deleta arquivos processados
- Mantém arquivos com erro para análise

### Processamento com Backup

**Cenário:** Mover arquivos para backup em vez de deletar

```env
DIRETORIO_PADRAO=C:\Sistema\XMLs\Entrada
DELETAR_APOS_PROCESSAR=false
MOVER_PARA_BACKUP=true
DIRETORIO_BACKUP=D:\Backup\XMLs
```

```bash
python run_etl.py
```

**Resultado:**
- Processa XMLs
- Move para D:\Backup\XMLs
- Mantém arquivos originais em backup

### Processamento de Múltiplas Fontes

**Cenário:** Processar XMLs de diferentes fontes (evitar duplicatas)

```env
VALIDAR_POR_HASH=true
VALIDAR_POR_CHAVE=true
```

```bash
# Fonte 1
python run_etl.py --diretorio "C:\Fonte1\XMLs"

# Fonte 2 (mesmo XML pode vir com nome diferente)
python run_etl.py --diretorio "C:\Fonte2\XMLs"
```

**Resultado:**
- Detecta se mesmo XML já foi processado (por hash)
- Não duplica NF-es no banco (por chave)
- Evita reprocessamento desnecessário

### Reprocessamento Seguro

**Cenário:** Reprocessar diretório sem deletar arquivos

```bash
python run_etl.py --diretorio "C:\XMLs\Revisar" --no-delete
```

**Resultado:**
- Processa novos XMLs
- Ignora XMLs já processados
- **Não** deleta nenhum arquivo

---

## 🗂️ Tabela: arquivos_processados

Rastreia histórico de todos os arquivos:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | SERIAL | ID único |
| caminho_arquivo | VARCHAR(500) | Caminho original do XML |
| hash_arquivo | VARCHAR(64) | Hash SHA256 do conteúdo |
| chave_acesso | VARCHAR(44) | Chave de acesso da NF-e |
| status | VARCHAR(20) | processado, duplicado, erro |
| data_processamento | TIMESTAMP | Data/hora do processamento |
| deletado | BOOLEAN | Se o arquivo foi deletado |
| caminho_backup | VARCHAR(500) | Caminho no backup (se movido) |

### Consultas Úteis

```sql
-- Arquivos processados hoje
SELECT caminho_arquivo, chave_acesso, status, data_processamento
FROM arquivos_processados
WHERE DATE(data_processamento) = CURRENT_DATE;

-- Arquivos deletados
SELECT COUNT(*) as total_deletados
FROM arquivos_processados
WHERE deletado = true;

-- Arquivos com erro (para análise)
SELECT caminho_arquivo, chave_acesso, data_processamento
FROM arquivos_processados
WHERE status = 'erro'
ORDER BY data_processamento DESC;

-- Verificar se arquivo específico já foi processado
SELECT * FROM arquivos_processados
WHERE caminho_arquivo = 'C:\caminho\arquivo.xml';

-- Detectar XMLs duplicados (mesmo hash)
SELECT hash_arquivo, COUNT(*) as quantidade
FROM arquivos_processados
WHERE hash_arquivo IS NOT NULL
GROUP BY hash_arquivo
HAVING COUNT(*) > 1;
```

---

## 🔧 Configurações Detalhadas

### DIRETORIO_PADRAO

Define diretório padrão quando comando executado sem argumentos.

```env
DIRETORIO_PADRAO=C:\Sistema\XMLs
```

```bash
# Usa DIRETORIO_PADRAO
python run_etl.py

# Sobrescreve com outro diretório
python run_etl.py --diretorio "C:\Outro"
```

### DELETAR_APOS_PROCESSAR

Remove arquivos após processamento bem-sucedido.

```env
DELETAR_APOS_PROCESSAR=true
```

- ✅ `true`: Deleta XMLs processados com sucesso
- ❌ `false`: Mantém arquivos originais

**Sobrescrever via CLI:**
```bash
python run_etl.py --no-delete
```

**Importante:**
- Arquivos duplicados também são deletados (já estão no banco)
- Arquivos com **erro** são sempre **mantidos** para análise

### MOVER_PARA_BACKUP

Alternativa ao deletar - move arquivos para backup.

```env
MOVER_PARA_BACKUP=true
DIRETORIO_BACKUP=D:\Backup\XMLs
```

**Prioridade:**
1. `DELETAR_APOS_PROCESSAR=true` → deleta (ignora backup)
2. `MOVER_PARA_BACKUP=true` → move para backup
3. Ambos `false` → mantém arquivos originais

### VALIDAR_POR_CHAVE

Verifica se NF-e já existe no banco pela chave de acesso (44 caracteres).

```env
VALIDAR_POR_CHAVE=true
```

- ✅ `true`: Não reprocessa NF-es já no banco (recomendado)
- ⚠️ `false`: Pode causar erros de integridade (chave duplicada)

### VALIDAR_POR_HASH

Verifica se arquivo XML exato já foi processado.

```env
VALIDAR_POR_HASH=true
```

- ✅ `true`: Detecta reprocessamento de mesmo arquivo
- ❌ `false`: Permite reprocessar mesmo XML

**Quando usar:**
- Múltiplas fontes podem ter mesmo XML com nomes diferentes
- Evitar reprocessamento após mover/renomear arquivos
- Detectar duplicatas de downloads

**Overhead:**
- Pequeno custo de performance (cálculo SHA256)
- Recomendado na maioria dos casos

---

## 📊 Fluxo de Processamento

### Arquivo Novo ✨

```
1. Extração → Leitura do XML
2. Transformação → Conversão para modelo do banco
3. Validação Hash → Arquivo já foi processado?
   ❌ Não → Continua
4. Validação Chave → NF-e já existe no banco?
   ❌ Não → Continua
5. Inserção → Grava no banco de dados
6. Registro → Salva em arquivos_processados
7. Gerenciamento → Deleta ou move arquivo
✅ Sucesso
```

### Arquivo Duplicado (Hash) ⚠️

```
1. Extração → Leitura do XML
2. Cálculo Hash → SHA256 do conteúdo
3. Validação → Hash já existe em arquivos_processados?
   ✅ Sim → Duplicado detectado
4. Registro → Atualiza log como "duplicado"
5. Gerenciamento → Deleta arquivo duplicado
⚠️ Duplicado (não insere no banco)
```

### Arquivo com Chave Duplicada 🔄

```
1. Extração → Leitura do XML
2. Transformação → Conversão para modelo
3. Validação Hash → Arquivo é novo (hash diferente)
4. Validação Chave → Chave já existe no banco
   ✅ Sim → NF-e já cadastrada
5. Registro → Salva em arquivos_processados como "duplicado"
6. Gerenciamento → Deleta arquivo
🔄 Duplicado (não insere no banco)
```

### Arquivo com Erro ❌

```
1. Extração → Erro ao ler XML
2. Captura Exceção → Registra erro
3. Registro → Salva em arquivos_processados como "erro"
4. Log → Grava detalhes em log_processamento
5. Preservação → Arquivo NÃO é deletado
❌ Erro (arquivo mantido para análise)
```

---

## 🛡️ Segurança e Boas Práticas

### Período de Testes

**Recomendação:** Comece sem deletar arquivos

```env
# Fase 1: Teste (1-2 semanas)
DELETAR_APOS_PROCESSAR=false
MOVER_PARA_BACKUP=true
DIRETORIO_BACKUP=D:\Backup\XMLs
```

Valide:
- ✅ Todos os XMLs sendo processados corretamente
- ✅ Duplicatas sendo detectadas
- ✅ Dados corretos no banco

```env
# Fase 2: Produção
DELETAR_APOS_PROCESSAR=true
MOVER_PARA_BACKUP=false
```

### Backup Periódico

Mesmo com deleção automática, faça backup do banco:

```bash
# Backup diário do banco
pg_dump -U postgres fiscal_datalake > backup_$(date +%Y%m%d).sql
```

### Monitoramento

Crie alertas para arquivos com erro:

```sql
-- Arquivos com erro nas últimas 24h
SELECT COUNT(*) as total_erros
FROM arquivos_processados
WHERE status = 'erro'
  AND data_processamento > NOW() - INTERVAL '24 hours';
```

Se `total_erros > 0`, investigar manualmente.

### Recuperação

A tabela `arquivos_processados` mantém registro permanente:

```sql
-- Listar arquivos deletados dos últimos 30 dias
SELECT caminho_arquivo, chave_acesso, hash_arquivo, data_processamento
FROM arquivos_processados
WHERE deletado = true
  AND data_processamento > CURRENT_DATE - INTERVAL '30 days'
ORDER BY data_processamento DESC;
```

Se precisar recuperar:
1. Usar chave de acesso para buscar no sistema fiscal
2. Consultar backup (se configurado)
3. Exportar dados do banco para gerar novo XML

---

## 🐛 Troubleshooting

### "Nenhum diretório especificado"

**Causa:** Arquivo `.env.etl` não configurado e comando sem argumentos

**Solução 1:** Configurar `.env.etl`
```env
DIRETORIO_PADRAO=C:\Seu\Diretorio
```

**Solução 2:** Passar diretório na linha de comando
```bash
python run_etl.py --diretorio "C:\Seu\Diretorio"
```

### Arquivos não estão sendo deletados

**Verificar:**

1. Configuração no `.env.etl`:
   ```env
   DELETAR_APOS_PROCESSAR=true
   ```

2. Comando não usa `--no-delete`:
   ```bash
   # ❌ Errado (não deleta)
   python run_etl.py --no-delete
   
   # ✅ Correto (deleta)
   python run_etl.py
   ```

3. Permissões de escrita no diretório:
   ```bash
   # Windows: verificar permissões na pasta
   ```

4. Arquivos com status "erro" não são deletados (comportamento esperado)

### Muitos arquivos "duplicados"

**Causas:**

1. ✅ **Comportamento correto:** Arquivos já foram processados anteriormente
2. ⚠️ **Múltiplos XMLs mesma NF-e:** Chave de acesso duplicada
3. 🔄 **Mesmo XML, nomes diferentes:** Hash detecta duplicata

**Análise:**

```sql
SELECT 
    status,
    COUNT(*) as quantidade,
    COUNT(DISTINCT chave_acesso) as nfes_unicas,
    COUNT(DISTINCT hash_arquivo) as arquivos_unicos
FROM arquivos_processados
GROUP BY status;
```

### "Erro ao calcular hash do arquivo"

**Causa:** Arquivo bloqueado ou permissões insuficientes

**Solução:**
1. Verificar se arquivo está aberto em outro programa
2. Verificar permissões de leitura
3. Verificar antivírus bloqueando acesso

### Arquivo processado mas não deletado

**Verificar logs:**

```sql
SELECT * FROM arquivos_processados
WHERE caminho_arquivo LIKE '%nome_arquivo%'
ORDER BY data_processamento DESC;
```

**Status possíveis:**
- `processado` + `deletado=false` → Erro na deleção (verificar logs)
- `erro` + `deletado=false` → Arquivo com erro (mantido propositalmente)
- `duplicado` + `deletado=true` → Arquivo duplicado foi deletado

---

## 📚 Documentação Adicional

- [CONFIGURACAO.md](CONFIGURACAO.md) - Guia detalhado de configuração
- [GUIA_ETL.md](GUIA_ETL.md) - Guia de uso do ETL
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Solução de problemas

---

## 🎉 Resumo

O sistema agora possui gerenciamento automático completo:

✅ Configuração flexível via `.env.etl`  
✅ Deleção automática após processamento  
✅ Validação dupla (hash + chave) para evitar reprocessamento  
✅ Histórico completo de arquivos processados  
✅ Proteção: arquivos com erro são preservados  
✅ Backup opcional em vez de deleção  
✅ CLI intuitivo com sobrescrita de configurações  

**Execute agora:**

```bash
# Configure uma vez
cp .env.etl.example .env.etl
nano .env.etl  # Edite com seu diretório

# Execute sempre que quiser
python run_etl.py
```

🚀 Pronto! Seus XMLs serão processados e gerenciados automaticamente!
