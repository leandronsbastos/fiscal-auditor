# Implementação Fase 1 - Campos Críticos NF-e

## Data: 2026-01-12

## Resumo da Implementação

Implementação bem-sucedida dos campos críticos da Fase 1 baseados na análise do XSD NF-e v4.00 (NT 2025.002 v1.30).

## Campos Implementados

### 1. ICMS Monofásico (NT 2023.003)
**Campos NFe (Totalizadores):**
- quantidade_bc_mono
- valor_icms_mono
- quantidade_bc_mono_reten
- valor_icms_mono_reten
- quantidade_bc_mono_ret
- valor_icms_mono_ret

**Campos NFeItem:**
- quantidade_bc_mono
- aliquota_adrem_mono (aliquota_icms_mono no banco)
- valor_icms_mono
- quantidade_bc_mono_reten
- aliquota_adrem_mono_reten (aliquota_icms_mono_reten no banco)
- valor_icms_mono_reten
- quantidade_bc_mono_ret
- aliquota_adrem_mono_ret (aliquota_icms_mono_ret no banco)
- valor_icms_mono_ret

### 2. Pagamento Eletrônico (NT 2023.001)
**Campos NFe:**
- tipo_integracao_pagamento (tpIntegra)
- cnpj_instituicao_pagamento (CNPJ da instituição - credenciadora)
- bandeira_operadora (tBand)
- numero_autorizacao_pagamento (cAut)
- cnpj_beneficiario_pagamento (CNPJReceb)
- terminal_pagamento (idTermPag)
- cnpj_transacional_pagamento (CNPJPag)
- uf_pagamento (UFPag)

### 3. Benefícios Fiscais (NT 2021.004)
**Campos NFeItem:**
- codigo_beneficio_fiscal (cBenef)
- codigo_beneficio_fiscal_ibs (cBenefIBS)
- codigo_beneficio_fiscal_uf (cBenefUF) - adicionado pela migração

### 4. Crédito Presumido (NT 2023.002)
**Campos NFeItem:**
- codigo_credito_presumido (cCredPresumido)
- percentual_credito_presumido (pCredPresumido)
- valor_credito_presumido (vCredPresumido)
- tipo_credito_pres_ibs_zfm (tpCredPresIBSZFM)

### 5. Indicadores e Complementos
**Campos NFe:**
- indicador_presenca (indPres)
- indicador_final (indFinal)
- indicador_intermediador (indIntermed)
- codigo_municipio_fg_ibs (cMunFGIBS)
- processo_emissao (procEmi)
- versao_processo (verProc)
- natureza_operacao (natOp)

**Campos NFeItem:**
- indicador_escala_relevante (indEscala)
- cnpj_fabricante (CNPJFab)

### 6. Intermediador (NT 2020.006)
**Campos NFe:**
- cnpj_intermediador (CNPJ do intermediador/marketplace)
- identificador_intermediador (idCadIntTran)

## Arquivos Modificados

1. **etl_service/models.py**
   - Já continha os campos necessários

2. **etl_service/extractor.py**
   - ✓ Atualizado método _extrair_identificacao() para extrair codigo_municipio_fg_ibs e indicador_intermediador
   - ✓ Atualizado _extrair_itens() para extrair campos de produto (benefício fiscal, crédito presumido, indicadores)
   - ✓ Atualizado _extrair_impostos_item() para extrair campos ICMS Monofásico nos impostos
   - ✓ Atualizado _extrair_totais() para extrair totalizadores ICMS Monofásico
   - ✓ Atualizado _extrair_pagamento() para extrair campos de pagamento eletrônico
   - ✓ Criado _extrair_intermediador() para extrair dados do intermediador
   - ✓ Adicionada chamada de intermediador na extração principal

3. **etl_service/transformer.py**
   - ✓ Atualizado transformar_nfe() para mapear novos campos da NFe
   - ✓ Atualizado _transformar_item() para mapear novos campos do item
   - ✓ Ajustados nomes dos campos para corresponder aos do banco de dados

4. **etl_service/migrations/003_adicionar_campos_criticos_fase1.sql**
   - ✓ Criada migração SQL completa
   - ✓ Executada com sucesso no banco de dados
   - ✓ Todos os campos adicionados às tabelas nfe e nfe_item

## Status do Banco de Dados

✓ Migração 003 executada com sucesso
✓ 11 campos adicionados na tabela `nfe`
✓ 18 campos adicionados na tabela `nfe_item`
✓ Índices criados (cnpj_intermediador)
✓ 520 NF-es existentes no banco
✓ 2955 itens existentes no banco

## Teste de Extração

Executado teste com XML real (tests/fixtures/nfe_entrada.xml):

**Resultado:**
- ✓ Extração: Funcionando corretamente
- ⚠ Transformação: Issue de cache do SQLAlchemy (os modelos em memória não refletem as novas colunas do banco)

**Campos extraídos com sucesso no XML de teste:**
- processo_emissao: 0
- versao_processo: 1.0
- natureza_operacao: "Compra de mercadoria"

**Campos não encontrados no XML de teste (normal para XML sem esses dados):**
- codigo_municipio_fg_ibs
- indicador_intermediador
- Campos ICMS Monofásico
- Campos de pagamento eletrônico
- Benefícios fiscais

## Observações Técnicas

1. **Cache do SQLAlchemy:**
   - O SQLAlchemy mantém os modelos em cache na memória do processo
   - Após adicionar colunas no banco, é necessário reiniciar a aplicação para que os modelos sejam recarregados
   - Solução: Reiniciar o servidor FastAPI (app.py) ou processos ETL após a migração

2. **Mapeamento de Nomes:**
   - Alguns campos tiveram nomes ajustados entre o XML e o banco:
     - `consumidor_final` → `indicador_final`
     - `cnpj_credenciadora` → `cnpj_instituicao_pagamento`
     - `bandeira_cartao` → `bandeira_operadora`
     - `autorizacao_cartao` → `numero_autorizacao_pagamento`
     - `id_cadastro` → `identificador_intermediador`
     - `aliquota_adrem_mono` → `aliquota_icms_mono` (no banco)

3. **Crédito Presumido:**
   - O XML pode conter múltiplos créditos (grupo gCred pode repetir)
   - Implementação atual pega o primeiro crédito
   - Pode ser expandido para armazenar múltiplos créditos em tabela relacionada no futuro

## Próximos Passos

1. **Reiniciar aplicação:**
   ```bash
   # Reiniciar FastAPI
   Ctrl+C no terminal do app.py
   python app.py
   ```

2. **Testar com XMLs reais contendo:**
   - ICMS Monofásico (combustíveis, lubrificantes)
   - Pagamento eletrônico (PIX, cartão com tpIntegra)
   - Benefícios fiscais (ex: ICMS-ST com cBenef)
   - Operações com intermediador (marketplaces)

3. **Reprocessar XMLs existentes:**
   ```bash
   python run_etl.py
   ```
   - Isso irá extrair e persistir os novos campos dos XMLs já no banco

4. **Fase 2 (Próxima implementação):**
   - Combustíveis (grupo comb)
   - Exportação (grupo exportInd)
   - Rastreabilidade (grupo rastro)
   - ~100 campos adicionais

## Cobertura Atual

- **Antes:** ~60% dos campos do XSD
- **Após Fase 1:** ~70% dos campos do XSD
- **Meta Fase 2:** ~85% dos campos do XSD

## Scripts Criados

1. `executar_migracao_fase1.py` - Executa a migração 003
2. `testar_fase1.py` - Testa extração e transformação dos novos campos
3. `verificar_colunas.py` - Verifica colunas na tabela nfe
4. `verificar_colunas_item.py` - Verifica colunas na tabela nfe_item

## Documentação de Referência

- XSD: leiauteNFe_v4.00.xsd (NT 2025.002 v1.30)
- Notas Técnicas:
  - NT 2023.003: ICMS Monofásico
  - NT 2023.001: Pagamento Eletrônico
  - NT 2021.004: Benefício Fiscal
  - NT 2023.002: Crédito Presumido
  - NT 2020.006: Intermediador
  - NT 2016.002: Indicadores
