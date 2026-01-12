# Dashboard e Relatórios da Fase 1

## 📊 Funcionalidades Implementadas

Este documento descreve as funcionalidades do dashboard de visualização dos campos da Fase 1 (41 campos críticos de NF-e).

## 🚀 Acesso ao Dashboard

### Opção 1: Pelo Painel Principal
1. Acesse http://localhost:8000
2. Faça login com suas credenciais
3. No painel de empresas, clique em **"📈 Relatórios Fase 1"** em qualquer empresa

### Opção 2: Pela Página do Datalake
1. Acesse a página de consulta de documentos
2. Clique no botão **"📈 Relatórios Fase 1"** no menu superior

### Opção 3: URL Direta
```
http://localhost:8000/relatorios-fase1?empresa_id={ID_DA_EMPRESA}
```

## 📈 Estatísticas Disponíveis

### 1. Indicadores Gerais (Cards Superiores)
- **Total de NF-es**: Quantidade total de notas fiscais no período
- **Pagamento Eletrônico**: Quantidade de NF-es com pagamento eletrônico
- **Com Intermediador**: Quantidade de operações com intermediador
- **Benefícios Fiscais**: Total de benefícios fiscais únicos identificados

### 2. Gráficos de Distribuição

#### Gráfico 1: Indicador de Presença
- **Tipo**: Gráfico de Pizza
- **Dados**: Distribuição das NF-es por indicador de presença
  - 1 = Operação presencial
  - 2 = Operação não presencial, pela internet
  - 3 = Operação não presencial, teleatendimento
  - 4 = NFC-e em operação com entrega a domicílio
  - 9 = Operação não presencial, outros

#### Gráfico 2: Indicador de Consumidor Final
- **Tipo**: Gráfico de Rosca (Doughnut)
- **Dados**: Distribuição por tipo de consumidor
  - 0 = Normal (não consumidor final)
  - 1 = Consumidor final

#### Gráfico 3: Tipos de Pagamento Eletrônico
- **Tipo**: Gráfico de Barras
- **Dados**: Distribuição por tipo de pagamento
  - 01 = Dinheiro
  - 02 = Cheque
  - 03 = Cartão de Crédito
  - 04 = Cartão de Débito
  - 05 = Crédito Loja
  - 10 = Vale Alimentação
  - 11 = Vale Refeição
  - 12 = Vale Presente
  - 13 = Vale Combustível
  - 15 = Boleto Bancário
  - 16 = Depósito Bancário
  - 17 = PIX
  - 18 = Transferência bancária
  - 19 = Programa de fidelidade
  - 90 = Sem pagamento
  - 99 = Outros

#### Gráfico 4: Indicador de Intermediador
- **Tipo**: Gráfico de Pizza
- **Dados**: Operações com/sem intermediador
  - 0 = Operação sem intermediador
  - 1 = Operação em site ou plataforma de terceiros

### 3. Tabelas Detalhadas

#### Top 10 Naturezas de Operação
- Lista as 10 naturezas de operação mais frequentes
- Mostra descrição completa e quantidade de ocorrências

#### Top 10 Benefícios Fiscais
- Lista os 10 benefícios fiscais mais utilizados
- Exclui automaticamente o código '0000000000' (sem benefício)
- Mostra código e quantidade de itens

#### Intermediadores Identificados
- Lista todos os CNPJs de intermediadores encontrados
- Mostra quantidade de operações por intermediador

## 🔧 Endpoint da API

### GET `/api/estatisticas/fase1`

**Autenticação**: Bearer Token obrigatório

**Parâmetros Query**:
- `empresa_id` (obrigatório): ID da empresa

**Resposta**:
```json
{
  "total_nfes": 520,
  "indicadores": {
    "presenca": {
      "1": 150,
      "2": 100,
      "9": 23
    },
    "final": {
      "0": 200,
      "1": 273
    },
    "intermediador": {
      "0": 463,
      "1": 57
    }
  },
  "naturezas_operacao": [
    {
      "natureza": "VENDA DE MERCADORIA",
      "total": 250
    }
  ],
  "beneficios_fiscais": [
    {
      "codigo": "RJ123456",
      "total_itens": 150
    }
  ],
  "pagamento_eletronico": {
    "total_com_pagamento": 57,
    "tipos": {
      "03": 30,
      "04": 15,
      "17": 12
    }
  },
  "intermediadores": [
    {
      "cnpj": "12.345.678/0001-90",
      "total_operacoes": 45
    }
  ]
}
```

## 📝 Campos da Fase 1 Incluídos

### Campos da NFe (Cabeçalho)
1. `indicador_presenca` - Indicador de presença do comprador
2. `indicador_final` - Indicador de consumidor final
3. `indicador_intermediador` - Indicador de operação com intermediador
4. `codigo_municipio_fg_ibs` - Código do município FG (IBGE)
5. `natureza_operacao` - Natureza da operação
6. `processo_emissao` - Processo de emissão da NF-e
7. `versao_processo` - Versão do processo de emissão
8. `quantidade_bc_mono` - Quantidade tributada BC ICMS monofásico
9. `valor_icms_mono` - Valor do ICMS monofásico
10. `tipo_integracao_pagamento` - Tipo de integração do pagamento
11. `cnpj_intermediador` - CNPJ do intermediador
12. `identificador_intermediador` - Identificador do intermediador

### Campos dos Itens (NFeItem)
13-41. Diversos campos de tributação, rastreabilidade e benefícios fiscais

## 🎨 Tecnologias Utilizadas

- **Backend**: FastAPI + SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Gráficos**: Chart.js v3.9.1
- **Banco de Dados**: PostgreSQL (fiscal_datalake)

## 📊 Validação dos Dados

Segundo o último relatório de validação (520 NF-es processadas):
- **273 NF-es** (52%) com `indicador_presenca` preenchido
- **273 NF-es** (52%) com `indicador_final` preenchido
- **273 NF-es** (52%) com `natureza_operacao` preenchida
- **57 NF-es** (10%) com `tipo_integracao_pagamento` preenchido
- **653 itens** (22%) com `codigo_beneficio_fiscal` preenchido

## 🔐 Segurança

- Autenticação JWT obrigatória para todos os endpoints
- Filtragem automática por empresa do usuário autenticado
- Validação de permissões de acesso

## 📱 Responsividade

O dashboard é totalmente responsivo e funciona em:
- Desktop (otimizado)
- Tablets
- Smartphones

## 🔄 Próximas Melhorias Sugeridas

1. **Filtros de Período**: Adicionar filtros de data_inicio e data_fim
2. **Exportação**: Botões para exportar dados em Excel/PDF
3. **Drill-down**: Clicar em gráficos para ver detalhes
4. **Comparações**: Comparar períodos diferentes
5. **Alertas**: Notificações para anomalias nos dados
6. **Benchmarking**: Comparar com médias do setor
7. **Relatórios Agendados**: Envio automático por e-mail

## 🐛 Troubleshooting

### Dashboard não carrega
- Verifique se está autenticado (token válido)
- Confirme que a empresa_id está correta na URL
- Verifique o console do navegador para erros

### Gráficos vazios
- Pode significar que não há dados para aquele indicador
- Verifique se a empresa possui NF-es processadas
- Confirme que a Fase 1 foi executada corretamente

### Erro 401 Unauthorized
- Token expirado ou inválido
- Faça logout e login novamente

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs do servidor (`app.py`)
2. Consulte o `TROUBLESHOOTING.md` do ETL
3. Revise o `SYSTEM_OVERVIEW.md` para arquitetura geral
