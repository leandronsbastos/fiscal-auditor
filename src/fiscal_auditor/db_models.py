"""
Modelos do banco de dados.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Text, Numeric, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


# Tabela associativa para relacionamento many-to-many entre Usuario e Empresa
usuario_empresa = Table(
    'usuario_empresa',
    Base.metadata,
    Column('usuario_id', Integer, ForeignKey('usuarios.id'), primary_key=True),
    Column('empresa_id', Integer, ForeignKey('empresas.id'), primary_key=True),
    Column('data_vinculo', DateTime, default=datetime.now)
)


class Usuario(Base):
    """Modelo de usuário do sistema."""
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    senha_hash = Column(String(200), nullable=False)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    empresas = relationship('Empresa', secondary=usuario_empresa, back_populates='usuarios')


class Empresa(Base):
    """Modelo de empresa."""
    __tablename__ = 'empresas'

    id = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(18), unique=True, index=True, nullable=False)
    razao_social = Column(String(200), nullable=False)
    nome_fantasia = Column(String(200))
    inscricao_estadual = Column(String(20))
    inscricao_municipal = Column(String(20))
    endereco = Column(String(300))
    cidade = Column(String(100))
    estado = Column(String(2))
    cep = Column(String(10))
    telefone = Column(String(20))
    email = Column(String(200))
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    usuarios = relationship('Usuario', secondary=usuario_empresa, back_populates='empresas')
    analises = relationship('Analise', back_populates='empresa', cascade='all, delete-orphan')


class Analise(Base):
    """Modelo de análise fiscal."""
    __tablename__ = 'analises'

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    periodo = Column(String(10), nullable=False)  # MM/AAAA
    data_processamento = Column(DateTime, default=datetime.now)
    
    # Totais
    total_documentos = Column(Integer, default=0)
    total_entradas = Column(Numeric(15, 2), default=0)
    total_saidas = Column(Numeric(15, 2), default=0)
    
    # Tributos - Débitos
    icms_debito = Column(Numeric(15, 2), default=0)
    ipi_debito = Column(Numeric(15, 2), default=0)
    pis_debito = Column(Numeric(15, 2), default=0)
    cofins_debito = Column(Numeric(15, 2), default=0)
    ibs_debito = Column(Numeric(15, 2), default=0)
    cbs_debito = Column(Numeric(15, 2), default=0)
    
    # Tributos - Créditos
    icms_credito = Column(Numeric(15, 2), default=0)
    ipi_credito = Column(Numeric(15, 2), default=0)
    pis_credito = Column(Numeric(15, 2), default=0)
    cofins_credito = Column(Numeric(15, 2), default=0)
    ibs_credito = Column(Numeric(15, 2), default=0)
    cbs_credito = Column(Numeric(15, 2), default=0)
    
    # Tributos - Saldos
    icms_saldo = Column(Numeric(15, 2), default=0)
    ipi_saldo = Column(Numeric(15, 2), default=0)
    pis_saldo = Column(Numeric(15, 2), default=0)
    cofins_saldo = Column(Numeric(15, 2), default=0)
    ibs_saldo = Column(Numeric(15, 2), default=0)
    cbs_saldo = Column(Numeric(15, 2), default=0)
    
    # Dados completos em JSON
    relatorio_completo = Column(Text)  # JSON com todos os detalhes
    
    # Relacionamentos
    empresa = relationship('Empresa', back_populates='analises')
    documentos = relationship('DocumentoFiscalDB', back_populates='analise', cascade='all, delete-orphan')


class DocumentoFiscalDB(Base):
    """Modelo de documento fiscal armazenado."""
    __tablename__ = 'documentos_fiscais'

    id = Column(Integer, primary_key=True, index=True)
    analise_id = Column(Integer, ForeignKey('analises.id'), nullable=False)
    
    chave = Column(String(44), index=True, nullable=False)
    numero = Column(String(20))
    serie = Column(String(10))
    tipo_documento = Column(String(10))  # NF-e, NFC-e, etc
    tipo_movimento = Column(String(10))  # Entrada/Saída
    data_emissao = Column(DateTime)
    
    cnpj_emitente = Column(String(18))
    cnpj_destinatario = Column(String(18))
    
    valor_total = Column(Numeric(15, 2))
    
    # Relacionamentos
    analise = relationship('Analise', back_populates='documentos')
