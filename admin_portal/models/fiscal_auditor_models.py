"""
Modelos do banco fiscal_auditor (empresas e usuários).
"""
from datetime import datetime


def create_models(db):
    """Cria os modelos usando a instância do SQLAlchemy."""
    
    class Empresa(db.Model):
        """Modelo para empresas no banco fiscal_auditor."""
        
        __bind_key__ = 'fiscal_auditor'
        __tablename__ = 'empresas'
        
        id = db.Column(db.Integer, primary_key=True)
        cnpj = db.Column(db.String(14), unique=True, nullable=False, index=True)
        razao_social = db.Column(db.String(200), nullable=False)
        nome_fantasia = db.Column(db.String(200))
        ie = db.Column(db.String(20))
        im = db.Column(db.String(20))
        cnae = db.Column(db.String(10))
        
        # Endereço
        logradouro = db.Column(db.String(200))
        numero = db.Column(db.String(20))
        complemento = db.Column(db.String(100))
        bairro = db.Column(db.String(100))
        municipio = db.Column(db.String(100))
        uf = db.Column(db.String(2))
        cep = db.Column(db.String(8))
        codigo_municipio = db.Column(db.String(7))
        pais = db.Column(db.String(100))
        codigo_pais = db.Column(db.String(4))
        
        # Contato
        telefone = db.Column(db.String(20))
        email = db.Column(db.String(100))
        
        # Regime tributário
        regime_tributario = db.Column(db.String(1))
        
        # Status
        ativo = db.Column(db.Boolean, default=True)
        
        # Timestamps
        data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
        data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        # Relacionamento com usuários
        usuarios = db.relationship('UsuarioEmpresa', back_populates='empresa', lazy='dynamic')
        
        def to_dict(self):
            """Converte para dicionário."""
            return {
                'id': self.id,
                'cnpj': self.cnpj,
                'razao_social': self.razao_social,
                'nome_fantasia': self.nome_fantasia,
                'ie': self.ie,
                'im': self.im,
                'cnae': self.cnae,
                'logradouro': self.logradouro,
                'numero': self.numero,
                'complemento': self.complemento,
                'bairro': self.bairro,
                'municipio': self.municipio,
                'uf': self.uf,
                'cep': self.cep,
                'codigo_municipio': self.codigo_municipio,
                'pais': self.pais,
                'codigo_pais': self.codigo_pais,
                'telefone': self.telefone,
                'email': self.email,
                'regime_tributario': self.regime_tributario,
                'ativo': self.ativo,
                'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
                'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
                'usuarios_count': self.usuarios.count()
            }
    
    
    class Usuario(db.Model):
        """Modelo para usuários no banco fiscal_auditor."""
        
        __bind_key__ = 'fiscal_auditor'
        __tablename__ = 'usuarios'
        
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(200), nullable=False)
        email = db.Column(db.String(100), unique=True, nullable=False, index=True)
        senha_hash = db.Column(db.String(255), nullable=False)
        
        # Perfil
        perfil = db.Column(db.String(20), default='usuario')
        
        # Status
        ativo = db.Column(db.Boolean, default=True)
        
        # Timestamps
        data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
        ultimo_acesso = db.Column(db.DateTime)
        
        # Relacionamento com empresas
        empresas = db.relationship('UsuarioEmpresa', back_populates='usuario', lazy='dynamic')
        
        def to_dict(self):
            """Converte para dicionário."""
            return {
                'id': self.id,
                'nome': self.nome,
                'email': self.email,
                'perfil': self.perfil,
                'ativo': self.ativo,
                'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
                'ultimo_acesso': self.ultimo_acesso.isoformat() if self.ultimo_acesso else None,
                'empresas_count': self.empresas.count()
            }
    
    
    class UsuarioEmpresa(db.Model):
        """Relacionamento entre usuários e empresas."""
        
        __bind_key__ = 'fiscal_auditor'
        __tablename__ = 'usuario_empresa'
        
        id = db.Column(db.Integer, primary_key=True)
        usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
        empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
        data_vinculo = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Relacionamentos
        usuario = db.relationship('Usuario', back_populates='empresas')
        empresa = db.relationship('Empresa', back_populates='usuarios')
        
        # Índice único para evitar duplicatas
        __table_args__ = (
            db.UniqueConstraint('usuario_id', 'empresa_id', name='uk_usuario_empresa'),
        )
        
        def to_dict(self):
            """Converte para dicionário."""
            return {
                'id': self.id,
                'usuario_id': self.usuario_id,
                'empresa_id': self.empresa_id,
                'usuario_nome': self.usuario.nome if self.usuario else None,
                'empresa_razao_social': self.empresa.razao_social if self.empresa else None,
                'data_vinculo': self.data_vinculo.isoformat() if self.data_vinculo else None
            }
    
    return {
        'Empresa': Empresa,
        'Usuario': Usuario,
        'UsuarioEmpresa': UsuarioEmpresa
    }
