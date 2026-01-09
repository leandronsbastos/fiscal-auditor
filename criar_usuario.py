"""
Script para criar o primeiro usuário do sistema.
"""
from fiscal_auditor.database import SessionLocal
from fiscal_auditor import crud, schemas

def criar_primeiro_usuario():
    """Cria o primeiro usuário administrativo."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("CRIAR PRIMEIRO USUÁRIO - FISCAL AUDITOR")
        print("=" * 80)
        print()
        
        nome = input("Nome completo: ")
        email = input("E-mail: ")
        senha = input("Senha: ")
        
        print()
        print("Criando usuário...")
        
        # Verificar se email já existe
        usuario_existente = crud.obter_usuario_por_email(db, email)
        if usuario_existente:
            print(f"❌ Erro: Email '{email}' já está cadastrado!")
            return
        
        # Criar usuário
        usuario_data = schemas.UsuarioCreate(
            nome=nome,
            email=email,
            senha=senha
        )
        
        usuario = crud.criar_usuario(db, usuario_data)
        
        print()
        print("✅ Usuário criado com sucesso!")
        print()
        print(f"ID: {usuario.id}")
        print(f"Nome: {usuario.nome}")
        print(f"Email: {usuario.email}")
        print(f"Ativo: {'Sim' if usuario.ativo else 'Não'}")
        print()
        print("⚠️  IMPORTANTE: Vincule este usuário a uma empresa para ele poder fazer login!")
        print()
        print("Para vincular, use:")
        print(f"  python vincular_usuario_empresa.py {usuario.id} <empresa_id>")
        print()
        print("Ou pela API:")
        print(f'''  curl -X POST "http://localhost:8000/api/vinculos" \\
       -H "Content-Type: application/json" \\
       -d '{{"usuario_id": {usuario.id}, "empresa_id": 1}}'
        ''')
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    criar_primeiro_usuario()
