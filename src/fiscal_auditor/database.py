"""
Configuração do banco de dados PostgreSQL.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# URL de conexão do PostgreSQL
# Formato: postgresql://usuario:senha@host:porta/nome_banco
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/fiscal_auditor"
)

# Criar engine
engine = create_engine(DATABASE_URL)

# Criar SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obter sessão do banco de dados.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas.
    """
    from . import models  # Import aqui para evitar circular import
    Base.metadata.create_all(bind=engine)
