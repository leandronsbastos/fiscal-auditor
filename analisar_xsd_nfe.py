"""
Script para analisar o XSD da NF-e e gerar mapeamento completo de campos.

Este script lê o arquivo leiauteNFe_v4.00.xsd e extrai todos os elementos
para criar um mapeamento completo dos campos da NF-e.
"""
import xml.etree.ElementTree as ET
from collections import defaultdict
import json

def analisar_xsd(arquivo_xsd):
    """Analisa o XSD e extrai estrutura de campos."""
    
    tree = ET.parse(arquivo_xsd)
    root = tree.getroot()
    
    # Namespace do XSD
    ns = {
        'xs': 'http://www.w3.org/2001/XMLSchema',
        'nfe': 'http://www.portalfiscal.inf.br/nfe'
    }
    
    estrutura = {
        'ide': [],  # Identificação
        'emit': [],  # Emitente
        'dest': [],  # Destinatário
        'det': {  # Detalhes/Itens
            'prod': [],  # Produto
            'imposto': {
                'ICMS': [],
                'IPI': [],
                'II': [],  # Imposto de Importação
                'PIS': [],
                'PISST': [],
                'COFINS': [],
                'COFINSST': [],
                'IBSCBS': []  # Reforma Tributária
            }
        },
        'total': [],  # Totais
        'transp': [],  # Transporte
        'cobr': [],  # Cobrança
        'pag': [],  # Pagamento
        'infAdic': [],  # Informações Adicionais
        'exporta': [],  # Exportação
        'compra': [],  # Compra
        'cana': []  # Cana
    }
    
    # Encontrar complexTypes
    for complex_type in root.findall('.//xs:complexType', ns):
        nome = complex_type.get('name', '')
        
        # Extrair elementos deste complexType
        elementos = []
        for element in complex_type.findall('.//xs:element', ns):
            elem_name = element.get('name', '')
            elem_type = element.get('type', '')
            
            # Pegar documentação
            doc = ''
            doc_elem = element.find('.//xs:documentation', ns)
            if doc_elem is not None and doc_elem.text:
                doc = doc_elem.text.strip()
            
            if elem_name:
                elementos.append({
                    'nome': elem_name,
                    'tipo': elem_type,
                    'documentacao': doc,
                    'minOccurs': element.get('minOccurs', '1'),
                    'maxOccurs': element.get('maxOccurs', '1')
                })
        
        # Mapear para estrutura apropriada
        if nome.startswith('TIde'):
            estrutura['ide'].extend(elementos)
        elif nome.startswith('TEmit'):
            estrutura['emit'].extend(elementos)
        elif nome.startswith('TDest'):
            estrutura['dest'].extend(elementos)
        elif nome.startswith('TProd'):
            estrutura['det']['prod'].extend(elementos)
        elif 'ICMS' in nome:
            estrutura['det']['imposto']['ICMS'].extend(elementos)
        elif 'IPI' in nome:
            estrutura['det']['imposto']['IPI'].extend(elementos)
        elif 'PIS' in nome and 'ST' not in nome:
            estrutura['det']['imposto']['PIS'].extend(elementos)
        elif 'PISST' in nome:
            estrutura['det']['imposto']['PISST'].extend(elementos)
        elif 'COFINS' in nome and 'ST' not in nome:
            estrutura['det']['imposto']['COFINS'].extend(elementos)
        elif 'COFINSST' in nome:
            estrutura['det']['imposto']['COFINSST'].extend(elementos)
        elif 'IBS' in nome or 'CBS' in nome:
            estrutura['det']['imposto']['IBSCBS'].extend(elementos)
        elif nome.startswith('TTotal') or nome.startswith('TICMS'):
            estrutura['total'].extend(elementos)
        elif nome.startswith('TTransp'):
            estrutura['transp'].extend(elementos)
        elif nome.startswith('TCobr'):
            estrutura['cobr'].extend(elementos)
        elif nome.startswith('TPag'):
            estrutura['pag'].extend(elementos)
    
    return estrutura

def contar_campos(estrutura, nivel=''):
    """Conta campos em todos os níveis da estrutura."""
    total = 0
    
    if isinstance(estrutura, list):
        return len(estrutura)
    elif isinstance(estrutura, dict):
        for chave, valor in estrutura.items():
            subtotal = contar_campos(valor, f"{nivel}.{chave}" if nivel else chave)
            if subtotal > 0:
                print(f"{nivel}.{chave}: {subtotal} campos" if nivel else f"{chave}: {subtotal} campos")
            total += subtotal
    
    return total

def gerar_relatorio(estrutura):
    """Gera relatório detalhado da estrutura."""
    
    print("=" * 80)
    print("ANÁLISE DO LAYOUT NF-e v4.00")
    print("=" * 80)
    print()
    
    # Identificação
    print("### IDE (Identificação) ###")
    print(f"Total de campos: {len(estrutura['ide'])}")
    for campo in estrutura['ide'][:10]:  # Primeiros 10
        print(f"  - {campo['nome']}: {campo['documentacao'][:80] if campo['documentacao'] else '(sem doc)'}")
    if len(estrutura['ide']) > 10:
        print(f"  ... e mais {len(estrutura['ide']) - 10} campos")
    print()
    
    # Emitente
    print("### EMIT (Emitente) ###")
    print(f"Total de campos: {len(estrutura['emit'])}")
    print()
    
    # Destinatário
    print("### DEST (Destinatário) ###")
    print(f"Total de campos: {len(estrutura['dest'])}")
    print()
    
    # Produto
    print("### PROD (Produto) ###")
    print(f"Total de campos: {len(estrutura['det']['prod'])}")
    print()
    
    # Impostos
    print("### IMPOSTOS ###")
    for imposto, campos in estrutura['det']['imposto'].items():
        print(f"  {imposto}: {len(campos)} campos")
    print()
    
    # Totais
    print("### TOTAL (Totalizadores) ###")
    print(f"Total de campos: {len(estrutura['total'])}")
    print()
    
    # Transporte
    print("### TRANSP (Transporte) ###")
    print(f"Total de campos: {len(estrutura['transp'])}")
    print()
    
    # Cobrança
    print("### COBR (Cobrança) ###")
    print(f"Total de campos: {len(estrutura['cobr'])}")
    print()
    
    # Pagamento
    print("### PAG (Pagamento) ###")
    print(f"Total de campos: {len(estrutura['pag'])}")
    print()
    
    print("=" * 80)
    total_geral = contar_campos(estrutura)
    print(f"TOTAL GERAL: {total_geral} campos mapeados")
    print("=" * 80)

if __name__ == '__main__':
    print("\nAnalisando XSD da NF-e v4.00...\n")
    
    try:
        estrutura = analisar_xsd('leiauteNFe_v4.00.xsd')
        
        # Salvar em JSON
        with open('estrutura_nfe_completa.json', 'w', encoding='utf-8') as f:
            json.dump(estrutura, f, indent=2, ensure_ascii=False)
        
        print("✓ Estrutura salva em estrutura_nfe_completa.json\n")
        
        # Gerar relatório
        gerar_relatorio(estrutura)
        
    except Exception as e:
        print(f"❌ Erro ao analisar XSD: {e}")
        import traceback
        traceback.print_exc()
