"""
Script de teste rápido para verificar se o ETL está gravando no banco.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from etl_service.database import SessionLocal, init_database
from etl_service.models import NFe


def verificar_banco():
    """Verifica a conexão e estado do banco."""
    print("\n" + "="*80)
    print("VERIFICAÇÃO DO BANCO DE DADOS")
    print("="*80 + "\n")
    
    try:
        # Testar conexão
        print("1. Testando conexão com banco...")
        session = SessionLocal()
        
        # Contar registros
        total_nfes = session.query(NFe).count()
        print(f"   ✓ Conexão OK - Total de NF-es: {total_nfes}")
        
        # Listar últimas 5 notas
        if total_nfes > 0:
            print("\n2. Últimas 5 NF-es no banco:")
            ultimas = session.query(NFe).order_by(NFe.data_processamento_etl.desc()).limit(5).all()
            for nfe in ultimas:
                print(f"   - Chave: {nfe.chave_acesso[:20]}...")
                print(f"     Número: {nfe.numero_nota} | Série: {nfe.serie}")
                print(f"     Emitente: {nfe.emitente_razao_social}")
                print(f"     Valor: R$ {nfe.valor_total_nota:,.2f}")
                print()
        
        session.close()
        
        print("✓ Verificação concluída com sucesso!\n")
        return True
        
    except Exception as e:
        print(f"✗ Erro ao conectar: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def teste_rapido():
    """Executa um teste rápido de gravação."""
    print("\n" + "="*80)
    print("TESTE DE GRAVAÇÃO NO BANCO")
    print("="*80 + "\n")
    
    from etl_service.extractor import XMLExtractor
    from etl_service.transformer import DataTransformer
    from etl_service.loader import DataLoader
    import os
    import glob
    
    # Perguntar pelo arquivo
    arquivo = input("Digite o caminho de um arquivo XML de teste (ou deixe vazio para pular): ").strip()
    
    if not arquivo:
        print("Teste de gravação pulado.\n")
        return
    
    # Verificar se existe
    if not os.path.exists(arquivo):
        print(f"✗ Caminho não encontrado: {arquivo}\n")
        return
    
    # Se for um diretório, listar XMLs disponíveis
    if os.path.isdir(arquivo):
        print(f"\n⚠ O caminho informado é um DIRETÓRIO, não um arquivo!")
        print(f"\nBuscando arquivos XML em: {arquivo}\n")
        
        # Buscar XMLs
        xmls = glob.glob(os.path.join(arquivo, "*.xml"))
        
        if not xmls:
            print("✗ Nenhum arquivo XML encontrado neste diretório.\n")
            return
        
        print(f"Encontrados {len(xmls)} arquivo(s) XML:")
        for i, xml_file in enumerate(xmls[:10], 1):  # Mostrar até 10
            print(f"  {i}. {os.path.basename(xml_file)}")
        
        if len(xmls) > 10:
            print(f"  ... e mais {len(xmls) - 10} arquivo(s)")
        
        print("\nEscolha uma opção:")
        print("  1. Processar o primeiro arquivo")
        print("  2. Processar todos os arquivos do diretório")
        print("  3. Cancelar")
        
        opcao = input("\nOpção: ").strip()
        
        if opcao == "1":
            arquivo = xmls[0]
            print(f"\nProcessando: {os.path.basename(arquivo)}\n")
        elif opcao == "2":
            print(f"\nPara processar todos, use:")
            print(f'  python run_etl.py --diretorio "{arquivo}"\n')
            return
        else:
            print("Teste cancelado.\n")
            return
    
    try:
        print("\n1. Extraindo dados do XML...")
        extractor = XMLExtractor()
        dados = extractor.extrair_nfe(arquivo)
        print(f"   ✓ Chave: {dados['identificacao']['chave_acesso']}")
        
        print("\n2. Transformando dados...")
        transformer = DataTransformer()
        nfe = transformer.transformar_nfe(dados)
        print(f"   ✓ NF-e: {nfe.numero_nota}/{nfe.serie}")
        print(f"   ✓ Valor: R$ {nfe.valor_total_nota:,.2f}")
        
        # Salvar chave de acesso antes de gravar (pois o objeto será desvinculado da sessão)
        chave_acesso = nfe.chave_acesso
        numero_nota = nfe.numero_nota
        serie = nfe.serie
        
        print("\n3. Gravando no banco...")
        loader = DataLoader()
        resultado = loader.carregar_nfe(nfe, arquivo)
        
        if resultado['sucesso']:
            print(f"   ✓ Gravado com sucesso!")
        elif resultado['duplicado']:
            print(f"   ⚠ Nota já existe no banco")
        else:
            print(f"   ✗ Erro: {resultado['mensagem']}")
        
        print("\n4. Verificando no banco...")
        session = SessionLocal()
        nfe_banco = session.query(NFe).filter(NFe.chave_acesso == chave_acesso).first()
        
        if nfe_banco:
            print(f"   ✓ Confirmado! NF-e encontrada no banco:")
            print(f"     ID: {nfe_banco.id}")
            print(f"     Chave: {nfe_banco.chave_acesso}")
            print(f"     Número: {nfe_banco.numero_nota}/{nfe_banco.serie}")
            print(f"     Emitente: {nfe_banco.emitente_razao_social}")
            print(f"     Destinatário: {nfe_banco.destinatario_razao_social}")
            print(f"     Valor: R$ {nfe_banco.valor_total_nota:,.2f}")
            print(f"     Itens: {len(nfe_banco.itens)}")
        else:
            print(f"   ✗ NF-e NÃO encontrada no banco!")
            print(f"     Chave buscada: {chave_acesso}")
        
        session.close()
        print("\n✓ Teste concluído!\n")
        
    except Exception as e:
        print(f"\n✗ Erro no teste: {e}\n")
        import traceback
        traceback.print_exc()


def main():
    print("\n╔" + "═"*78 + "╗")
    print("║" + " "*25 + "TESTE DO SERVIÇO ETL" + " "*34 + "║")
    print("╚" + "═"*78 + "╝")
    
    # Verificar banco
    if not verificar_banco():
        print("\n⚠ Execute primeiro: python run_etl.py --init-db\n")
        return 1
    
    # Teste de gravação
    teste_rapido()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
