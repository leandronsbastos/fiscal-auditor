"""
Utilitários de autenticação e segurança.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os

from .database import get_db
from . import crud, db_models

# Configurações
SECRET_KEY = os.getenv("SECRET_KEY", "sua-chave-secreta-super-segura-mude-em-producao")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def criar_token_acesso(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria um token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verificar_token(token: str) -> Optional[dict]:
    """Verifica e decodifica um token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def obter_usuario_atual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> db_models.Usuario:
    """
    Dependency para obter o usuário atual autenticado.
    Usa o token JWT do header Authorization.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verificar_token(token)
    
    if payload is None:
        raise credentials_exception
    
    usuario_id: int = payload.get("sub")
    if usuario_id is None:
        raise credentials_exception
    
    usuario = crud.obter_usuario(db, usuario_id=int(usuario_id))
    if usuario is None:
        raise credentials_exception
    
    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    return usuario


def verificar_acesso_empresa(
    usuario: db_models.Usuario,
    empresa_id: int,
    db: Session
) -> bool:
    """
    Verifica se o usuário tem acesso à empresa especificada.
    """
    empresas_usuario = [emp.id for emp in usuario.empresas]
    return empresa_id in empresas_usuario


def require_acesso_empresa(empresa_id: int):
    """
    Dependency factory para verificar acesso à empresa.
    """
    def _verificar(
        usuario: db_models.Usuario = Depends(obter_usuario_atual),
        db: Session = Depends(get_db)
    ):
        if not verificar_acesso_empresa(usuario, empresa_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem acesso a esta empresa"
            )
        return usuario
    return _verificar
