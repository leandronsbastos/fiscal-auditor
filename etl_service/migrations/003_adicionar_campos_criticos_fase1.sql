-- Migração: Adicionar campos críticos da Fase 1 (ICMS Monofásico, Pagamentos, Benefícios)
-- Data: 2026-01-12
-- Descrição: Adiciona campos críticos identificados na análise do XSD NF-e v4.00

-- ==========================================
-- TABELA NFE - Campos Críticos
-- ==========================================

-- Indicadores
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS indicador_presenca VARCHAR(1);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS indicador_final VARCHAR(1);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS indicador_intermediador VARCHAR(1);

-- Município FG IBS/CBS
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS codigo_municipio_fg_ibs VARCHAR(10);

-- Processo de emissão
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS processo_emissao VARCHAR(1);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS versao_processo VARCHAR(20);

-- Natureza da operação
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS natureza_operacao VARCHAR(60);

-- ICMS Monofásico - Totalizadores
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS quantidade_bc_mono NUMERIC(15, 4);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS valor_icms_mono NUMERIC(15, 2);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS quantidade_bc_mono_reten NUMERIC(15, 4);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS valor_icms_mono_reten NUMERIC(15, 2);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS quantidade_bc_mono_ret NUMERIC(15, 4);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS valor_icms_mono_ret NUMERIC(15, 2);

-- Pagamentos Eletrônicos (NT 2023.001)
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS tipo_integracao_pagamento VARCHAR(1);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS cnpj_instituicao_pagamento VARCHAR(14);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS bandeira_operadora VARCHAR(2);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS numero_autorizacao_pagamento VARCHAR(128);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS cnpj_beneficiario_pagamento VARCHAR(14);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS terminal_pagamento VARCHAR(8);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS cnpj_transacional_pagamento VARCHAR(14);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS uf_pagamento VARCHAR(2);

-- Intermediador (Marketplace - NT 2019.001)
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS cnpj_intermediador VARCHAR(14);
ALTER TABLE nfe ADD COLUMN IF NOT EXISTS identificador_intermediador VARCHAR(60);

-- Criar índice no CNPJ do intermediador
CREATE INDEX IF NOT EXISTS idx_nfe_cnpj_intermediador ON nfe(cnpj_intermediador);

-- ==========================================
-- TABELA NFE_ITEM - Campos Críticos
-- ==========================================

-- Benefício Fiscal (NT 2021.004)
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS codigo_beneficio_fiscal VARCHAR(10);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS codigo_beneficio_fiscal_ibs VARCHAR(10);

-- Crédito Presumido (NT 2023.002)
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS codigo_credito_presumido VARCHAR(3);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS percentual_credito_presumido NUMERIC(5, 2);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS valor_credito_presumido NUMERIC(15, 2);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS tipo_credito_pres_ibs_zfm VARCHAR(1);

-- Indicadores
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS indicador_escala_relevante VARCHAR(1);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS cnpj_fabricante VARCHAR(14);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS codigo_beneficio_fiscal_uf VARCHAR(10);

-- ICMS Monofásico nos Itens (NT 2023.003 - Combustíveis)
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS quantidade_bc_mono NUMERIC(15, 4);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS aliquota_icms_mono NUMERIC(15, 4);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS valor_icms_mono NUMERIC(15, 2);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS quantidade_bc_mono_reten NUMERIC(15, 4);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS aliquota_icms_mono_reten NUMERIC(15, 4);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS valor_icms_mono_reten NUMERIC(15, 2);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS quantidade_bc_mono_ret NUMERIC(15, 4);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS aliquota_icms_mono_ret NUMERIC(15, 4);
ALTER TABLE nfe_item ADD COLUMN IF NOT EXISTS valor_icms_mono_ret NUMERIC(15, 2);

-- ==========================================
-- COMENTÁRIOS NOS CAMPOS
-- ==========================================

COMMENT ON COLUMN nfe.indicador_presenca IS '0=Não se aplica, 1=Presencial, 2=Internet, 3=Teleatendimento, 4=NFC-e entrega domicílio, 5=Fora estabelecimento, 9=Outros';
COMMENT ON COLUMN nfe.indicador_final IS '0=Normal, 1=Consumidor final';
COMMENT ON COLUMN nfe.indicador_intermediador IS '0=Sem intermediador, 1=Com intermediador';
COMMENT ON COLUMN nfe.codigo_municipio_fg_ibs IS 'Município de ocorrência do fato gerador do IBS/CBS (Código IBGE)';
COMMENT ON COLUMN nfe.cnpj_intermediador IS 'CNPJ do intermediador da transação (marketplace, plataforma digital)';
COMMENT ON COLUMN nfe.quantidade_bc_mono IS 'Quantidade tributada do ICMS monofásico próprio';
COMMENT ON COLUMN nfe.valor_icms_mono IS 'Valor do ICMS monofásico próprio';

COMMENT ON COLUMN nfe_item.codigo_beneficio_fiscal IS 'Código de benefício fiscal na UF aplicável ao item';
COMMENT ON COLUMN nfe_item.codigo_credito_presumido IS 'Código de benefício fiscal de crédito presumido na UF';
COMMENT ON COLUMN nfe_item.percentual_credito_presumido IS 'Percentual do crédito presumido';
COMMENT ON COLUMN nfe_item.valor_credito_presumido IS 'Valor do crédito presumido';
COMMENT ON COLUMN nfe_item.indicador_escala_relevante IS 'S=Produzido em escala relevante, N=Não produzido em escala relevante';
COMMENT ON COLUMN nfe_item.quantidade_bc_mono IS 'Quantidade tributada do ICMS monofásico próprio do item';
COMMENT ON COLUMN nfe_item.aliquota_icms_mono IS 'Alíquota ad rem do imposto (R$ por unidade)';
