#!/usr/bin/env python
"""
Exemplo de uso do sistema Fiscal Auditor.
Este script demonstra como processar XMLs de documentos fiscais,
validar, calcular apuração e gerar relatórios.
"""
import os
import sys
from fiscal_auditor import (
    XMLReader,
    ValidadorTributario,
    ApuradorTributario,
    GeradorRelatorios
)


def main():
    """Exemplo completo de uso do sistema."""
    print("=" * 80)
    print("FISCAL AUDITOR - Sistema de Auditoria e Apuração Tributária")
    print("=" * 80)
    print()

    # Configuração
    cnpj_empresa = "12345678000190"
    periodo = "01/2024"
    
    # Diretório com os XMLs de teste
    diretorio_xmls = os.path.join(os.path.dirname(__file__), "tests", "fixtures")
    
    print(f"CNPJ da Empresa: {cnpj_empresa}")
    print(f"Período de Apuração: {periodo}")
    print(f"Diretório dos XMLs: {diretorio_xmls}")
    print()

    # Inicializa componentes
    print("Inicializando componentes...")
    reader = XMLReader(cnpj_empresa)
    validador = ValidadorTributario()
    apurador = ApuradorTributario()
    gerador = GeradorRelatorios()
    print("✓ Componentes inicializados")
    print()

    # Processa XMLs
    print("Processando documentos fiscais...")
    documentos = []
    validacoes = []
    
    arquivos_xml = [
        os.path.join(diretorio_xmls, "nfe_entrada.xml"),
        os.path.join(diretorio_xmls, "nfe_saida.xml")
    ]
    
    for caminho_xml in arquivos_xml:
        if not os.path.exists(caminho_xml):
            print(f"⚠ Arquivo não encontrado: {caminho_xml}")
            continue
            
        print(f"  Lendo: {os.path.basename(caminho_xml)}")
        
        try:
            # Lê XML
            doc = reader.ler_xml(caminho_xml)
            documentos.append(doc)
            
            print(f"    Tipo: {doc.tipo.value}")
            print(f"    Movimento: {doc.tipo_movimento.value}")
            print(f"    Número: {doc.numero}")
            print(f"    Valor Total: R$ {doc.valor_total}")
            print(f"    Itens: {len(doc.items)}")
            
            # Valida documento
            validacao = validador.validar_documento(doc)
            validacoes.append(validacao)
            
            if validacao.valido:
                print(f"    ✓ Validação: OK")
            else:
                print(f"    ⚠ Validação: Problemas encontrados")
                for msg in validacao.mensagens[:3]:  # Mostra até 3 mensagens
                    print(f"      - {msg}")
            
            print(f"    Créditos aproveitáveis: {len(validacao.creditos_aproveitaveis)}")
            print(f"    Créditos indevidos: {len(validacao.creditos_indevidos)}")
            print(f"    Créditos glosáveis: {len(validacao.creditos_glosaveis)}")
            
            # Adiciona para apuração
            apurador.adicionar_documento(doc)
            print(f"    ✓ Adicionado para apuração")
            
        except Exception as e:
            print(f"    ✗ Erro ao processar: {str(e)}")
            
        print()

    if not documentos:
        print("Nenhum documento foi processado.")
        sys.exit(1)

    # Realiza apuração
    print("Realizando apuração de tributos...")
    mapa = apurador.apurar(periodo)
    print(f"✓ Apuração concluída para {len(mapa.apuracoes)} tributos")
    print()

    # Exibe resultado da apuração
    print("RESULTADO DA APURAÇÃO:")
    print("-" * 80)
    for apuracao in mapa.apuracoes:
        print(f"\n{apuracao.tipo.value}:")
        print(f"  Débitos (Saídas):  R$ {apuracao.debitos:>12}")
        print(f"  Créditos (Entradas): R$ {apuracao.creditos:>12}")
        print(f"  {'─' * 40}")
        if apuracao.saldo >= 0:
            print(f"  Saldo a Recolher:   R$ {apuracao.saldo:>12}")
        else:
            print(f"  Saldo Credor:       R$ {abs(apuracao.saldo):>12}")
    print()

    # Gera relatórios
    print("Gerando relatórios...")
    
    # Relatório de entradas
    demo_entradas = gerador.gerar_demonstrativo_entradas(documentos)
    print(f"  ✓ Demonstrativo de Entradas: {demo_entradas['quantidade_documentos']} documento(s)")
    
    # Relatório de saídas
    demo_saidas = gerador.gerar_demonstrativo_saidas(documentos)
    print(f"  ✓ Demonstrativo de Saídas: {demo_saidas['quantidade_documentos']} documento(s)")
    
    # Mapa de apuração
    relatorio_mapa = gerador.gerar_mapa_apuracao(mapa)
    print(f"  ✓ Mapa de Apuração: {len(relatorio_mapa['apuracoes'])} tributo(s)")
    
    # Relatório de validação
    relatorio_validacao = gerador.gerar_relatorio_validacao(validacoes)
    print(f"  ✓ Relatório de Validação: {relatorio_validacao['total_validacoes']} validação(ões)")
    
    # Relatório completo
    relatorio_completo = gerador.gerar_relatorio_completo(documentos, mapa, validacoes)
    print(f"  ✓ Relatório Completo gerado")
    print()

    # Exporta para JSON
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    print("Exportando relatórios em JSON...")
    
    arquivos_gerados = []
    
    arquivo = os.path.join(output_dir, f"demonstrativo_entradas_{periodo.replace('/', '_')}.json")
    gerador.exportar_json(demo_entradas, arquivo)
    arquivos_gerados.append(arquivo)
    print(f"  ✓ {os.path.basename(arquivo)}")
    
    arquivo = os.path.join(output_dir, f"demonstrativo_saidas_{periodo.replace('/', '_')}.json")
    gerador.exportar_json(demo_saidas, arquivo)
    arquivos_gerados.append(arquivo)
    print(f"  ✓ {os.path.basename(arquivo)}")
    
    arquivo = os.path.join(output_dir, f"mapa_apuracao_{periodo.replace('/', '_')}.json")
    gerador.exportar_json(relatorio_mapa, arquivo)
    arquivos_gerados.append(arquivo)
    print(f"  ✓ {os.path.basename(arquivo)}")
    
    arquivo = os.path.join(output_dir, f"relatorio_validacao_{periodo.replace('/', '_')}.json")
    gerador.exportar_json(relatorio_validacao, arquivo)
    arquivos_gerados.append(arquivo)
    print(f"  ✓ {os.path.basename(arquivo)}")
    
    arquivo = os.path.join(output_dir, f"relatorio_completo_{periodo.replace('/', '_')}.json")
    gerador.exportar_json(relatorio_completo, arquivo)
    arquivos_gerados.append(arquivo)
    print(f"  ✓ {os.path.basename(arquivo)}")
    
    print()
    print("=" * 80)
    print("PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
    print("=" * 80)
    print()
    print(f"Total de documentos processados: {len(documentos)}")
    print(f"Relatórios gerados: {len(arquivos_gerados)}")
    print(f"Diretório de saída: {output_dir}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
