"""
Rotas para gerenciamento de empresas e usuários
"""
from flask import Blueprint, jsonify, request, render_template
from sqlalchemy import create_engine, text
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Blueprint será registrado no app_admin.py
empresa_bp = Blueprint('empresa', __name__)


def init_empresa_routes(app, db_url):
    """
    Inicializa as rotas de empresa com a engine do banco
    
    Args:
        app: Instância Flask
        db_url: URL de conexão do banco de dados
    """
    engine = create_engine(db_url)
    
    @app.route('/empresas')
    def pagina_empresas():
        """Página de gerenciamento de empresas e usuários"""
        return render_template('empresas.html')
    
    @app.route('/api/empresas', methods=['GET'])
    def listar_empresas():
        """Lista todas as empresas"""
        try:
            with engine.begin() as conn:
                result = conn.execute(text("""
                    SELECT 
                        e.id,
                        e.cnpj,
                        e.razao_social,
                        e.nome_fantasia,
                        e.inscricao_estadual,
                        e.cidade,
                        e.estado,
                        e.ativo,
                        e.data_criacao,
                        COUNT(DISTINCT ue.usuario_id) as total_usuarios
                    FROM empresas e
                    LEFT JOIN usuario_empresa ue ON e.id = ue.empresa_id
                    GROUP BY e.id, e.cnpj, e.razao_social, e.nome_fantasia, 
                             e.inscricao_estadual, e.cidade, e.estado, e.ativo, e.data_criacao
                    ORDER BY e.razao_social
                """))
                
                empresas = []
                for row in result:
                    empresas.append({
                        'id': row[0],
                        'cnpj': formatar_cnpj(row[1]),
                        'razao_social': row[2],
                        'nome_fantasia': row[3],
                        'inscricao_estadual': row[4],
                        'cidade': row[5],
                        'estado': row[6],
                        'ativo': row[7],
                        'data_criacao': row[8].isoformat() if row[8] else None,
                        'total_usuarios': row[9]
                    })
                
                return jsonify(empresas), 200
                
        except Exception as e:
            logger.error(f"Erro ao listar empresas: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/usuarios', methods=['GET'])
    def listar_usuarios():
        """Lista todos os usuários"""
        try:
            with engine.begin() as conn:
                result = conn.execute(text("""
                    SELECT 
                        u.id,
                        u.nome,
                        u.email,
                        u.ativo,
                        u.data_criacao,
                        COUNT(DISTINCT ue.empresa_id) as total_empresas
                    FROM usuarios u
                    LEFT JOIN usuario_empresa ue ON u.id = ue.usuario_id
                    GROUP BY u.id, u.nome, u.email, u.ativo, u.data_criacao
                    ORDER BY u.nome
                """))
                
                usuarios = []
                for row in result:
                    usuarios.append({
                        'id': row[0],
                        'nome': row[1],
                        'email': row[2],
                        'ativo': row[3],
                        'data_criacao': row[4].isoformat() if row[4] else None,
                        'total_empresas': row[5]
                    })
                
                return jsonify(usuarios), 200
                
        except Exception as e:
            logger.error(f"Erro ao listar usuários: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/empresas/<int:empresa_id>/usuarios', methods=['GET'])
    def listar_usuarios_empresa(empresa_id):
        """Lista usuários vinculados a uma empresa"""
        try:
            with engine.begin() as conn:
                result = conn.execute(text("""
                    SELECT 
                        u.id,
                        u.nome,
                        u.email,
                        u.ativo,
                        ue.data_vinculo
                    FROM usuarios u
                    INNER JOIN usuario_empresa ue ON u.id = ue.usuario_id
                    WHERE ue.empresa_id = :empresa_id
                    ORDER BY u.nome
                """), {'empresa_id': empresa_id})
                
                usuarios = []
                for row in result:
                    usuarios.append({
                        'id': row[0],
                        'nome': row[1],
                        'email': row[2],
                        'ativo': row[3],
                        'data_vinculo': row[4].isoformat() if row[4] else None
                    })
                
                return jsonify(usuarios), 200
                
        except Exception as e:
            logger.error(f"Erro ao listar usuários da empresa: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/usuarios/<int:usuario_id>/empresas', methods=['GET'])
    def listar_empresas_usuario(usuario_id):
        """Lista empresas vinculadas a um usuário"""
        try:
            with engine.begin() as conn:
                result = conn.execute(text("""
                    SELECT 
                        e.id,
                        e.cnpj,
                        e.razao_social,
                        e.nome_fantasia,
                        e.ativo,
                        ue.data_vinculo
                    FROM empresas e
                    INNER JOIN usuario_empresa ue ON e.id = ue.empresa_id
                    WHERE ue.usuario_id = :usuario_id
                    ORDER BY e.razao_social
                """), {'usuario_id': usuario_id})
                
                empresas = []
                for row in result:
                    empresas.append({
                        'id': row[0],
                        'cnpj': formatar_cnpj(row[1]),
                        'razao_social': row[2],
                        'nome_fantasia': row[3],
                        'ativo': row[4],
                        'data_vinculo': row[5].isoformat() if row[5] else None
                    })
                
                return jsonify(empresas), 200
                
        except Exception as e:
            logger.error(f"Erro ao listar empresas do usuário: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/empresas/<int:empresa_id>/usuarios/<int:usuario_id>', methods=['POST'])
    def vincular_usuario_empresa(empresa_id, usuario_id):
        """Vincula um usuário a uma empresa"""
        try:
            with engine.begin() as conn:
                # Verificar se já existe o vínculo
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM usuario_empresa
                    WHERE usuario_id = :usuario_id AND empresa_id = :empresa_id
                """), {'usuario_id': usuario_id, 'empresa_id': empresa_id})
                
                if result.fetchone()[0] > 0:
                    return jsonify({'message': 'Vínculo já existe'}), 200
                
                # Criar vínculo
                conn.execute(text("""
                    INSERT INTO usuario_empresa (usuario_id, empresa_id, data_vinculo)
                    VALUES (:usuario_id, :empresa_id, :data_vinculo)
                """), {
                    'usuario_id': usuario_id,
                    'empresa_id': empresa_id,
                    'data_vinculo': datetime.now()
                })
                
                logger.info(f"Usuário {usuario_id} vinculado à empresa {empresa_id}")
                return jsonify({'message': 'Vínculo criado com sucesso'}), 201
                
        except Exception as e:
            logger.error(f"Erro ao vincular usuário: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/empresas/<int:empresa_id>/usuarios/<int:usuario_id>', methods=['DELETE'])
    def desvincular_usuario_empresa(empresa_id, usuario_id):
        """Remove vínculo entre usuário e empresa"""
        try:
            with engine.begin() as conn:
                result = conn.execute(text("""
                    DELETE FROM usuario_empresa
                    WHERE usuario_id = :usuario_id AND empresa_id = :empresa_id
                """), {'usuario_id': usuario_id, 'empresa_id': empresa_id})
                
                if result.rowcount == 0:
                    return jsonify({'error': 'Vínculo não encontrado'}), 404
                
                logger.info(f"Usuário {usuario_id} desvinculado da empresa {empresa_id}")
                return jsonify({'message': 'Vínculo removido com sucesso'}), 200
                
        except Exception as e:
            logger.error(f"Erro ao desvincular usuário: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/empresas/<int:empresa_id>', methods=['PUT'])
    def atualizar_empresa(empresa_id):
        """Atualiza dados de uma empresa"""
        try:
            data = request.get_json()
            
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE empresas
                    SET razao_social = :razao_social,
                        nome_fantasia = :nome_fantasia,
                        inscricao_estadual = :inscricao_estadual,
                        ativo = :ativo,
                        data_atualizacao = :data_atualizacao
                    WHERE id = :empresa_id
                """), {
                    'empresa_id': empresa_id,
                    'razao_social': data.get('razao_social'),
                    'nome_fantasia': data.get('nome_fantasia'),
                    'inscricao_estadual': data.get('inscricao_estadual'),
                    'ativo': data.get('ativo', True),
                    'data_atualizacao': datetime.now()
                })
                
                logger.info(f"Empresa {empresa_id} atualizada")
                return jsonify({'message': 'Empresa atualizada com sucesso'}), 200
                
        except Exception as e:
            logger.error(f"Erro ao atualizar empresa: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500


def formatar_cnpj(cnpj):
    """Formata CNPJ para exibição"""
    if not cnpj or len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
