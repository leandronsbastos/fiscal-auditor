"""
Rotas para gerenciamento de empresas e usuários.
"""
from flask import Blueprint, jsonify, request, render_template
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

empresas_bp = Blueprint('empresas', __name__, url_prefix='/empresas')

# Modelos serão importados depois
Empresa = None
Usuario = None  
UsuarioEmpresa = None
db = None


def init_models(database, empresa_model, usuario_model, usuario_empresa_model):
    """Inicializa os modelos com a instância do banco."""
    global Empresa, Usuario, UsuarioEmpresa, db
    db = database
    Empresa = empresa_model
    Usuario = usuario_model
    UsuarioEmpresa = usuario_empresa_model


@empresas_bp.route('/')
def index():
    """Página de gerenciamento de empresas."""
    return render_template('empresas.html')


@empresas_bp.route('/api/empresas', methods=['GET'])
def listar_empresas():
    """Lista todas as empresas."""
    try:
        empresas = Empresa.query.order_by(Empresa.razao_social).all()
        return jsonify({
            'empresas': [emp.to_dict() for emp in empresas]
        })
    except Exception as e:
        logger.error(f"Erro ao listar empresas: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@empresas_bp.route('/api/empresas/<int:empresa_id>', methods=['GET'])
def obter_empresa(empresa_id):
    """Obtém detalhes de uma empresa."""
    try:
        empresa = Empresa.query.get_or_404(empresa_id)
        return jsonify(empresa.to_dict())
    except Exception as e:
        logger.error(f"Erro ao obter empresa: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@empresas_bp.route('/api/empresas/<int:empresa_id>', methods=['PUT'])
def atualizar_empresa(empresa_id):
    """Atualiza dados de uma empresa."""
    try:
        empresa = Empresa.query.get_or_404(empresa_id)
        data = request.json
        
        # Atualizar campos
        if 'razao_social' in data:
            empresa.razao_social = data['razao_social']
        if 'nome_fantasia' in data:
            empresa.nome_fantasia = data['nome_fantasia']
        if 'ie' in data:
            empresa.ie = data['ie']
        if 'email' in data:
            empresa.email = data['email']
        if 'telefone' in data:
            empresa.telefone = data['telefone']
        if 'ativo' in data:
            empresa.ativo = data['ativo']
            
        empresa.data_atualizacao = datetime.utcnow()
        db.session.commit()
        
        return jsonify(empresa.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar empresa: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@empresas_bp.route('/api/usuarios', methods=['GET'])
def listar_usuarios():
    """Lista todos os usuários."""
    try:
        usuarios = Usuario.query.order_by(Usuario.nome).all()
        return jsonify({
            'usuarios': [usr.to_dict() for usr in usuarios]
        })
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@empresas_bp.route('/api/usuarios/<int:usuario_id>', methods=['GET'])
def obter_usuario(usuario_id):
    """Obtém detalhes de um usuário."""
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        return jsonify(usuario.to_dict())
    except Exception as e:
        logger.error(f"Erro ao obter usuário: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@empresas_bp.route('/api/vinculos', methods=['GET'])
def listar_vinculos():
    """Lista todos os vínculos usuário-empresa."""
    try:
        vinculos = UsuarioEmpresa.query.all()
        return jsonify({
            'vinculos': [v.to_dict() for v in vinculos]
        })
    except Exception as e:
        logger.error(f"Erro ao listar vínculos: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@empresas_bp.route('/api/vinculos', methods=['POST'])
def criar_vinculo():
    """Cria um novo vínculo entre usuário e empresa."""
    try:
        data = request.json
        usuario_id = data.get('usuario_id')
        empresa_id = data.get('empresa_id')
        
        if not usuario_id or not empresa_id:
            return jsonify({'error': 'usuario_id e empresa_id são obrigatórios'}), 400
        
        # Verificar se usuário e empresa existem
        usuario = Usuario.query.get(usuario_id)
        empresa = Empresa.query.get(empresa_id)
        
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        if not empresa:
            return jsonify({'error': 'Empresa não encontrada'}), 404
        
        # Verificar se vínculo já existe
        vinculo_existente = UsuarioEmpresa.query.filter_by(
            usuario_id=usuario_id,
            empresa_id=empresa_id
        ).first()
        
        if vinculo_existente:
            return jsonify({'error': 'Vínculo já existe'}), 409
        
        # Criar novo vínculo
        vinculo = UsuarioEmpresa(
            usuario_id=usuario_id,
            empresa_id=empresa_id
        )
        db.session.add(vinculo)
        db.session.commit()
        
        logger.info(f"Vínculo criado: Usuário {usuario_id} - Empresa {empresa_id}")
        return jsonify(vinculo.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar vínculo: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@empresas_bp.route('/api/vinculos/<int:vinculo_id>', methods=['DELETE'])
def excluir_vinculo(vinculo_id):
    """Remove um vínculo entre usuário e empresa."""
    try:
        vinculo = UsuarioEmpresa.query.get_or_404(vinculo_id)
        
        usuario_id = vinculo.usuario_id
        empresa_id = vinculo.empresa_id
        
        db.session.delete(vinculo)
        db.session.commit()
        
        logger.info(f"Vínculo removido: Usuário {usuario_id} - Empresa {empresa_id}")
        return jsonify({'message': 'Vínculo removido com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir vínculo: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@empresas_bp.route('/api/empresas/<int:empresa_id>/usuarios', methods=['GET'])
def listar_usuarios_empresa(empresa_id):
    """Lista usuários vinculados a uma empresa."""
    try:
        empresa = Empresa.query.get_or_404(empresa_id)
        vinculos = empresa.usuarios.all()
        
        return jsonify({
            'empresa': empresa.to_dict(),
            'usuarios': [
                {
                    'vinculo_id': v.id,
                    'usuario': v.usuario.to_dict(),
                    'data_vinculo': v.data_vinculo.isoformat() if v.data_vinculo else None
                }
                for v in vinculos
            ]
        })
    except Exception as e:
        logger.error(f"Erro ao listar usuários da empresa: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@empresas_bp.route('/api/usuarios/<int:usuario_id>/empresas', methods=['GET'])
def listar_empresas_usuario(usuario_id):
    """Lista empresas vinculadas a um usuário."""
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        vinculos = usuario.empresas.all()
        
        return jsonify({
            'usuario': usuario.to_dict(),
            'empresas': [
                {
                    'vinculo_id': v.id,
                    'empresa': v.empresa.to_dict(),
                    'data_vinculo': v.data_vinculo.isoformat() if v.data_vinculo else None
                }
                for v in vinculos
            ]
        })
    except Exception as e:
        logger.error(f"Erro ao listar empresas do usuário: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
