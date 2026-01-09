"""
Configuração do banco de dados para o serviço ETL.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# URL de conexão do PostgreSQL para o datalake
DATABASE_URL = os.getenv(
    "ETL_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/fiscal_datalake"
)

# Criar engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

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


def init_database():
    """
    Inicializa o banco de dados, criando todas as tabelas.
    """
    from . import models  # Import here to avoid circular dependency
    Base.metadata.create_all(bind=engine)
