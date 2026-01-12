"""
Script para criar tabelas de empresas e usuários no banco fiscal_auditor
"""
from sqlalchemy import create_engine, text
import os

# URL do banco fiscal_auditor
db_url = os.getenv(
    'FISCAL_AUDITOR_DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/fiscal_auditor'
)

engine = create_engine(db_url)

# SQL para criar as tabelas
sql_criar_tabelas = """
-- Tabela de usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    senha_hash VARCHAR(200) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT NOW(),
    data_atualizacao TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);

-- Tabela de empresas
CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14) UNIQUE NOT NULL,
    razao_social VARCHAR(200) NOT NULL,
    nome_fantasia VARCHAR(200),
    ie VARCHAR(20),
    im VARCHAR(20),
    cnae VARCHAR(10),
    logradouro VARCHAR(200),
    numero VARCHAR(20),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    municipio VARCHAR(100),
    uf VARCHAR(2),
    cep VARCHAR(8),
    codigo_municipio VARCHAR(7),
    pais VARCHAR(100),
    codigo_pais VARCHAR(4),
    telefone VARCHAR(20),
    email VARCHAR(100),
    regime_tributario VARCHAR(1),
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_empresas_cnpj ON empresas(cnpj);

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    perfil VARCHAR(20) DEFAULT 'usuario',
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acesso TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);

-- Tabela associativa usuário-empresa (many-to-many)
CREATE TABLE IF NOT EXISTS usuario_empresa (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    data_vinculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_usuario_empresa UNIQUE (usuario_id, empresa_id)
);

CREATE INDEX IF NOT EXISTS idx_usuario_empresa_usuario ON usuario_empresa(usuario_id);
CREATE INDEX IF NOT EXISTS idx_usuario_empresa_empresa ON usuario_empresa(empresa_id);

-- Inserir usuário admin padrão (senha: admin123)
INSERT INTO usuarios (nome, email, senha_hash, ativo)
VALUES ('Administrador', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5jtJ3sduyUqK2', TRUE)
ON CONFLICT (email) DO NOTHING;
"""

try:
    print("Criando tabelas de empresas e usuários no banco fiscal_auditor...")
    print("=" * 80)
    
    with engine.begin() as conn:
        conn.execute(text(sql_criar_tabelas))
    
    print("✓ Tabelas criadas com sucesso!")
    print()
    print("Tabelas criadas:")
    print("  - empresas")
    print("  - usuarios")
    print("  - usuario_empresa (associativa)")
    print()
    print("Usuário padrão criado:")
    print("  Email: admin@example.com")
    print("  Senha: admin123")
    print("=" * 80)
    
except Exception as e:
    print(f"✗ Erro ao criar tabelas: {e}")
    raise
finally:
    engine.dispose()
