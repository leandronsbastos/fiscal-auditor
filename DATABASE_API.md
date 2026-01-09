# API de Banco de Dados - Fiscal Auditor

## Configuração

### 1. Instalar PostgreSQL
Baixe e instale o PostgreSQL: https://www.postgresql.org/download/

### 2. Criar Banco de Dados
```sql
CREATE DATABASE fiscal_auditor;
```

### 3. Configurar Variável de Ambiente
Configure a variável `DATABASE_URL` com a string de conexão:

**Windows PowerShell:**
```powershell
$env:DATABASE_URL = "postgresql://postgres:suasenha@localhost:5432/fiscal_auditor"
```

**Linux/Mac:**
```bash
export DATABASE_URL="postgresql://postgres:suasenha@localhost:5432/fiscal_auditor"
```

### 4. Inicializar Banco de Dados
```bash
python init_db.py
```

## Endpoints da API

### Usuários

#### POST /api/usuarios
Cria um novo usuário.
```json
{
  "nome": "João Silva",
  "email": "joao@empresa.com",
  "senha": "senha123"
}
```

#### GET /api/usuarios
Lista todos os usuários.

#### GET /api/usuarios/{usuario_id}
Obtém um usuário específico.

#### PUT /api/usuarios/{usuario_id}
Atualiza dados do usuário.
```json
{
  "nome": "João Silva Santos",
  "email": "joao.silva@empresa.com",
  "ativo": true
}
```

#### DELETE /api/usuarios/{usuario_id}
Deleta um usuário.

---

### Empresas

#### POST /api/empresas
Cria uma nova empresa.
```json
{
  "cnpj": "12345678000190",
  "razao_social": "Empresa Exemplo LTDA",
  "nome_fantasia": "Empresa Exemplo",
  "inscricao_estadual": "123456789",
  "endereco": "Rua Exemplo, 123",
  "cidade": "São Paulo",
  "estado": "SP",
  "cep": "01234-567",
  "telefone": "(11) 1234-5678",
  "email": "contato@empresa.com"
}
```

#### GET /api/empresas
Lista todas as empresas.

#### GET /api/empresas/{empresa_id}
Obtém uma empresa específica.

#### PUT /api/empresas/{empresa_id}
Atualiza dados da empresa.
```json
{
  "razao_social": "Empresa Exemplo LTDA ME",
  "telefone": "(11) 9999-8888"
}
```

#### DELETE /api/empresas/{empresa_id}
Deleta uma empresa.

---

### Vínculos (Usuário ↔ Empresa)

#### POST /api/vinculos
Vincula um usuário a uma empresa.
```json
{
  "usuario_id": 1,
  "empresa_id": 1
}
```

#### DELETE /api/vinculos/{usuario_id}/{empresa_id}
Remove vínculo entre usuário e empresa.

#### GET /api/usuarios/{usuario_id}/empresas
Lista todas as empresas vinculadas a um usuário.

#### GET /api/empresas/{empresa_id}/usuarios
Lista todos os usuários vinculados a uma empresa.

---

### Análises

#### GET /api/empresas/{empresa_id}/analises
Lista todas as análises de uma empresa.

#### GET /api/analises/{analise_id}
Obtém detalhes completos de uma análise específica.

#### DELETE /api/analises/{analise_id}
Deleta uma análise.

---

## Exemplos de Uso com cURL

### Criar Usuário
```bash
curl -X POST "http://localhost:8000/api/usuarios" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "email": "joao@empresa.com",
    "senha": "senha123"
  }'
```

### Criar Empresa
```bash
curl -X POST "http://localhost:8000/api/empresas" \
  -H "Content-Type: application/json" \
  -d '{
    "cnpj": "12345678000190",
    "razao_social": "Empresa Exemplo LTDA",
    "nome_fantasia": "Empresa Exemplo"
  }'
```

### Vincular Usuário à Empresa
```bash
curl -X POST "http://localhost:8000/api/vinculos" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": 1,
    "empresa_id": 1
  }'
```

### Listar Empresas do Usuário
```bash
curl "http://localhost:8000/api/usuarios/1/empresas"
```

### Listar Análises da Empresa
```bash
curl "http://localhost:8000/api/empresas/1/analises"
```

---

## Documentação Interativa

Após iniciar o servidor, acesse:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

A documentação interativa permite testar todos os endpoints diretamente no navegador.

---

## Estrutura do Banco de Dados

### Tabela: usuarios
- id (PK)
- nome
- email (único)
- senha_hash
- ativo
- data_criacao
- data_atualizacao

### Tabela: empresas
- id (PK)
- cnpj (único)
- razao_social
- nome_fantasia
- inscricao_estadual
- inscricao_municipal
- endereco
- cidade
- estado
- cep
- telefone
- email
- ativo
- data_criacao
- data_atualizacao

### Tabela: usuario_empresa (relacionamento N:N)
- usuario_id (FK)
- empresa_id (FK)
- data_vinculo

### Tabela: analises
- id (PK)
- empresa_id (FK)
- periodo
- data_processamento
- total_documentos
- total_entradas
- total_saidas
- icms_debito, icms_credito, icms_saldo
- ipi_debito, ipi_credito, ipi_saldo
- pis_debito, pis_credito, pis_saldo
- cofins_debito, cofins_credito, cofins_saldo
- ibs_debito, ibs_credito, ibs_saldo
- cbs_debito, cbs_credito, cbs_saldo
- relatorio_completo (JSON)

### Tabela: documentos_fiscais
- id (PK)
- analise_id (FK)
- chave
- numero
- serie
- tipo_documento
- tipo_movimento
- data_emissao
- cnpj_emitente
- cnpj_destinatario
- valor_total

---

## Fluxo de Trabalho

1. **Criar Usuário:** POST /api/usuarios
2. **Criar Empresa:** POST /api/empresas
3. **Vincular Usuário à Empresa:** POST /api/vinculos
4. **Fazer Upload de XMLs:** A interface web já salva automaticamente as análises
5. **Consultar Análises:** GET /api/empresas/{empresa_id}/analises
6. **Ver Detalhes da Análise:** GET /api/analises/{analise_id}

---

## Segurança

⚠️ **Nota:** Esta versão inicial não implementa autenticação JWT. Para produção, é recomendado:

1. Adicionar endpoints de login/logout
2. Implementar middleware de autenticação
3. Proteger endpoints sensíveis com tokens JWT
4. Adicionar permissões por nível de usuário
5. Implementar rate limiting
6. Usar HTTPS em produção

---

## Próximas Melhorias

- [ ] Sistema de autenticação JWT
- [ ] Permissões e roles de usuário
- [ ] Integração automática: salvar análises no upload
- [ ] Filtros avançados de consulta
- [ ] Exportação de relatórios do banco
- [ ] Auditoria de operações
- [ ] Backup automático
