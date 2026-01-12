-- Adicionar campos do ICMS Monofásico (NT 2023.003) na tabela nfe_item

ALTER TABLE nfe_item 
ADD COLUMN IF NOT EXISTS quantidade_bc_mono NUMERIC(15, 4),
ADD COLUMN IF NOT EXISTS valor_icms_mono NUMERIC(15, 2),
ADD COLUMN IF NOT EXISTS quantidade_bc_mono_reten NUMERIC(15, 4),
ADD COLUMN IF NOT EXISTS valor_icms_mono_reten NUMERIC(15, 2),
ADD COLUMN IF NOT EXISTS quantidade_bc_mono_ret NUMERIC(15, 4),
ADD COLUMN IF NOT EXISTS valor_icms_mono_ret NUMERIC(15, 2);

-- Verificar se as colunas foram criadas
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'nfe_item'
AND column_name LIKE '%mono%'
ORDER BY column_name;
