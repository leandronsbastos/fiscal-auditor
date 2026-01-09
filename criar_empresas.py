#!/usr/bin/env python
"""Script para criar empresas faltantes no sistema."""

from fiscal_auditor.database import SessionLocal
from fiscal_auditor.db_models import Empresa, Usuario

def criar_empresas():
    session = SessionLocal()
    
    try:
        # Buscar usuário existente
        usuario = session.query(Usuario).first()
        if not usuario:
            print("❌ Nenhum usuário encontrado. Crie um usuário primeiro.")
            return
        
        # Empresas a serem criadas (baseado nos CNPJs do datalake)
        empresas_novas = [
            {
                'cnpj': '22569775000115',
                'razao_social': 'Empresa Principal Ltda',
                'nome_fantasia': 'Empresa Principal',
                'inscricao_estadual': '123456789'
            },
            {
                'cnpj': '50283139000168',
                'razao_social': 'Fornecedor XYZ Ltda',
                'nome_fantasia': 'Fornecedor XYZ',
                'inscricao_estadual': '987654321'
            },
            {
                'cnpj': '49810369000159',
                'razao_social': 'Cliente ABC Ltda',
                'nome_fantasia': 'Cliente ABC',
                'inscricao_estadual': '555666777'
            }
        ]
        
        empresas_criadas = []
        
        for dados in empresas_novas:
            # Verificar se já existe
            existe = session.query(Empresa).filter_by(cnpj=dados['cnpj']).first()
            if existe:
                print(f"⚠️  Empresa {dados['cnpj']} já existe (ID: {existe.id})")
                continue
            
            # Criar nova empresa
            empresa = Empresa(
                cnpj=dados['cnpj'],
                razao_social=dados['razao_social'],
                nome_fantasia=dados['nome_fantasia'],
                inscricao_estadual=dados['inscricao_estadual']
            )
            
            # Associar ao usuário
            empresa.usuarios.append(usuario)
            
            session.add(empresa)
            empresas_criadas.append(empresa)
        
        # Commit das mudanças
        session.commit()
        
        if empresas_criadas:
            print(f"\n✅ {len(empresas_criadas)} empresa(s) criada(s) com sucesso:\n")
            for emp in empresas_criadas:
                print(f"   ID {emp.id}: {emp.cnpj} - {emp.razao_social}")
        else:
            print("\n✓ Todas as empresas já existem no sistema.")
        
        # Mostrar resumo
        print(f"\n📊 Resumo:")
        todas_empresas = session.query(Empresa).all()
        print(f"   Total de empresas: {len(todas_empresas)}")
        for emp in todas_empresas:
            print(f"   - ID {emp.id}: {emp.cnpj} - {emp.razao_social}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erro ao criar empresas: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    criar_empresas()
