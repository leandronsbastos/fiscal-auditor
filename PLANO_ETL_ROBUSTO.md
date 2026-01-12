# Plano de Implementação - ETL Robusto NF-e v4.00

## 📊 Análise do XSD

**Total de campos identificados:** 405 campos distribuídos em 15 grupos principais

### Distribuição por Grupo:
- **IDE** (Identificação): 31 campos
- **EMIT** (Emitente): 10 campos  
- **AVULSA** (NFe Avulsa): 11 campos
- **DEST** (Destinatário): 10 campos
- **DET** (Detalhes/Itens): 203 campos
- **TOTAL** (Totalizadores): 54 campos
- **TRANSP** (Transporte): 29 campos
- **COBR** (Cobrança): 9 campos
- **PAG** (Pagamento): 16 campos
- **INFINTERMED** (Intermediador): 2 campos
- **INFADIC** (Informações Adicionais): 10 campos
- **EXPORTA** (Exportação): 3 campos
- **COMPRA** (Compra): 3 campos
- **CANA** (Cana de Açúcar): 13 campos
- **INFSOLICNFF** (Solicitação NFF): 1 campo

## 🎯 Status Atual vs. Necessário

### ✅ Grupos já implementados (parcialmente):
- IDE - Identificação ✓ (~80% implementado)
- EMIT - Emitente ✓ (~90% implementado)
- DEST - Destinatário ✓ (~85% implementado)
- DET/PROD - Produtos ✓ (~70% implementado)
- DET/IMPOSTO - Impostos ✓ (~65% implementado)
- TOTAL - Totalizadores ✓ (~75% implementado)
- TRANSP - Transporte ✓ (~60% implementado)
- COBR - Cobrança ✓ (~55% implementado)
- PAG - Pagamento ✓ (~40% implementado)

### ⚠️ Grupos com implementação parcial:
- INFADIC - Informações Adicionais (~30%)
- EXPORTA - Exportação (~20%)
- COMPRA - Compras Públicas (~10%)

### ❌ Grupos não implementados:
- AVULSA - NFe Avulsa (0%)
- RETIRADA - Local de Retirada (0%)
- ENTREGA - Local de Entrega (0%)
- INFINTERMED - Intermediador (0%)
- CANA - Cana de Açúcar (0%)
- INFSOLICNFF - Solicitação NFF (0%)
- AGROPECUÁRIO - Produtos Agropecuários (0%)
- INFRESPTEC - Responsável Técnico (0%)

## 📋 Campos Importantes Faltando

### Identificação (IDE):
- `cMunFGIBS` - Município de FG do IBS/CBS ⭐ REFORMA TRIBUTÁRIA
- `indPres` - Indicador de presença do comprador
- `indFinal` - Consumidor final
- `indIntermed` - Indicador de intermediador
- `procEmi` - Processo de emissão
- `verProc` - Versão do processo de emissão
- `dhCont` - Data/hora da contingência
- `xJust` - Justificativa da contingência

### Produto (PROD):
- `cBenef` - Código de benefício fiscal ⭐ NOVO
- `gCred` - Grupo de crédito presumido ⭐ IMPORTANTE
- `indEscala` - Indicador de escala relevante
- `CNPJFab` - CNPJ do fabricante
- `cBenefIBS` - Benefício fiscal IBS ⭐ REFORMA
- `indRegimeEsp` - Regime especial
- `rastro` - Rastreabilidade de produtos
- `veicProd` - Veículos novos
- `med` - Medicamentos
- `arma` - Armas
- `comb` - Combustíveis

### Impostos:
- **ICMS**: Diversos CST/CSOSN com campos específicos
- **IPI**: Campos de selo de controle
- **II** - Imposto de Importação (não implementado)
- **PIS-ST** e **COFINS-ST** (não implementados)
- **IBSCBS** - Implementação inicial feita, mas faltam validações

### Totalizadores:
- `qBCMono` e `vICMSMono` - ICMS Monofásico ⭐
- `qBCMonoReten` e `vICMSMonoReten` - Retenção Monofásico ⭐
- `qBCMonoRet` e `vICMSMonoRet` - Ret. antecipada ⭐
- Campos de partilha ICMS (DIFAL)
- Campos FCP detalhados

### Pagamento:
- `card` - Dados de cartão/PIX/Boleto ⭐ IMPORTANTE
- `tpIntegra` - Tipo de integração
- `CNPJReceb`, `CNPJPag`, `UFPag` ⭐ NT 2023.001
- `idTermPag` - Terminal de pagamento

## 🚀 Estratégia de Implementação

### Fase 1: Campos Críticos (Prioridade ALTA) ⭐⭐⭐
**Prazo:** Imediato

1. **Reforma Tributária - IBS/CBS**
   - ✅ Campos básicos implementados
   - ⚠️ Faltam: `cMunFGIBS`, `cBenefIBS`, validações
   
2. **ICMS Monofásico** (NT 2023.003)
   - Totalizadores: `qBCMono`, `vICMSMono`, etc.
   - Por item: campos de ICMS Monofásico
   
3. **Pagamentos Eletrônicos** (NT 2023.001)
   - Grupo `card` completo
   - CNPJ do pagador e recebedor
   - Terminal de pagamento

4. **Benefícios Fiscais**
   - `cBenef` no produto
   - Grupo `gCred` (crédito presumido)

### Fase 2: Campos Importantes (Prioridade MÉDIA) ⭐⭐
**Prazo:** Curto prazo (1-2 semanas)

1. **Complementos IDE**
   - Indicadores: `indPres`, `indFinal`, `indIntermed`
   - Contingência: `dhCont`, `xJust`
   - Processo de emissão: `procEmi`, `verProc`

2. **Intermediador da Transação** (Marketplaces)
   - Grupo `infIntermed` completo
   - CNPJ e identificador

3. **Produtos Específicos**
   - Medicamentos (`med`)
   - Combustíveis (`comb`)
   - Veículos (`veicProd`)
   - Rastreabilidade (`rastro`)

4. **Impostos Complementares**
   - IPI completo (selos de controle)
   - II - Imposto de Importação
   - PIS-ST e COFINS-ST

### Fase 3: Campos Especializados (Prioridade BAIXA) ⭐
**Prazo:** Médio prazo (1 mês)

1. **Operações Específicas**
   - Exportação (`exporta`)
   - Compras públicas (`compra`)
   - Cana de açúcar (`cana`)
   - NFF (`infSolicNFF`)
   - Produtos agropecuários

2. **Locais Alternativos**
   - Retirada
   - Entrega

3. **Responsável Técnico**
   - `infRespTec`

4. **NF-e Avulsa**
   - Grupo `avulsa`

## 💾 Estrutura do Banco de Dados

### Tabelas Necessárias:

#### Existentes (a expandir):
- `nfe` - Adicionar ~20 campos
- `nfe_item` - Adicionar ~50 campos

#### Novas tabelas:
1. `nfe_credito_presumido` - Créditos presumidos por item
2. `nfe_rastro` - Rastreabilidade de produtos
3. `nfe_medicamento` - Dados de medicamentos
4. `nfe_combustivel` - Dados de combustíveis
5. `nfe_veiculo` - Dados de veículos
6. `nfe_arma` - Dados de armas
7. `nfe_intermediador` - Dados do intermediador
8. `nfe_exportacao` - Dados de exportação
9. `nfe_compra_publica` - Compras públicas
10. `nfe_cana` - Fornecimento de cana
11. `nfe_local_retirada` - Local de retirada
12. `nfe_local_entrega` - Local de entrega
13. `nfe_autorizacao_xml` - Autorizações para download do XML

## 📝 Próximos Passos

### Etapa 1: Análise de Prioridades ✅ CONCLUÍDA
- [x] Analisar XSD completo
- [x] Mapear 405 campos
- [x] Identificar gaps
- [x] Definir prioridades

### Etapa 2: Implementação Fase 1 (CRÍTICO)
- [ ] Expandir modelos do banco (campos críticos)
- [ ] Criar migrações SQL
- [ ] Atualizar extrator para campos críticos
- [ ] Atualizar transformer
- [ ] Testes com XMLs reais

### Etapa 3: Implementação Fase 2 (IMPORTANTE)
- [ ] Criar novas tabelas especializadas
- [ ] Implementar extração de dados complementares
- [ ] Atualizar datalake_integration.py

### Etapa 4: Implementação Fase 3 (OPCIONAL)
- [ ] Casos especializados (cana, exportação, etc.)
- [ ] Validações avançadas

## 🎯 Objetivos de Cobertura

- **Atual:** ~60% dos campos oficiais
- **Meta Fase 1:** ~85% (campos críticos e comuns)
- **Meta Fase 2:** ~95% (incluindo casos importantes)
- **Meta Fase 3:** 100% (cobertura completa)

## 📌 Campos da Reforma Tributária - Status

### ✅ Implementado:
- Campos básicos IBS/CBS nos itens
- Campos básicos IBS/CBS nos totalizadores
- Extração do XML
- Armazenamento no banco

### ⚠️ Pendente:
- `cMunFGIBS` - Município de FG do IBS/CBS (IDE)
- `cBenefIBS` - Benefício fiscal IBS (PROD)
- `indRegimeEsp` - Regime especial de tributação
- Validações específicas
- Integração com interface web
- Relatórios com IBS/CBS

---

**Documento gerado em:** 12/01/2026
**Baseado em:** leiauteNFe_v4.00.xsd (NT 2025.002 v1.30)
**Total de campos mapeados:** 405 campos
