# 🚀 Guia Rápido - Fiscal Auditor com PostgreSQL

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
2. **PostgreSQL** instalado e rodando
3. Dependências instaladas: `pip install -r requirements.txt`

---

## ⚙️ Configuração Inicial

### 1. Instalar PostgreSQL

Baixe em: https://www.postgresql.org/download/

Durante a instalação, anote:
- Usuário (padrão: `postgres`)
- Senha que você definir
- Porta (padrão: `5432`)

### 2. Criar o Banco de Dados

Abra o **pgAdmin** ou **psql** e execute:

```sql
CREATE DATABASE fiscal_auditor;
```

### 3. Configurar Conexão

**Opção A: Variável de Ambiente (Recomendado)**

Windows PowerShell:
```powershell
$env:DATABASE_URL = "postgresql://postgres:suasenha@localhost:5432/fiscal_auditor"
```

Linux/Mac:
```bash
export DATABASE_URL="postgresql://postgres:suasenha@localhost:5432/fiscal_auditor"
```

**Opção B: Arquivo .env**

Copie `.env.example` para `.env` e edite com suas credenciais.

### 4. Inicializar Banco de Dados

Execute o script de inicialização:

```bash
python init_db.py
```

Isso criará todas as tabelas necessárias:
- `usuarios` - Usuários do sistema
- `empresas` - Empresas (CNPJs)
- `usuario_empresa` - Relacionamento N:N
- `analises` - Análises fiscais processadas
- `documentos_fiscais` - Documentos armazenados

---

## 🎯 Executar a Aplicação

```bash
python app.py
```

Acesse: http://localhost:8000

---

## 📖 Usando a API

### Documentação Interativa

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Fluxo Completo

#### 1. Criar Usuário

```bash
curl -X POST "http://localhost:8000/api/usuarios" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "email": "joao@empresa.com",
    "senha": "senha123"
  }'
```

Resposta:
```json
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao@empresa.com",
  "ativo": true,
  "data_criacao": "2024-01-15T10:30:00",
  "empresas": []
}
```

#### 2. Criar Empresa

```bash
curl -X POST "http://localhost:8000/api/empresas" \
  -H "Content-Type: application/json" \
  -d '{
    "cnpj": "12345678000190",
    "razao_social": "Empresa Exemplo LTDA",
    "nome_fantasia": "Empresa Exemplo"
  }'
```

#### 3. Vincular Usuário à Empresa

```bash
curl -X POST "http://localhost:8000/api/vinculos" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": 1,
    "empresa_id": 1
  }'
```

#### 4. Listar Empresas do Usuário

```bash
curl "http://localhost:8000/api/usuarios/1/empresas"
```

#### 5. Fazer Upload de XMLs

Use a interface web em http://localhost:8000

#### 6. Consultar Análises

```bash
curl "http://localhost:8000/api/empresas/1/analises"
```

---

## 🧪 Testar a API

Execute o script de teste automatizado:

```bash
python test_api.py
```

Este script testa todos os endpoints principais.

---

## 📊 Estrutura do Banco de Dados

### Usuários
- Armazena usuários do sistema
- Senha criptografada com bcrypt
- Pode estar vinculado a múltiplas empresas

### Empresas
- Identificadas por CNPJ único
- Dados cadastrais completos
- Pode ter múltiplos usuários

### Análises
- Vinculadas a uma empresa
- Armazena totais de tributos
- JSON completo com todos os detalhes
- Histórico de processamentos

### Documentos Fiscais
- Vinculados a uma análise
- Chave de acesso para identificação
- Metadados principais

---

## 🔍 Endpoints Disponíveis

### Usuários
- `POST /api/usuarios` - Criar
- `GET /api/usuarios` - Listar todos
- `GET /api/usuarios/{id}` - Obter um
- `PUT /api/usuarios/{id}` - Atualizar
- `DELETE /api/usuarios/{id}` - Deletar

### Empresas
- `POST /api/empresas` - Criar
- `GET /api/empresas` - Listar todas
- `GET /api/empresas/{id}` - Obter uma
- `PUT /api/empresas/{id}` - Atualizar
- `DELETE /api/empresas/{id}` - Deletar

### Vínculos
- `POST /api/vinculos` - Criar vínculo
- `DELETE /api/vinculos/{usuario_id}/{empresa_id}` - Remover
- `GET /api/usuarios/{id}/empresas` - Empresas do usuário
- `GET /api/empresas/{id}/usuarios` - Usuários da empresa

### Análises
- `GET /api/empresas/{id}/analises` - Listar análises
- `GET /api/analises/{id}` - Obter detalhes
- `DELETE /api/analises/{id}` - Deletar

---

## 🛠️ Comandos Úteis

### Ver logs do servidor
O servidor exibe logs detalhados no console ao processar requisições.

### Verificar conexão com banco
```bash
python -c "from fiscal_auditor.database import engine; print(engine.url)"
```

### Resetar banco de dados
```sql
DROP DATABASE fiscal_auditor;
CREATE DATABASE fiscal_auditor;
```
Depois execute: `python init_db.py`

---

## 📝 Notas Importantes

1. **Senhas:** Armazenadas com hash bcrypt (seguras)
2. **CNPJ:** Validado e normalizado (apenas números)
3. **Multi-tenancy:** Um usuário pode acessar múltiplas empresas
4. **Análises:** Salvam JSON completo para consultas detalhadas

---

## 🔐 Segurança

⚠️ **Esta versão não possui autenticação JWT implementada.**

Para produção, recomenda-se:
- Implementar login com JWT tokens
- Adicionar middleware de autenticação
- Proteger endpoints com permissões
- Usar HTTPS
- Implementar rate limiting

---

## 🐛 Troubleshooting

### Erro: "could not connect to server"
- Verifique se o PostgreSQL está rodando
- Confirme usuário/senha/porta na DATABASE_URL

### Erro: "relation does not exist"
- Execute `python init_db.py` para criar as tabelas

### Erro: "CNPJ já cadastrado"
- Use outro CNPJ ou consulte o existente

### Erro: "Email já cadastrado"
- Use outro email ou faça login com o existente

---

## 📚 Documentação Completa

Veja [DATABASE_API.md](DATABASE_API.md) para documentação detalhada da API.

---

## ✅ Checklist de Setup

- [ ] PostgreSQL instalado e rodando
- [ ] Banco de dados `fiscal_auditor` criado
- [ ] Variável `DATABASE_URL` configurada
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Banco inicializado (`python init_db.py`)
- [ ] Servidor iniciado (`python app.py`)
- [ ] API testada (`python test_api.py` ou Swagger)

---

**Pronto para usar! 🎉**
