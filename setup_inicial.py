"""
Script completo para setup inicial: criar usuário e empresa, e vinculá-los.
"""
from fiscal_auditor.database import SessionLocal
from fiscal_auditor import crud, schemas

def setup_inicial():
    """Setup completo: criar usuário, empresa e vincular."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("SETUP INICIAL - FISCAL AUDITOR")
        print("=" * 80)
        print()
        
        # 1. Criar Usuário
        print("📝 CRIAR USUÁRIO")
        print("-" * 80)
        nome = input("Nome completo: ")
        email = input("E-mail: ")
        senha = input("Senha: ")
        
        # Verificar se email já existe
        usuario_existente = crud.obter_usuario_por_email(db, email)
        if usuario_existente:
            print(f"\n⚠️  Usuário com email '{email}' já existe (ID: {usuario_existente.id})")
            usuario = usuario_existente
        else:
            usuario_data = schemas.UsuarioCreate(nome=nome, email=email, senha=senha)
            usuario = crud.criar_usuario(db, usuario_data)
            print(f"\n✅ Usuário criado: {usuario.nome} (ID: {usuario.id})")
        
        print()
        
        # 2. Criar Empresa
        print("🏢 CRIAR EMPRESA")
        print("-" * 80)
        cnpj = input("CNPJ (apenas números): ")
        razao_social = input("Razão Social: ")
        nome_fantasia = input("Nome Fantasia (opcional): ")
        
        # Verificar se CNPJ já existe
        empresa_existente = crud.obter_empresa_por_cnpj(db, cnpj)
        if empresa_existente:
            print(f"\n⚠️  Empresa com CNPJ '{cnpj}' já existe (ID: {empresa_existente.id})")
            empresa = empresa_existente
        else:
            empresa_data = schemas.EmpresaCreate(
                cnpj=cnpj,
                razao_social=razao_social,
                nome_fantasia=nome_fantasia if nome_fantasia else None
            )
            empresa = crud.criar_empresa(db, empresa_data)
            print(f"\n✅ Empresa criada: {empresa.razao_social} (ID: {empresa.id})")
        
        print()
        
        # 3. Vincular
        print("🔗 VINCULAR USUÁRIO À EMPRESA")
        print("-" * 80)
        
        # Verificar se já existe vínculo
        empresas_usuario = crud.listar_empresas_usuario(db, usuario.id)
        if empresa.id in [e.id for e in empresas_usuario]:
            print(f"⚠️  Usuário já está vinculado a esta empresa")
        else:
            sucesso = crud.vincular_usuario_empresa(db, usuario.id, empresa.id)
            if sucesso:
                print(f"✅ Vínculo criado com sucesso!")
            else:
                print(f"❌ Erro ao criar vínculo")
        
        print()
        print("=" * 80)
        print("SETUP CONCLUÍDO!")
        print("=" * 80)
        print()
        print("📊 Resumo:")
        print(f"  Usuário: {usuario.nome} ({usuario.email})")
        print(f"  Empresa: {empresa.razao_social} (CNPJ: {empresa.cnpj})")
        print()
        print("🚀 Próximos passos:")
        print("  1. Inicie o servidor: python app.py")
        print("  2. Acesse: http://localhost:8000/login")
        print(f"  3. Faça login com: {usuario.email}")
        print()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    setup_inicial()
