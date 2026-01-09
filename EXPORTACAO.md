# 📊 Guia de Exportação de Relatórios

## Visão Geral

O sistema Fiscal Auditor oferece recursos completos de exportação de relatórios em dois formatos:
- **Excel (.xlsx)**: Planilha estruturada com múltiplas abas
- **PDF (.pdf)**: Documento formatado para impressão

## Formatos de Exportação

### 📊 Excel (XLSX)

O arquivo Excel gerado contém **6 abas** organizadas:

1. **Resumo Executivo**
   - Resumo geral da apuração
   - Totais de documentos, entradas e saídas
   - Período de competência

2. **Mapa de Apuração**
   - Apuração por tributo (ICMS, PIS, COFINS)
   - Débitos (saídas)
   - Créditos (entradas)
   - Saldo a recolher/credor

3. **Documentos Fiscais**
   - Lista completa de todos os documentos processados
   - Número, tipo, movimento, emitente, destinatário
   - Valores totais e quantidade de itens

4. **Análise de Entradas**
   - Detalhamento de todos os documentos de entrada
   - Totais por documento
   - Créditos tributários

5. **Análise de Saídas**
   - Detalhamento de todos os documentos de saída
   - Totais por documento
   - Débitos tributários

6. **Validações e Alertas**
   - Resultado das validações
   - Créditos aproveitáveis
   - Créditos indevidos ou glosáveis
   - Mensagens de alerta

**Características:**
- Formatação profissional com cores e bordas
- Cabeçalhos destacados
- Valores monetários formatados
- Células ajustadas automaticamente

### 📄 PDF

O arquivo PDF gerado contém:

1. **Cabeçalho com Logo**
   - Título do relatório
   - Período de apuração
   - Data de geração

2. **Resumo Executivo**
   - Indicadores principais em tabela

3. **Mapa de Apuração**
   - Tabela detalhada por tributo
   - Totais e saldos

4. **Documentos Processados**
   - Lista completa em tabela formatada

5. **Validações**
   - Alertas e verificações

**Características:**
- Formato paisagem (landscape) para melhor visualização de tabelas
- Margens otimizadas
- Fonte legível e profissional
- Quebras de página automáticas

## Como Usar

### Via Interface Web

1. **Após processar os XMLs**, acesse qualquer uma das páginas:
   - Dashboard Principal
   - Visão por Produto
   - Análise Tributária

2. **Localize a seção "Exportar Relatórios"**

3. **Clique no botão desejado**:
   - 📊 **Exportar para Excel** - Gera arquivo .xlsx
   - 📄 **Exportar para PDF** - Gera arquivo .pdf

4. **O download inicia automaticamente**
   - Arquivo salvo com nome: `relatorio_fiscal_YYYY-MM-DD.xlsx` ou `.pdf`

### Via API

#### Exportar Excel

```bash
GET /api/export/excel
Authorization: Bearer {seu_token_jwt}
```

**Parâmetros opcionais:**
- `analise_id`: ID da análise salva no banco (se omitido, usa dados da sessão atual)

**Resposta:**
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Arquivo Excel para download

#### Exportar PDF

```bash
GET /api/export/pdf
Authorization: Bearer {seu_token_jwt}
```

**Parâmetros opcionais:**
- `analise_id`: ID da análise salva no banco (se omitido, usa dados da sessão atual)

**Resposta:**
- Content-Type: `application/pdf`
- Arquivo PDF para download

### Exemplos de Código

#### JavaScript (Fetch API)

```javascript
async function exportarExcel() {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/export/excel', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `relatorio_fiscal_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
}
```

#### Python (Requests)

```python
import requests

# Fazer login
login_response = requests.post('http://localhost:8000/api/login', json={
    'email': 'usuario@empresa.com',
    'senha': 'senha123'
})
token = login_response.json()['access_token']

# Exportar Excel
headers = {'Authorization': f'Bearer {token}'}
excel_response = requests.get('http://localhost:8000/api/export/excel', headers=headers)

# Salvar arquivo
with open('relatorio.xlsx', 'wb') as f:
    f.write(excel_response.content)

# Exportar PDF
pdf_response = requests.get('http://localhost:8000/api/export/pdf', headers=headers)

with open('relatorio.pdf', 'wb') as f:
    f.write(pdf_response.content)
```

#### cURL

```bash
# Obter token
TOKEN=$(curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"usuario@empresa.com","senha":"senha123"}' \
  | jq -r '.access_token')

# Exportar Excel
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/export/excel \
  -o relatorio.xlsx

# Exportar PDF
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/export/pdf \
  -o relatorio.pdf
```

## Estrutura de Dados

Os relatórios são gerados a partir dos dados processados que incluem:

```python
{
    "mapa_apuracao": {
        "periodo": "01/2024",
        "apuracoes": [
            {
                "tipo": "ICMS",
                "debitos": 15000.00,
                "creditos": 8000.00,
                "saldo": 7000.00
            }
        ]
    },
    "documentos": [...],
    "validacoes": [...]
}
```

## Requisitos Técnicos

### Dependências Python

```txt
openpyxl>=3.1.0      # Geração de arquivos Excel
reportlab>=4.0.0     # Geração de arquivos PDF
matplotlib>=3.8.0    # Gráficos (futuro)
```

### Instalação

```bash
pip install openpyxl reportlab matplotlib
```

## Segurança

- ✅ Autenticação JWT obrigatória
- ✅ Verificação de acesso à empresa
- ✅ Validação de permissões do usuário
- ✅ Dados isolados por empresa (multi-tenant)

## Limitações

1. **Tamanho dos Arquivos**
   - Dependente do número de documentos processados
   - Recomendado: até 10.000 documentos por relatório

2. **Performance**
   - Geração assíncrona em processamento
   - Tempo médio: 2-5 segundos para 1.000 documentos

3. **Armazenamento**
   - Arquivos gerados em `/tmp/` (temporários)
   - Limpeza automática após download

## Troubleshooting

### Erro: "Nenhum documento processado"
**Solução:** Faça upload de XMLs antes de exportar

### Erro: "Acesso negado a esta análise"
**Solução:** Verifique se o usuário tem acesso à empresa da análise

### Erro: "Token inválido"
**Solução:** Faça login novamente para obter novo token

### Arquivo corrompido
**Solução:** Verifique se todas as dependências estão instaladas corretamente

## Roadmap Futuro

- [ ] Gráficos visuais no Excel e PDF
- [ ] Exportação em formato CSV
- [ ] Relatórios personalizáveis por template
- [ ] Agendamento de exportações automáticas
- [ ] Envio por e-mail
- [ ] Compressão ZIP para múltiplos períodos

## Suporte

Para questões ou problemas, consulte:
- [README.md](README.md) - Documentação principal
- [DATABASE_API.md](DATABASE_API.md) - Documentação da API
- [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) - Visão geral do sistema
