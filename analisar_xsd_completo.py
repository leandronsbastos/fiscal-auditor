"""
Script melhorado para analisar o XSD da NF-e v4.00 e mapear todos os campos.
"""
import xml.etree.ElementTree as ET
import json
from collections import OrderedDict

def extrair_campos_recursivo(element, ns, caminho=''):
    """Extrai campos de forma recursiva."""
    campos = []
    
    # Encontrar todos os elementos filhos
    for elem in element.findall('xs:element', ns):
        nome = elem.get('name', '')
        tipo = elem.get('type', '')
        minOccurs = elem.get('minOccurs', '1')
        maxOccurs = elem.get('maxOccurs', '1')
        
        # Extrair documentação
        doc_elem = elem.find('xs:annotation/xs:documentation', ns)
        doc = doc_elem.text.strip() if doc_elem is not None and doc_elem.text else ''
        
        campo = {
            'nome': nome,
            'caminho': f"{caminho}/{nome}" if caminho else nome,
            'tipo': tipo,
            'obrigatorio': minOccurs != '0',
            'multiplo': maxOccurs != '1',
            'documentacao': doc
        }
        
        if nome:
            campos.append(campo)
        
        # Se tem complexType interno, processar recursivamente
        complex_type = elem.find('xs:complexType', ns)
        if complex_type is not None:
            seq = complex_type.find('xs:sequence', ns)
            if seq is not None:
                subcampos = extrair_campos_recursivo(seq, ns, f"{caminho}/{nome}" if caminho else nome)
                campos.extend(subcampos)
    
    # Processar sequences
    for seq in element.findall('xs:sequence', ns):
        subcampos = extrair_campos_recursivo(seq, ns, caminho)
        campos.extend(subcampos)
    
    # Processar choices
    for choice in element.findall('xs:choice', ns):
        subcampos = extrair_campos_recursivo(choice, ns, caminho)
        campos.extend(subcampos)
    
    return campos

def analisar_xsd_completo(arquivo_xsd):
    """Analisa o XSD completo extraindo toda a estrutura."""
    
    tree = ET.parse(arquivo_xsd)
    root = tree.getroot()
    
    ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}
    
    print("Analisando estrutura do XSD...")
    print(f"Root tag: {root.tag}")
    print(f"Total de complexTypes: {len(root.findall('.//xs:complexType', ns))}")
    print(f"Total de elements: {len(root.findall('.//xs:element', ns))}")
    print()
    
    # Estrutura organizada por grupos
    estrutura = OrderedDict()
    
    # Buscar o elemento raiz TNFe
    tnfe = root.find('.//xs:complexType[@name="TNFe"]', ns)
    
    if tnfe:
        print("✓ Encontrado complexType TNFe")
        
        # Buscar infNFe
        infnfe_seq = tnfe.find('.//xs:element[@name="infNFe"]/xs:complexType/xs:sequence', ns)
        
        if infnfe_seq:
            print("✓ Encontrado infNFe")
            
            # Processar cada grupo principal
            for elem in infnfe_seq.findall('xs:element', ns):
                grupo_nome = elem.get('name', '')
                print(f"\nProcessando grupo: {grupo_nome}")
                
                # Pegar o complexType
                complex_type = elem.find('xs:complexType', ns)
                if complex_type:
                    seq = complex_type.find('xs:sequence', ns)
                    if seq:
                        campos = extrair_campos_recursivo(seq, ns, grupo_nome)
                        estrutura[grupo_nome] = campos
                        print(f"  → {len(campos)} campos encontrados")
                    else:
                        # Pode ser referência a outro tipo
                        tipo_ref = elem.get('type', '')
                        if tipo_ref:
                            # Buscar o complexType referenciado
                            tipo_complex = root.find(f'.//xs:complexType[@name="{tipo_ref}"]', ns)
                            if tipo_complex:
                                seq = tipo_complex.find('xs:sequence', ns)
                                if seq:
                                    campos = extrair_campos_recursivo(seq, ns, grupo_nome)
                                    estrutura[grupo_nome] = campos
                                    print(f"  → {len(campos)} campos encontrados (via referência)")
    
    return estrutura

def gerar_relatorio_completo(estrutura):
    """Gera relatório completo da análise."""
    
    print("\n" + "=" * 80)
    print("RELATÓRIO COMPLETO - LAYOUT NF-e v4.00")
    print("=" * 80 + "\n")
    
    total_campos = 0
    
    for grupo, campos in estrutura.items():
        print(f"### {grupo.upper()} ###")
        print(f"Total: {len(campos)} campos\n")
        
        # Mostrar primeiros 15 campos
        for campo in campos[:15]:
            obr = "[OBR]" if campo['obrigatorio'] else "[OPC]"
            mult = "[*]" if campo['multiplo'] else ""
            doc = campo['documentacao'][:60] + "..." if len(campo['documentacao']) > 60 else campo['documentacao']
            print(f"  {obr}{mult} {campo['nome']:30} | {doc}")
        
        if len(campos) > 15:
            print(f"  ... e mais {len(campos) - 15} campos")
        
        print()
        total_campos += len(campos)
    
    print("=" * 80)
    print(f"TOTAL: {total_campos} campos mapeados em {len(estrutura)} grupos")
    print("=" * 80 + "\n")
    
    return total_campos

def salvar_mapeamento_sql(estrutura, arquivo='campos_nfe_mapeamento.md'):
    """Salva mapeamento em formato Markdown para documentação."""
    
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write("# Mapeamento Completo dos Campos NF-e v4.00\n\n")
        f.write(f"Gerado automaticamente a partir do XSD oficial da NF-e\n\n")
        f.write("---\n\n")
        
        for grupo, campos in estrutura.items():
            f.write(f"## {grupo.upper()}\n\n")
            f.write(f"**Total de campos:** {len(campos)}\n\n")
            f.write("| Campo | Tipo | Obrigatório | Múltiplo | Documentação |\n")
            f.write("|-------|------|-------------|----------|-------------|\n")
            
            for campo in campos:
                obr = "Sim" if campo['obrigatorio'] else "Não"
                mult = "Sim" if campo['multiplo'] else "Não"
                doc = campo['documentacao'].replace('\n', ' ').replace('|', '\\|')
                f.write(f"| `{campo['nome']}` | {campo['tipo']} | {obr} | {mult} | {doc} |\n")
            
            f.write("\n---\n\n")
    
    print(f"✓ Mapeamento salvo em {arquivo}\n")

if __name__ == '__main__':
    try:
        print("\n" + "="*80)
        print("ANALISADOR COMPLETO DE XSD NF-e v4.00")
        print("="*80 + "\n")
        
        estrutura = analisar_xsd_completo('leiauteNFe_v4.00.xsd')
        
        # Salvar JSON
        with open('estrutura_nfe_completa.json', 'w', encoding='utf-8') as f:
            json.dump(estrutura, f, indent=2, ensure_ascii=False)
        print("✓ Estrutura salva em estrutura_nfe_completa.json\n")
        
        # Gerar relatório
        total = gerar_relatorio_completo(estrutura)
        
        # Salvar mapeamento
        salvar_mapeamento_sql(estrutura)
        
        print(f"\n✅ Análise concluída com sucesso!")
        print(f"📊 {total} campos identificados")
        print(f"📁 Arquivos gerados:")
        print(f"   - estrutura_nfe_completa.json")
        print(f"   - campos_nfe_mapeamento.md\n")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
