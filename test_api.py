"""
Script de teste para verificar a API do banco de dados.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def testar_api():
    """Testa os endpoints da API."""
    
    print("=" * 80)
    print("TESTE DA API - FISCAL AUDITOR")
    print("=" * 80)
    print()
    
    # 1. Criar Usuário
    print("1. Criando usuário...")
    usuario_data = {
        "nome": "Teste Usuario",
        "email": f"teste{requests.get(f'{BASE_URL}/').status_code}@exemplo.com",
        "senha": "senha123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/usuarios", json=usuario_data)
        if response.status_code == 200:
            usuario = response.json()
            usuario_id = usuario['id']
            print(f"   ✓ Usuário criado: ID {usuario_id} - {usuario['nome']}")
        else:
            print(f"   ✗ Erro: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        return
    
    print()
    
    # 2. Criar Empresa
    print("2. Criando empresa...")
    empresa_data = {
        "cnpj": "12345678000190",
        "razao_social": "Empresa Teste LTDA",
        "nome_fantasia": "Empresa Teste"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/empresas", json=empresa_data)
        if response.status_code == 200:
            empresa = response.json()
            empresa_id = empresa['id']
            print(f"   ✓ Empresa criada: ID {empresa_id} - {empresa['razao_social']}")
        elif response.status_code == 400:
            # CNPJ já existe, buscar empresa
            response = requests.get(f"{BASE_URL}/api/empresas")
            empresas = response.json()
            empresa = [e for e in empresas if e['cnpj'] == empresa_data['cnpj']][0]
            empresa_id = empresa['id']
            print(f"   ℹ Empresa já existente: ID {empresa_id} - {empresa['razao_social']}")
        else:
            print(f"   ✗ Erro: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        return
    
    print()
    
    # 3. Vincular Usuário à Empresa
    print("3. Vinculando usuário à empresa...")
    vinculo_data = {
        "usuario_id": usuario_id,
        "empresa_id": empresa_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/vinculos", json=vinculo_data)
        if response.status_code == 200:
            print(f"   ✓ Vínculo criado com sucesso")
        else:
            print(f"   ✗ Erro: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ✗ Erro: {e}")
    
    print()
    
    # 4. Listar Empresas do Usuário
    print("4. Listando empresas do usuário...")
    try:
        response = requests.get(f"{BASE_URL}/api/usuarios/{usuario_id}/empresas")
        if response.status_code == 200:
            empresas = response.json()
            print(f"   ✓ Empresas encontradas: {len(empresas)}")
            for emp in empresas:
                print(f"      - {emp['razao_social']} (CNPJ: {emp['cnpj']})")
        else:
            print(f"   ✗ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Erro: {e}")
    
    print()
    
    # 5. Listar Usuários da Empresa
    print("5. Listando usuários da empresa...")
    try:
        response = requests.get(f"{BASE_URL}/api/empresas/{empresa_id}/usuarios")
        if response.status_code == 200:
            usuarios = response.json()
            print(f"   ✓ Usuários encontrados: {len(usuarios)}")
            for usr in usuarios:
                print(f"      - {usr['nome']} ({usr['email']})")
        else:
            print(f"   ✗ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Erro: {e}")
    
    print()
    
    # 6. Atualizar Usuário
    print("6. Atualizando usuário...")
    update_data = {
        "nome": "Teste Usuario Atualizado"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/api/usuarios/{usuario_id}", json=update_data)
        if response.status_code == 200:
            usuario = response.json()
            print(f"   ✓ Usuário atualizado: {usuario['nome']}")
        else:
            print(f"   ✗ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Erro: {e}")
    
    print()
    
    # 7. Listar Análises da Empresa
    print("7. Listando análises da empresa...")
    try:
        response = requests.get(f"{BASE_URL}/api/empresas/{empresa_id}/analises")
        if response.status_code == 200:
            analises = response.json()
            print(f"   ✓ Análises encontradas: {len(analises)}")
            for analise in analises:
                print(f"      - Período: {analise['periodo']} - Documentos: {analise['total_documentos']}")
        else:
            print(f"   ✗ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Erro: {e}")
    
    print()
    print("=" * 80)
    print("TESTE CONCLUÍDO!")
    print("=" * 80)
    print()
    print("IDs criados para referência:")
    print(f"  Usuario ID: {usuario_id}")
    print(f"  Empresa ID: {empresa_id}")
    print()

if __name__ == "__main__":
    print("\nCertifique-se de que:")
    print("  1. O servidor está rodando (python app.py)")
    print("  2. O PostgreSQL está ativo")
    print("  3. O banco foi inicializado (python init_db.py)")
    print()
    input("Pressione ENTER para iniciar os testes...")
    print()
    
    testar_api()
