# 🔐 Sistema de Autenticação - Fiscal Auditor

## Visão Geral

Sistema completo de autenticação com JWT que exige que usuários estejam vinculados a pelo menos uma empresa para fazer login.

## Fluxo de Autenticação

```
1. Usuário acessa /login
2. Fornece email e senha
3. Sistema valida credenciais
4. Verifica se usuário está ativo
5. Verifica se tem empresas vinculadas
6. Gera token JWT
7. Retorna token + dados do usuário
8. Usuário é redirecionado para /painel
9. Seleciona empresa para trabalhar
10. Acessa o sistema
```

## Arquivos Criados

### Backend
- **[src/fiscal_auditor/auth.py](src/fiscal_auditor/auth.py)** - Funções de autenticação, JWT, verificação de acesso
- **app.py** - Rotas de login e proteção de endpoints

### Frontend
- **[templates/login.html](templates/login.html)** - Tela de login
- **[templates/painel.html](templates/painel.html)** - Painel de seleção de empresas

### Scripts de Setup
- **[setup_inicial.py](setup_inicial.py)** - Setup completo interativo
- **[criar_usuario.py](criar_usuario.py)** - Criar apenas usuário

## Configuração Inicial

### 1. Configurar Chave Secreta (Importante!)

Configure a variável `SECRET_KEY` para produção:

```powershell
$env:SECRET_KEY = "sua-chave-super-secreta-aleatoria-aqui"
```

### 2. Criar Primeiro Usuário e Empresa

```bash
python setup_inicial.py
```

Este script interativo irá:
1. Criar um usuário
2. Criar uma empresa
3. Vincular usuário à empresa

**Exemplo de execução:**
```
Nome completo: João Silva
E-mail: joao@empresa.com
Senha: senha123
CNPJ: 12345678000190
Razão Social: Empresa Exemplo LTDA
Nome Fantasia: Empresa Exemplo
```

## Usar o Sistema

### 1. Iniciar Servidor

```bash
python app.py
```

### 2. Fazer Login

Acesse: http://localhost:8000/login

Use as credenciais criadas no setup.

### 3. Selecionar Empresa

Após login, você será levado ao painel onde pode:
- Ver todas as empresas vinculadas
- Selecionar uma empresa para trabalhar

## Endpoints de Autenticação

### POST /api/login
Realiza login e retorna token JWT.

**Request:**
```json
{
  "email": "joao@empresa.com",
  "senha": "senha123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "usuario": {
    "id": 1,
    "nome": "João Silva",
    "email": "joao@empresa.com",
    "total_empresas": 2
  }
}
```

**Erros:**
- `401` - Email ou senha incorretos
- `403` - Usuário inativo
- `403` - Usuário não vinculado a nenhuma empresa

### GET /api/me
Retorna informações do usuário logado.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao@empresa.com",
  "ativo": true,
  "data_criacao": "2024-01-15T10:30:00",
  "empresas": [
    {
      "id": 1,
      "cnpj": "12345678000190",
      "razao_social": "Empresa Exemplo LTDA"
    }
  ]
}
```

## Protegendo Endpoints

### Exemplo 1: Requer Autenticação

```python
from fiscal_auditor.auth import obter_usuario_atual

@app.get("/api/dados-protegidos")
async def dados_protegidos(
    usuario_atual: db_models.Usuario = Depends(obter_usuario_atual)
):
    return {"mensagem": f"Olá {usuario_atual.nome}!"}
```

### Exemplo 2: Requer Acesso à Empresa

```python
from fiscal_auditor.auth import obter_usuario_atual, verificar_acesso_empresa

@app.get("/api/empresas/{empresa_id}/dados")
async def dados_empresa(
    empresa_id: int,
    usuario_atual: db_models.Usuario = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    # Verificar acesso
    if not verificar_acesso_empresa(usuario_atual, empresa_id, db):
        raise HTTPException(status_code=403, detail="Sem acesso")
    
    # Retornar dados...
```

## Endpoints Protegidos

Endpoints que **REQUEREM** autenticação:

### Usuários
- ✅ `POST /api/usuarios` - **Público** (permite cadastro)
- 🔒 `GET /api/usuarios` - Requer autenticação
- 🔒 `GET /api/usuarios/{id}` - Requer autenticação
- 🔒 `PUT /api/usuarios/{id}` - Requer autenticação
- 🔒 `DELETE /api/usuarios/{id}` - Requer autenticação

### Empresas
- 🔒 `POST /api/empresas` - Requer autenticação
- 🔒 `GET /api/empresas` - Requer autenticação
- 🔒 `GET /api/empresas/{id}` - Requer autenticação
- 🔒 `PUT /api/empresas/{id}` - Requer autenticação
- 🔒 `DELETE /api/empresas/{id}` - Requer autenticação

### Vínculos
- 🔒 `GET /api/usuarios/{id}/empresas` - Requer autenticação + próprio usuário
- 🔒 `GET /api/empresas/{id}/usuarios` - Requer autenticação

### Análises
- 🔒 `GET /api/empresas/{id}/analises` - Requer autenticação + acesso à empresa
- 🔒 `GET /api/analises/{id}` - Requer autenticação
- 🔒 `DELETE /api/analises/{id}` - Requer autenticação

## Usando Token na API

### cURL

```bash
# Fazer login
TOKEN=$(curl -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@empresa.com","senha":"senha123"}' \
  | jq -r '.access_token')

# Usar token
curl "http://localhost:8000/api/me" \
  -H "Authorization: Bearer $TOKEN"
```

### Python

```python
import requests

# Login
response = requests.post("http://localhost:8000/api/login", json={
    "email": "joao@empresa.com",
    "senha": "senha123"
})
token = response.json()["access_token"]

# Usar token
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/me", headers=headers)
print(response.json())
```

### JavaScript (Frontend)

```javascript
// Login
const response = await fetch('/api/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: 'joao@empresa.com',
        senha: 'senha123'
    })
});

const data = await response.json();
const token = data.access_token;

// Salvar token
localStorage.setItem('token', token);

// Usar token
const response2 = await fetch('/api/me', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

## Configurações de Segurança

### Duração do Token

Padrão: **8 horas** (480 minutos)

Altere em [src/fiscal_auditor/auth.py](src/fiscal_auditor/auth.py):
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 480
```

### Chave Secreta

⚠️ **IMPORTANTE:** Em produção, use uma chave forte e aleatória!

```powershell
# Gerar chave aleatória
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Configurar
$env:SECRET_KEY = "chave-gerada-acima"
```

### Hash de Senha

Usa **bcrypt** - algoritmo seguro e recomendado.

## Regras de Negócio

### Login
1. Usuário deve existir
2. Senha deve estar correta
3. Usuário deve estar ativo
4. **Usuário deve ter pelo menos 1 empresa vinculada**

### Acesso a Dados
1. Usuário pode ver apenas suas próprias empresas
2. Usuário só acessa análises de empresas vinculadas
3. Token expira após 8 horas

## Gerenciar Vínculos

### Via Script Python

```python
from fiscal_auditor.database import SessionLocal
from fiscal_auditor import crud

db = SessionLocal()

# Vincular
crud.vincular_usuario_empresa(db, usuario_id=1, empresa_id=1)

# Desvincular
crud.desvincular_usuario_empresa(db, usuario_id=1, empresa_id=1)

# Listar empresas do usuário
empresas = crud.listar_empresas_usuario(db, usuario_id=1)
for emp in empresas:
    print(f"{emp.razao_social} - {emp.cnpj}")

db.close()
```

### Via API (requer autenticação)

```bash
# Vincular (endpoint não implementado no exemplo público)
# Por segurança, vincular deve ser feito via admin ou script

# Listar empresas do usuário
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/usuarios/1/empresas"
```

## Testando Autenticação

### Teste Completo

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Tentar acessar sem token (deve falhar)
response = requests.get(f"{BASE_URL}/api/me")
print(f"Sem token: {response.status_code}")  # 401

# 2. Fazer login
response = requests.post(f"{BASE_URL}/api/login", json={
    "email": "joao@empresa.com",
    "senha": "senha123"
})
token = response.json()["access_token"]
print(f"Token obtido: {token[:20]}...")

# 3. Acessar com token
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/api/me", headers=headers)
print(f"Com token: {response.status_code}")  # 200
print(f"Usuário: {response.json()['nome']}")

# 4. Listar empresas
response = requests.get(
    f"{BASE_URL}/api/usuarios/1/empresas",
    headers=headers
)
empresas = response.json()
print(f"Empresas: {len(empresas)}")
for emp in empresas:
    print(f"  - {emp['razao_social']}")
```

## Troubleshooting

### "Usuário não está vinculado a nenhuma empresa"

**Solução:**
```bash
python setup_inicial.py
# ou
python -c "
from fiscal_auditor.database import SessionLocal
from fiscal_auditor import crud
db = SessionLocal()
crud.vincular_usuario_empresa(db, usuario_id=1, empresa_id=1)
db.close()
"
```

### "Não foi possível validar as credenciais"

**Possíveis causas:**
1. Token expirado (refaça login)
2. Token inválido (formato incorreto)
3. SECRET_KEY diferente entre gerações

### "Você não tem acesso a esta empresa"

**Solução:** Vincule o usuário à empresa:
```python
crud.vincular_usuario_empresa(db, usuario_id, empresa_id)
```

---

## Fluxo Completo - Exemplo Prático

```bash
# 1. Inicializar banco
python init_db.py

# 2. Criar usuário e empresa
python setup_inicial.py

# 3. Iniciar servidor
python app.py

# 4. Acessar navegador
# http://localhost:8000/login

# 5. Fazer login
# Email: joao@empresa.com
# Senha: senha123

# 6. Selecionar empresa no painel

# 7. Trabalhar no sistema!
```

---

**Sistema de autenticação implementado com sucesso! 🎉**
