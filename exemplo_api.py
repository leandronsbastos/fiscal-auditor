"""
Exemplo completo de uso da API do Fiscal Auditor.
Demonstra todas as operações CRUD com usuários e empresas.
"""
import requests
import json
from datetime import datetime

# Configuração
BASE_URL = "http://localhost:8000"

class FiscalAuditorAPI:
    """Cliente Python para a API do Fiscal Auditor."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    # ========== USUÁRIOS ==========
    
    def criar_usuario(self, nome: str, email: str, senha: str):
        """Cria um novo usuário."""
        data = {"nome": nome, "email": email, "senha": senha}
        response = requests.post(f"{self.base_url}/api/usuarios", json=data)
        response.raise_for_status()
        return response.json()
    
    def listar_usuarios(self):
        """Lista todos os usuários."""
        response = requests.get(f"{self.base_url}/api/usuarios")
        response.raise_for_status()
        return response.json()
    
    def obter_usuario(self, usuario_id: int):
        """Obtém um usuário específico."""
        response = requests.get(f"{self.base_url}/api/usuarios/{usuario_id}")
        response.raise_for_status()
        return response.json()
    
    def atualizar_usuario(self, usuario_id: int, **kwargs):
        """Atualiza dados do usuário."""
        response = requests.put(
            f"{self.base_url}/api/usuarios/{usuario_id}",
            json=kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def deletar_usuario(self, usuario_id: int):
        """Deleta um usuário."""
        response = requests.delete(f"{self.base_url}/api/usuarios/{usuario_id}")
        response.raise_for_status()
        return response.json()
    
    # ========== EMPRESAS ==========
    
    def criar_empresa(self, cnpj: str, razao_social: str, **kwargs):
        """Cria uma nova empresa."""
        data = {"cnpj": cnpj, "razao_social": razao_social, **kwargs}
        response = requests.post(f"{self.base_url}/api/empresas", json=data)
        response.raise_for_status()
        return response.json()
    
    def listar_empresas(self):
        """Lista todas as empresas."""
        response = requests.get(f"{self.base_url}/api/empresas")
        response.raise_for_status()
        return response.json()
    
    def obter_empresa(self, empresa_id: int):
        """Obtém uma empresa específica."""
        response = requests.get(f"{self.base_url}/api/empresas/{empresa_id}")
        response.raise_for_status()
        return response.json()
    
    def atualizar_empresa(self, empresa_id: int, **kwargs):
        """Atualiza dados da empresa."""
        response = requests.put(
            f"{self.base_url}/api/empresas/{empresa_id}",
            json=kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def deletar_empresa(self, empresa_id: int):
        """Deleta uma empresa."""
        response = requests.delete(f"{self.base_url}/api/empresas/{empresa_id}")
        response.raise_for_status()
        return response.json()
    
    # ========== VÍNCULOS ==========
    
    def vincular_usuario_empresa(self, usuario_id: int, empresa_id: int):
        """Vincula um usuário a uma empresa."""
        data = {"usuario_id": usuario_id, "empresa_id": empresa_id}
        response = requests.post(f"{self.base_url}/api/vinculos", json=data)
        response.raise_for_status()
        return response.json()
    
    def desvincular_usuario_empresa(self, usuario_id: int, empresa_id: int):
        """Remove vínculo entre usuário e empresa."""
        response = requests.delete(
            f"{self.base_url}/api/vinculos/{usuario_id}/{empresa_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def listar_empresas_usuario(self, usuario_id: int):
        """Lista empresas vinculadas ao usuário."""
        response = requests.get(f"{self.base_url}/api/usuarios/{usuario_id}/empresas")
        response.raise_for_status()
        return response.json()
    
    def listar_usuarios_empresa(self, empresa_id: int):
        """Lista usuários vinculados à empresa."""
        response = requests.get(f"{self.base_url}/api/empresas/{empresa_id}/usuarios")
        response.raise_for_status()
        return response.json()
    
    # ========== ANÁLISES ==========
    
    def listar_analises_empresa(self, empresa_id: int):
        """Lista análises de uma empresa."""
        response = requests.get(f"{self.base_url}/api/empresas/{empresa_id}/analises")
        response.raise_for_status()
        return response.json()
    
    def obter_analise(self, analise_id: int):
        """Obtém detalhes completos de uma análise."""
        response = requests.get(f"{self.base_url}/api/analises/{analise_id}")
        response.raise_for_status()
        return response.json()
    
    def deletar_analise(self, analise_id: int):
        """Deleta uma análise."""
        response = requests.delete(f"{self.base_url}/api/analises/{analise_id}")
        response.raise_for_status()
        return response.json()


# ========== EXEMPLO DE USO ==========

def exemplo_completo():
    """Demonstra o uso completo da API."""
    
    api = FiscalAuditorAPI()
    
    print("=" * 80)
    print("EXEMPLO COMPLETO - API FISCAL AUDITOR")
    print("=" * 80)
    print()
    
    # 1. Criar usuário
    print("1. Criando usuário...")
    try:
        usuario = api.criar_usuario(
            nome="Maria Silva",
            email=f"maria.silva.{datetime.now().timestamp()}@empresa.com",
            senha="senha_segura_123"
        )
        print(f"   ✓ Usuário criado: {usuario['nome']} (ID: {usuario['id']})")
        usuario_id = usuario['id']
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        return
    
    print()
    
    # 2. Criar empresas
    print("2. Criando empresas...")
    empresas_ids = []
    
    empresas_data = [
        {
            "cnpj": "11111111000191",
            "razao_social": "Tech Solutions LTDA",
            "nome_fantasia": "Tech Solutions",
            "cidade": "São Paulo",
            "estado": "SP"
        },
        {
            "cnpj": "22222222000192",
            "razao_social": "Inovação Digital ME",
            "nome_fantasia": "Inovação Digital",
            "cidade": "Rio de Janeiro",
            "estado": "RJ"
        }
    ]
    
    for emp_data in empresas_data:
        try:
            empresa = api.criar_empresa(**emp_data)
            print(f"   ✓ Empresa criada: {empresa['razao_social']} (ID: {empresa['id']})")
            empresas_ids.append(empresa['id'])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                # CNPJ já existe, buscar
                empresas = api.listar_empresas()
                empresa = [e for e in empresas if e['cnpj'] == emp_data['cnpj']][0]
                print(f"   ℹ Empresa já existe: {empresa['razao_social']} (ID: {empresa['id']})")
                empresas_ids.append(empresa['id'])
            else:
                print(f"   ✗ Erro: {e}")
    
    print()
    
    # 3. Vincular usuário às empresas
    print("3. Vinculando usuário às empresas...")
    for empresa_id in empresas_ids:
        try:
            api.vincular_usuario_empresa(usuario_id, empresa_id)
            print(f"   ✓ Vínculo criado: Usuário {usuario_id} → Empresa {empresa_id}")
        except Exception as e:
            print(f"   ✗ Erro: {e}")
    
    print()
    
    # 4. Listar empresas do usuário
    print("4. Listando empresas do usuário...")
    try:
        empresas = api.listar_empresas_usuario(usuario_id)
        print(f"   ✓ Usuário tem acesso a {len(empresas)} empresa(s):")
        for emp in empresas:
            print(f"      - {emp['razao_social']} (CNPJ: {emp['cnpj']})")
    except Exception as e:
        print(f"   ✗ Erro: {e}")
    
    print()
    
    # 5. Atualizar dados do usuário
    print("5. Atualizando dados do usuário...")
    try:
        usuario = api.atualizar_usuario(
            usuario_id,
            nome="Maria Silva Santos"
        )
        print(f"   ✓ Nome atualizado para: {usuario['nome']}")
    except Exception as e:
        print(f"   ✗ Erro: {e}")
    
    print()
    
    # 6. Atualizar dados da empresa
    print("6. Atualizando dados da primeira empresa...")
    try:
        empresa = api.atualizar_empresa(
            empresas_ids[0],
            telefone="(11) 98765-4321",
            email="contato@techsolutions.com.br"
        )
        print(f"   ✓ Empresa atualizada:")
        print(f"      Telefone: {empresa.get('telefone', 'N/A')}")
        print(f"      Email: {empresa.get('email', 'N/A')}")
    except Exception as e:
        print(f"   ✗ Erro: {e}")
    
    print()
    
    # 7. Listar todas as análises de cada empresa
    print("7. Consultando análises das empresas...")
    for empresa_id in empresas_ids:
        try:
            analises = api.listar_analises_empresa(empresa_id)
            empresa = api.obter_empresa(empresa_id)
            print(f"   Empresa: {empresa['razao_social']}")
            print(f"   ✓ Análises encontradas: {len(analises)}")
            
            if analises:
                for analise in analises[:3]:  # Mostrar até 3 análises
                    print(f"      - Período: {analise['periodo']}")
                    print(f"        Documentos: {analise['total_documentos']}")
                    print(f"        ICMS Saldo: R$ {analise['icms_saldo']}")
        except Exception as e:
            print(f"   ✗ Erro: {e}")
    
    print()
    
    # 8. Listar todos os usuários
    print("8. Listando todos os usuários do sistema...")
    try:
        usuarios = api.listar_usuarios()
        print(f"   ✓ Total de usuários: {len(usuarios)}")
        for usr in usuarios[-3:]:  # Mostrar últimos 3
            print(f"      - {usr['nome']} ({usr['email']})")
            print(f"        Empresas vinculadas: {len(usr.get('empresas', []))}")
    except Exception as e:
        print(f"   ✗ Erro: {e}")
    
    print()
    
    # 9. Desvincular usuário de uma empresa
    print("9. Desvinculando usuário da segunda empresa...")
    if len(empresas_ids) > 1:
        try:
            api.desvincular_usuario_empresa(usuario_id, empresas_ids[1])
            print(f"   ✓ Vínculo removido")
            
            # Verificar
            empresas = api.listar_empresas_usuario(usuario_id)
            print(f"   Empresas restantes: {len(empresas)}")
        except Exception as e:
            print(f"   ✗ Erro: {e}")
    
    print()
    print("=" * 80)
    print("EXEMPLO CONCLUÍDO!")
    print("=" * 80)
    print()
    print("Recursos criados:")
    print(f"  - Usuário ID: {usuario_id}")
    print(f"  - Empresas IDs: {', '.join(map(str, empresas_ids))}")
    print()
    print("Acesse http://localhost:8000/docs para testar mais endpoints!")
    print()


if __name__ == "__main__":
    print("\n🔧 Certifique-se de que:")
    print("  1. O servidor está rodando (python app.py)")
    print("  2. O PostgreSQL está ativo")
    print("  3. O banco foi inicializado (python init_db.py)")
    print()
    
    resposta = input("Deseja executar o exemplo? (s/n): ")
    if resposta.lower() == 's':
        print()
        exemplo_completo()
    else:
        print("\nExemplo cancelado.")
