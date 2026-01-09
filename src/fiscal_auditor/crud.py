"""
Operações CRUD para o banco de dados.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from passlib.context import CryptContext
from . import db_models, schemas

# Configuração para hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============= USUÁRIO =============

def get_password_hash(password: str) -> str:
    """Gera hash da senha."""
    # Bcrypt tem limite de 72 bytes - truncar se necessário
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    return pwd_context.verify(plain_password, hashed_password)


def criar_usuario(db: Session, usuario: schemas.UsuarioCreate) -> db_models.Usuario:
    """Cria um novo usuário."""
    senha_hash = get_password_hash(usuario.senha)
    db_usuario = db_models.Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=senha_hash
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


def obter_usuario(db: Session, usuario_id: int) -> Optional[db_models.Usuario]:
    """Obtém usuário por ID."""
    return db.query(db_models.Usuario).filter(db_models.Usuario.id == usuario_id).first()


def obter_usuario_por_email(db: Session, email: str) -> Optional[db_models.Usuario]:
    """Obtém usuário por email."""
    return db.query(db_models.Usuario).filter(db_models.Usuario.email == email).first()


def listar_usuarios(db: Session, skip: int = 0, limit: int = 100) -> List[db_models.Usuario]:
    """Lista todos os usuários."""
    return db.query(db_models.Usuario).offset(skip).limit(limit).all()


def atualizar_usuario(
    db: Session,
    usuario_id: int,
    usuario_update: schemas.UsuarioUpdate
) -> Optional[db_models.Usuario]:
    """Atualiza dados do usuário."""
    db_usuario = obter_usuario(db, usuario_id)
    if not db_usuario:
        return None
    
    update_data = usuario_update.model_dump(exclude_unset=True)
    
    # Se senha foi fornecida, gera novo hash
    if 'senha' in update_data:
        senha_hash = get_password_hash(update_data.pop('senha'))
        update_data['senha_hash'] = senha_hash
    
    for key, value in update_data.items():
        setattr(db_usuario, key, value)
    
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


def deletar_usuario(db: Session, usuario_id: int) -> bool:
    """Deleta um usuário."""
    db_usuario = obter_usuario(db, usuario_id)
    if not db_usuario:
        return False
    
    db.delete(db_usuario)
    db.commit()
    return True


# ============= EMPRESA =============

def criar_empresa(db: Session, empresa: schemas.EmpresaCreate) -> db_models.Empresa:
    """Cria uma nova empresa."""
    db_empresa = db_models.Empresa(**empresa.model_dump())
    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa


def obter_empresa(db: Session, empresa_id: int) -> Optional[db_models.Empresa]:
    """Obtém empresa por ID."""
    return db.query(db_models.Empresa).filter(db_models.Empresa.id == empresa_id).first()


def obter_empresa_por_cnpj(db: Session, cnpj: str) -> Optional[db_models.Empresa]:
    """Obtém empresa por CNPJ."""
    return db.query(db_models.Empresa).filter(db_models.Empresa.cnpj == cnpj).first()


def listar_empresas(db: Session, skip: int = 0, limit: int = 100) -> List[db_models.Empresa]:
    """Lista todas as empresas."""
    return db.query(db_models.Empresa).offset(skip).limit(limit).all()


def atualizar_empresa(
    db: Session,
    empresa_id: int,
    empresa_update: schemas.EmpresaUpdate
) -> Optional[db_models.Empresa]:
    """Atualiza dados da empresa."""
    db_empresa = obter_empresa(db, empresa_id)
    if not db_empresa:
        return None
    
    update_data = empresa_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_empresa, key, value)
    
    db.commit()
    db.refresh(db_empresa)
    return db_empresa


def deletar_empresa(db: Session, empresa_id: int) -> bool:
    """Deleta uma empresa."""
    db_empresa = obter_empresa(db, empresa_id)
    if not db_empresa:
        return False
    
    db.delete(db_empresa)
    db.commit()
    return True


# ============= VÍNCULOS =============

def vincular_usuario_empresa(db: Session, usuario_id: int, empresa_id: int) -> bool:
    """Vincula um usuário a uma empresa."""
    usuario = obter_usuario(db, usuario_id)
    empresa = obter_empresa(db, empresa_id)
    
    if not usuario or not empresa:
        return False
    
    if empresa not in usuario.empresas:
        usuario.empresas.append(empresa)
        db.commit()
    
    return True


def desvincular_usuario_empresa(db: Session, usuario_id: int, empresa_id: int) -> bool:
    """Desvincula um usuário de uma empresa."""
    usuario = obter_usuario(db, usuario_id)
    empresa = obter_empresa(db, empresa_id)
    
    if not usuario or not empresa:
        return False
    
    if empresa in usuario.empresas:
        usuario.empresas.remove(empresa)
        db.commit()
    
    return True


def listar_empresas_usuario(db: Session, usuario_id: int) -> List[db_models.Empresa]:
    """Lista todas as empresas vinculadas a um usuário."""
    usuario = obter_usuario(db, usuario_id)
    if not usuario:
        return []
    return usuario.empresas


def listar_usuarios_empresa(db: Session, empresa_id: int) -> List[db_models.Usuario]:
    """Lista todos os usuários vinculados a uma empresa."""
    empresa = obter_empresa(db, empresa_id)
    if not empresa:
        return []
    return empresa.usuarios


# ============= ANÁLISE =============

def criar_analise(
    db: Session,
    empresa_id: int,
    periodo: str,
    dados_analise: dict
) -> db_models.Analise:
    """Cria uma nova análise."""
    import json
    
    db_analise = db_models.Analise(
        empresa_id=empresa_id,
        periodo=periodo,
        relatorio_completo=json.dumps(dados_analise)
    )
    
    # Preenche totais se disponíveis
    if 'mapa_apuracao' in dados_analise:
        mapa = dados_analise['mapa_apuracao']
        
        for tributo, valores in mapa.items():
            if isinstance(valores, dict):
                setattr(db_analise, f'{tributo.lower()}_debito', valores.get('debito', 0))
                setattr(db_analise, f'{tributo.lower()}_credito', valores.get('credito', 0))
                setattr(db_analise, f'{tributo.lower()}_saldo', valores.get('saldo', 0))
    
    if 'resumo' in dados_analise:
        resumo = dados_analise['resumo']
        db_analise.total_documentos = resumo.get('total_documentos', 0)
        db_analise.total_entradas = resumo.get('total_entradas', 0)
        db_analise.total_saidas = resumo.get('total_saidas', 0)
    
    db.add(db_analise)
    db.commit()
    db.refresh(db_analise)
    return db_analise


def listar_analises_empresa(
    db: Session,
    empresa_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[db_models.Analise]:
    """Lista análises de uma empresa."""
    return db.query(db_models.Analise)\
        .filter(db_models.Analise.empresa_id == empresa_id)\
        .order_by(db_models.Analise.data_processamento.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def obter_analise(db: Session, analise_id: int) -> Optional[db_models.Analise]:
    """Obtém uma análise por ID."""
    return db.query(db_models.Analise).filter(db_models.Analise.id == analise_id).first()


def deletar_analise(db: Session, analise_id: int) -> bool:
    """Deleta uma análise."""
    db_analise = obter_analise(db, analise_id)
    if not db_analise:
        return False
    
    db.delete(db_analise)
    db.commit()
    return True
