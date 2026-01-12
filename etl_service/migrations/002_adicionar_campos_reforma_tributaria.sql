-- Migração: Adicionar campos IBS e CBS (Reforma Tributária)
-- Data: 2026-01-12
-- Descrição: Adiciona campos para armazenar informações de IBS e CBS dos itens e totalizadores

-- Adicionar campos IBS e CBS na tabela de totalizadores (nfe)
ALTER TABLE nfe ADD COLUMN valor_ibs NUMERIC(15, 2);
ALTER TABLE nfe ADD COLUMN valor_cbs NUMERIC(15, 2);

-- Adicionar campos IBS e CBS na tabela de itens (nfe_item)
ALTER TABLE nfe_item ADD COLUMN situacao_tributaria_ibscbs VARCHAR(2);
ALTER TABLE nfe_item ADD COLUMN base_calculo_ibs NUMERIC(15, 2);
ALTER TABLE nfe_item ADD COLUMN aliquota_ibs NUMERIC(5, 4);
ALTER TABLE nfe_item ADD COLUMN valor_ibs NUMERIC(15, 2);
ALTER TABLE nfe_item ADD COLUMN base_calculo_cbs NUMERIC(15, 2);
ALTER TABLE nfe_item ADD COLUMN aliquota_cbs NUMERIC(5, 4);
ALTER TABLE nfe_item ADD COLUMN valor_cbs NUMERIC(15, 2);
