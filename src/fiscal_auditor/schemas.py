"""
Schemas Pydantic para validação de dados da API.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import re


# ============= USUÁRIO =============

class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=200)
    email: EmailStr


class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6)


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=200)
    email: Optional[EmailStr] = None
    senha: Optional[str] = Field(None, min_length=6)
    ativo: Optional[bool] = None


class UsuarioResponse(UsuarioBase):
    id: int
    ativo: bool
    data_criacao: datetime
    empresas: List['EmpresaSimples'] = []

    class Config:
        from_attributes = True


# ============= EMPRESA =============

class EmpresaBase(BaseModel):
    cnpj: str = Field(..., min_length=14, max_length=18)
    razao_social: str = Field(..., min_length=3, max_length=200)
    nome_fantasia: Optional[str] = Field(None, max_length=200)
    inscricao_estadual: Optional[str] = Field(None, max_length=20)
    inscricao_municipal: Optional[str] = Field(None, max_length=20)
    endereco: Optional[str] = Field(None, max_length=300)
    cidade: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = Field(None, max_length=10)
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None

    @validator('cnpj')
    def validar_cnpj(cls, v):
        # Remove caracteres não numéricos
        cnpj = re.sub(r'[^0-9]', '', v)
        if len(cnpj) != 14:
            raise ValueError('CNPJ deve ter 14 dígitos')
        return cnpj


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    razao_social: Optional[str] = Field(None, min_length=3, max_length=200)
    nome_fantasia: Optional[str] = Field(None, max_length=200)
    inscricao_estadual: Optional[str] = Field(None, max_length=20)
    inscricao_municipal: Optional[str] = Field(None, max_length=20)
    endereco: Optional[str] = Field(None, max_length=300)
    cidade: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = Field(None, max_length=10)
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    ativo: Optional[bool] = None


class EmpresaResponse(EmpresaBase):
    id: int
    ativo: bool
    data_criacao: datetime

    class Config:
        from_attributes = True


class EmpresaSimples(BaseModel):
    id: int
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str]

    class Config:
        from_attributes = True


# ============= VÍNCULO =============

class VincularEmpresa(BaseModel):
    usuario_id: int
    empresa_id: int


# ============= ANÁLISE =============

class AnaliseResponse(BaseModel):
    id: int
    periodo: str
    data_processamento: datetime
    total_documentos: int
    total_entradas: float
    total_saidas: float
    icms_saldo: float
    ipi_saldo: float
    pis_saldo: float
    cofins_saldo: float
    ibs_saldo: float
    cbs_saldo: float

    class Config:
        from_attributes = True


# Resolve forward references
UsuarioResponse.model_rebuild()
