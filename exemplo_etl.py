"""
Exemplos de uso do serviço ETL.

Este arquivo demonstra diferentes formas de utilizar o serviço ETL
para processar arquivos XML de NF-e e NFC-e.
"""
import os
from etl_service.pipeline import ETLPipeline, inicializar_banco
from etl_service.database import SessionLocal
from etl_service.models import NFe, NFeItem


def exemplo_1_inicializar_banco():
    """Exemplo 1: Inicializar o banco de dados."""
    print("=" * 80)
    print("EXEMPLO 1: Inicializando banco de dados")
    print("=" * 80)
    
    inicializar_banco()
    print("✓ Banco inicializado com sucesso!\n")


def exemplo_2_processar_diretorio():
    """Exemplo 2: Processar todos os XMLs de um diretório."""
    print("=" * 80)
    print("EXEMPLO 2: Processando diretório completo")
    print("=" * 80)
    
    # Criar pipeline
    pipeline = ETLPipeline()
    
    # Diretório com XMLs (ajuste para seu caso)
    diretorio = r"C:\XMLs\2024"
    
    # Processar
    stats = pipeline.processar_diretorio(
        diretorio=diretorio,
        tipo_processamento="completo",
        recursivo=True
    )
    
    print(f"\nResultados:")
    print(f"  Total: {stats['total_arquivos']}")
    print(f"  Processados: {stats['processados']}")
    print(f"  Duplicados: {stats['duplicados']}")
    print(f"  Erros: {stats['erros']}")
    print(f"  Tempo: {stats['tempo_total']:.2f}s\n")


def exemplo_3_processar_arquivo_unico():
    """Exemplo 3: Processar um único arquivo XML."""
    print("=" * 80)
    print("EXEMPLO 3: Processando arquivo único")
    print("=" * 80)
    
    pipeline = ETLPipeline()
    
    # Caminho do arquivo (ajuste para seu caso)
    arquivo = r"C:\XMLs\nota_exemplo.xml"
    
    if not os.path.exists(arquivo):
        print(f"Arquivo não encontrado: {arquivo}")
        return
    
    # Processar
    resultado = pipeline.processar_arquivo(arquivo)
    
    if resultado['sucesso']:
        print(f"✓ Arquivo processado com sucesso!")
        print(f"  Chave: {resultado['chave_acesso']}")
    elif resultado['duplicado']:
        print(f"⚠ Arquivo já foi processado anteriormente")
        print(f"  Chave: {resultado['chave_acesso']}")
    else:
        print(f"✗ Erro ao processar arquivo")
        print(f"  Mensagem: {resultado['mensagem']}")
    print()


def exemplo_4_processar_lista_arquivos():
    """Exemplo 4: Processar uma lista específica de arquivos."""
    print("=" * 80)
    print("EXEMPLO 4: Processando lista de arquivos")
    print("=" * 80)
    
    pipeline = ETLPipeline()
    
    # Lista de arquivos (ajuste para seu caso)
    arquivos = [
        r"C:\XMLs\nota1.xml",
        r"C:\XMLs\nota2.xml",
        r"C:\XMLs\nota3.xml",
    ]
    
    # Filtrar arquivos que existem
    arquivos_existentes = [a for a in arquivos if os.path.exists(a)]
    
    if not arquivos_existentes:
        print("Nenhum arquivo encontrado!")
        return
    
    # Processar
    stats = pipeline.processar_arquivos_lista(
        arquivos=arquivos_existentes,
        tipo_processamento="completo"
    )
    
    print(f"\nResultados:")
    print(f"  Processados: {stats['processados']}")
    print(f"  Erros: {stats['erros']}\n")


def exemplo_5_consultar_dados():
    """Exemplo 5: Consultar dados processados."""
    print("=" * 80)
    print("EXEMPLO 5: Consultando dados do datalake")
    print("=" * 80)
    
    session = SessionLocal()
    
    try:
        # Contar total de notas
        total_notas = session.query(NFe).count()
        print(f"\nTotal de NF-es no banco: {total_notas}")
        
        # Últimas 5 notas processadas
        print("\nÚltimas 5 NF-es processadas:")
        ultimas_notas = session.query(NFe).order_by(
            NFe.data_processamento_etl.desc()
        ).limit(5).all()
        
        for nfe in ultimas_notas:
            print(f"\n  Chave: {nfe.chave_acesso}")
            print(f"  Número: {nfe.numero_nota} / Série: {nfe.serie}")
            print(f"  Emitente: {nfe.emitente_razao_social}")
            print(f"  Valor: R$ {nfe.valor_total_nota:,.2f}")
            print(f"  Data: {nfe.data_emissao}")
            print(f"  Itens: {len(nfe.itens)}")
        
        # Buscar por CNPJ
        cnpj_exemplo = "12345678000190"
        notas_cnpj = session.query(NFe).filter(
            NFe.emitente_cnpj == cnpj_exemplo
        ).count()
        
        print(f"\n\nNotas do CNPJ {cnpj_exemplo}: {notas_cnpj}")
        
    finally:
        session.close()
    
    print()


def exemplo_6_estatisticas():
    """Exemplo 6: Gerar estatísticas dos dados."""
    print("=" * 80)
    print("EXEMPLO 6: Estatísticas do datalake")
    print("=" * 80)
    
    session = SessionLocal()
    
    try:
        from sqlalchemy import func
        
        # Estatísticas gerais
        stats = session.query(
            func.count(NFe.id).label('total'),
            func.sum(NFe.valor_total_nota).label('valor_total'),
            func.min(NFe.data_emissao).label('data_inicio'),
            func.max(NFe.data_emissao).label('data_fim')
        ).first()
        
        print(f"\nEstatísticas Gerais:")
        print(f"  Total de NF-es: {stats.total:,}")
        print(f"  Valor Total: R$ {stats.valor_total:,.2f}" if stats.valor_total else "  Valor Total: R$ 0,00")
        print(f"  Período: {stats.data_inicio} a {stats.data_fim}" if stats.data_inicio else "  Período: N/A")
        
        # Total de itens
        total_itens = session.query(NFeItem).count()
        print(f"  Total de Itens: {total_itens:,}")
        
        # Emitentes únicos
        emitentes = session.query(func.count(func.distinct(NFe.emitente_cnpj))).scalar()
        print(f"  Emitentes Únicos: {emitentes:,}")
        
        # Destinatários únicos
        destinatarios = session.query(func.count(func.distinct(NFe.destinatario_cnpj))).scalar()
        print(f"  Destinatários Únicos: {destinatarios:,}")
        
        # Por modelo
        print(f"\nPor Modelo:")
        por_modelo = session.query(
            NFe.modelo,
            func.count(NFe.id).label('quantidade')
        ).group_by(NFe.modelo).all()
        
        for modelo, qtd in por_modelo:
            tipo = "NF-e" if modelo == "55" else "NFC-e" if modelo == "65" else f"Modelo {modelo}"
            print(f"  {tipo}: {qtd:,}")
        
    finally:
        session.close()
    
    print()


def exemplo_7_uso_customizado():
    """Exemplo 7: Uso customizado dos componentes."""
    print("=" * 80)
    print("EXEMPLO 7: Uso customizado dos componentes")
    print("=" * 80)
    
    from etl_service.extractor import XMLExtractor
    from etl_service.transformer import DataTransformer
    from etl_service.loader import DataLoader
    
    # Criar componentes separados
    extractor = XMLExtractor()
    transformer = DataTransformer()
    loader = DataLoader()
    
    # Arquivo de exemplo
    arquivo = r"C:\XMLs\nota_exemplo.xml"
    
    if not os.path.exists(arquivo):
        print(f"Arquivo não encontrado: {arquivo}")
        return
    
    try:
        # 1. Extrair
        print("\n1. Extraindo dados do XML...")
        dados_extraidos = extractor.extrair_nfe(arquivo)
        print(f"   ✓ Chave: {dados_extraidos['identificacao']['chave_acesso']}")
        print(f"   ✓ Itens extraídos: {len(dados_extraidos['itens'])}")
        
        # 2. Transformar
        print("\n2. Transformando dados...")
        nfe = transformer.transformar_nfe(dados_extraidos)
        print(f"   ✓ NF-e: {nfe.numero_nota}/{nfe.serie}")
        print(f"   ✓ Valor: R$ {nfe.valor_total_nota:,.2f}")
        
        # 3. Carregar
        print("\n3. Carregando no banco...")
        resultado = loader.carregar_nfe(nfe, arquivo)
        
        if resultado['sucesso']:
            print(f"   ✓ Carregado com sucesso!")
        elif resultado['duplicado']:
            print(f"   ⚠ Já existe no banco")
        else:
            print(f"   ✗ Erro: {resultado['mensagem']}")
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
    
    print()


def main():
    """Executa todos os exemplos."""
    print("\n" + "=" * 80)
    print(" " * 20 + "EXEMPLOS DE USO DO SERVIÇO ETL")
    print("=" * 80 + "\n")
    
    # Descomentar os exemplos que deseja executar:
    
    # exemplo_1_inicializar_banco()
    # exemplo_2_processar_diretorio()
    # exemplo_3_processar_arquivo_unico()
    # exemplo_4_processar_lista_arquivos()
    # exemplo_5_consultar_dados()
    # exemplo_6_estatisticas()
    # exemplo_7_uso_customizado()
    
    print("\n" + "=" * 80)
    print("Para executar os exemplos, descomente as funções no main()")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
