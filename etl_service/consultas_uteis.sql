-- ============================================================================
-- CONSULTAS SQL ÚTEIS PARA O DATALAKE DE DOCUMENTOS FISCAIS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CONSULTAS BÁSICAS
-- ----------------------------------------------------------------------------

-- Contar total de notas
SELECT COUNT(*) as total_notas FROM nfe;

-- Últimas 10 notas processadas
SELECT 
    chave_acesso,
    numero_nota,
    serie,
    data_emissao,
    emitente_razao_social,
    destinatario_razao_social,
    valor_total_nota,
    data_processamento_etl
FROM nfe
ORDER BY data_processamento_etl DESC
LIMIT 10;

-- Buscar nota por chave de acesso
SELECT * FROM nfe 
WHERE chave_acesso = '35240112345678901234550010000123451234567890';

-- Buscar notas por número
SELECT * FROM nfe 
WHERE numero_nota = '123456';


-- ----------------------------------------------------------------------------
-- 2. CONSULTAS POR EMITENTE/DESTINATÁRIO
-- ----------------------------------------------------------------------------

-- Todas as notas de um emitente
SELECT 
    numero_nota,
    serie,
    data_emissao,
    destinatario_razao_social,
    valor_total_nota
FROM nfe
WHERE emitente_cnpj = '12345678000190'
ORDER BY data_emissao DESC;

-- Todas as compras de um destinatário
SELECT 
    numero_nota,
    serie,
    data_emissao,
    emitente_razao_social,
    valor_total_nota
FROM nfe
WHERE destinatario_cnpj = '12345678000190'
ORDER BY data_emissao DESC;

-- Top 10 emitentes por quantidade de notas
SELECT 
    emitente_cnpj,
    emitente_razao_social,
    COUNT(*) as quantidade_notas,
    SUM(valor_total_nota) as valor_total
FROM nfe
GROUP BY emitente_cnpj, emitente_razao_social
ORDER BY quantidade_notas DESC
LIMIT 10;

-- Top 10 destinatários por valor
SELECT 
    destinatario_cnpj,
    destinatario_razao_social,
    COUNT(*) as quantidade_notas,
    SUM(valor_total_nota) as valor_total
FROM nfe
GROUP BY destinatario_cnpj, destinatario_razao_social
ORDER BY valor_total DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- 3. ANÁLISES POR PERÍODO
-- ----------------------------------------------------------------------------

-- Total por mês
SELECT 
    DATE_TRUNC('month', data_emissao) as mes,
    COUNT(*) as quantidade,
    SUM(valor_total_nota) as valor_total,
    AVG(valor_total_nota) as valor_medio
FROM nfe
GROUP BY DATE_TRUNC('month', data_emissao)
ORDER BY mes DESC;

-- Total por dia (últimos 30 dias)
SELECT 
    DATE(data_emissao) as dia,
    COUNT(*) as quantidade,
    SUM(valor_total_nota) as valor_total
FROM nfe
WHERE data_emissao >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(data_emissao)
ORDER BY dia DESC;

-- Comparativo mensal (ano atual vs ano anterior)
SELECT 
    EXTRACT(MONTH FROM data_emissao) as mes,
    EXTRACT(YEAR FROM data_emissao) as ano,
    COUNT(*) as quantidade,
    SUM(valor_total_nota) as valor_total
FROM nfe
WHERE EXTRACT(YEAR FROM data_emissao) IN (
    EXTRACT(YEAR FROM CURRENT_DATE),
    EXTRACT(YEAR FROM CURRENT_DATE) - 1
)
GROUP BY EXTRACT(MONTH FROM data_emissao), EXTRACT(YEAR FROM data_emissao)
ORDER BY mes, ano;


-- ----------------------------------------------------------------------------
-- 4. ANÁLISES DE PRODUTOS/ITENS
-- ----------------------------------------------------------------------------

-- Total de itens
SELECT COUNT(*) as total_itens FROM nfe_item;

-- Produtos mais vendidos
SELECT 
    descricao,
    ncm,
    COUNT(*) as quantidade_vendas,
    SUM(quantidade_comercial) as quantidade_total,
    SUM(valor_total_bruto) as valor_total
FROM nfe_item
GROUP BY descricao, ncm
ORDER BY quantidade_vendas DESC
LIMIT 20;

-- Produtos por NCM
SELECT 
    ncm,
    COUNT(DISTINCT descricao) as variedades,
    COUNT(*) as quantidade_vendas,
    SUM(quantidade_comercial) as quantidade_total,
    SUM(valor_total_bruto) as valor_total
FROM nfe_item
WHERE ncm IS NOT NULL
GROUP BY ncm
ORDER BY valor_total DESC
LIMIT 20;

-- Produtos por CFOP
SELECT 
    cfop,
    COUNT(*) as quantidade,
    SUM(valor_total_bruto) as valor_total
FROM nfe_item
WHERE cfop IS NOT NULL
GROUP BY cfop
ORDER BY quantidade DESC;


-- ----------------------------------------------------------------------------
-- 5. ANÁLISES DE IMPOSTOS
-- ----------------------------------------------------------------------------

-- Total de impostos geral
SELECT 
    SUM(valor_icms) as total_icms,
    SUM(valor_icms_st) as total_icms_st,
    SUM(valor_ipi) as total_ipi,
    SUM(valor_pis) as total_pis,
    SUM(valor_cofins) as total_cofins,
    SUM(valor_aproximado_tributos) as total_tributos
FROM nfe;

-- Impostos por mês
SELECT 
    DATE_TRUNC('month', n.data_emissao) as mes,
    SUM(n.valor_icms) as total_icms,
    SUM(n.valor_ipi) as total_ipi,
    SUM(n.valor_pis) as total_pis,
    SUM(n.valor_cofins) as total_cofins
FROM nfe n
GROUP BY DATE_TRUNC('month', n.data_emissao)
ORDER BY mes DESC;

-- Alíquotas médias de ICMS por UF
SELECT 
    n.emitente_uf as uf,
    COUNT(*) as quantidade_notas,
    AVG(i.aliquota_icms) as aliquota_media_icms,
    SUM(i.valor_icms) as total_icms
FROM nfe n
JOIN nfe_item i ON n.id = i.nfe_id
WHERE i.aliquota_icms IS NOT NULL
GROUP BY n.emitente_uf
ORDER BY quantidade_notas DESC;

-- Análise de substituição tributária
SELECT 
    COUNT(DISTINCT n.id) as notas_com_st,
    SUM(n.valor_icms_st) as total_st,
    AVG(n.valor_icms_st) as media_st
FROM nfe n
WHERE n.valor_icms_st > 0;


-- ----------------------------------------------------------------------------
-- 6. ANÁLISES POR UF/REGIÃO
-- ----------------------------------------------------------------------------

-- Total por UF do emitente
SELECT 
    emitente_uf,
    COUNT(*) as quantidade,
    SUM(valor_total_nota) as valor_total
FROM nfe
GROUP BY emitente_uf
ORDER BY valor_total DESC;

-- Operações interestaduais
SELECT 
    emitente_uf,
    destinatario_uf,
    COUNT(*) as quantidade,
    SUM(valor_total_nota) as valor_total
FROM nfe
WHERE emitente_uf != destinatario_uf
GROUP BY emitente_uf, destinatario_uf
ORDER BY quantidade DESC;


-- ----------------------------------------------------------------------------
-- 7. ANÁLISES DE SITUAÇÃO/STATUS
-- ----------------------------------------------------------------------------

-- Distribuição por situação
SELECT 
    situacao,
    COUNT(*) as quantidade,
    SUM(valor_total_nota) as valor_total
FROM nfe
GROUP BY situacao
ORDER BY quantidade DESC;

-- Notas canceladas
SELECT 
    chave_acesso,
    numero_nota,
    serie,
    data_emissao,
    emitente_razao_social,
    valor_total_nota
FROM nfe
WHERE situacao = 'Cancelada'
ORDER BY data_emissao DESC;

-- Distribuição por tipo (NF-e vs NFC-e)
SELECT 
    CASE 
        WHEN modelo = '55' THEN 'NF-e'
        WHEN modelo = '65' THEN 'NFC-e'
        ELSE 'Outro'
    END as tipo,
    COUNT(*) as quantidade,
    SUM(valor_total_nota) as valor_total
FROM nfe
GROUP BY modelo
ORDER BY quantidade DESC;


-- ----------------------------------------------------------------------------
-- 8. ANÁLISES DE TRANSPORTE
-- ----------------------------------------------------------------------------

-- Distribuição por modalidade de frete
SELECT 
    CASE modalidade_frete
        WHEN '0' THEN 'Emitente'
        WHEN '1' THEN 'Destinatário'
        WHEN '2' THEN 'Terceiros'
        WHEN '9' THEN 'Sem frete'
        ELSE 'Outros'
    END as modalidade,
    COUNT(*) as quantidade
FROM nfe
WHERE modalidade_frete IS NOT NULL
GROUP BY modalidade_frete
ORDER BY quantidade DESC;

-- Total de peso transportado por mês
SELECT 
    DATE_TRUNC('month', data_emissao) as mes,
    SUM(peso_bruto) as peso_total_kg,
    COUNT(*) as quantidade_notas
FROM nfe
WHERE peso_bruto IS NOT NULL
GROUP BY DATE_TRUNC('month', data_emissao)
ORDER BY mes DESC;


-- ----------------------------------------------------------------------------
-- 9. ANÁLISES DE PAGAMENTO
-- ----------------------------------------------------------------------------

-- Distribuição por forma de pagamento
SELECT 
    forma_pagamento,
    COUNT(*) as quantidade,
    SUM(valor_total_nota) as valor_total
FROM nfe
WHERE forma_pagamento IS NOT NULL
GROUP BY forma_pagamento
ORDER BY quantidade DESC;

-- Análise de duplicatas
SELECT 
    COUNT(DISTINCT d.nfe_id) as notas_com_duplicatas,
    COUNT(*) as total_duplicatas,
    SUM(d.valor_duplicata) as valor_total_duplicatas,
    AVG(d.valor_duplicata) as valor_medio_duplicata
FROM nfe_duplicata d;

-- Vencimentos futuros
SELECT 
    DATE(d.data_vencimento) as data_vencimento,
    COUNT(*) as quantidade_duplicatas,
    SUM(d.valor_duplicata) as valor_total
FROM nfe_duplicata d
WHERE d.data_vencimento >= CURRENT_DATE
GROUP BY DATE(d.data_vencimento)
ORDER BY data_vencimento;


-- ----------------------------------------------------------------------------
-- 10. MONITORAMENTO DO ETL
-- ----------------------------------------------------------------------------

-- Histórico de processamentos
SELECT 
    id,
    data_processamento,
    tipo_processamento,
    status,
    arquivos_processados,
    arquivos_erro,
    tempo_execucao
FROM etl_processamento
ORDER BY data_processamento DESC;

-- Arquivos com erro no último processamento
SELECT 
    arquivo,
    chave_acesso,
    status,
    mensagem,
    tempo_processamento
FROM etl_log_processamento
WHERE status = 'erro'
ORDER BY data_hora DESC
LIMIT 50;

-- Estatísticas de processamento
SELECT 
    DATE(data_hora) as data,
    COUNT(*) as total_arquivos,
    COUNT(CASE WHEN status = 'sucesso' THEN 1 END) as sucessos,
    COUNT(CASE WHEN status = 'duplicado' THEN 1 END) as duplicados,
    COUNT(CASE WHEN status = 'erro' THEN 1 END) as erros,
    AVG(tempo_processamento) as tempo_medio
FROM etl_log_processamento
GROUP BY DATE(data_hora)
ORDER BY data DESC;


-- ----------------------------------------------------------------------------
-- 11. CONSULTAS COMPLEXAS/AVANÇADAS
-- ----------------------------------------------------------------------------

-- Nota completa com itens
SELECT 
    n.chave_acesso,
    n.numero_nota,
    n.serie,
    n.data_emissao,
    n.emitente_razao_social,
    n.destinatario_razao_social,
    n.valor_total_nota,
    json_agg(
        json_build_object(
            'item', i.numero_item,
            'codigo', i.codigo_produto,
            'descricao', i.descricao,
            'quantidade', i.quantidade_comercial,
            'valor_unitario', i.valor_unitario_comercial,
            'valor_total', i.valor_total_bruto
        ) ORDER BY i.numero_item
    ) as itens
FROM nfe n
LEFT JOIN nfe_item i ON n.id = i.nfe_id
WHERE n.chave_acesso = '35240112345678901234550010000123451234567890'
GROUP BY n.id;

-- Ranking de produtos por emitente
WITH ranking AS (
    SELECT 
        n.emitente_razao_social,
        i.descricao,
        COUNT(*) as vendas,
        SUM(i.quantidade_comercial) as quantidade,
        SUM(i.valor_total_bruto) as valor_total,
        ROW_NUMBER() OVER (
            PARTITION BY n.emitente_cnpj 
            ORDER BY SUM(i.valor_total_bruto) DESC
        ) as rank
    FROM nfe n
    JOIN nfe_item i ON n.id = i.nfe_id
    GROUP BY n.emitente_cnpj, n.emitente_razao_social, i.descricao
)
SELECT * FROM ranking
WHERE rank <= 5
ORDER BY emitente_razao_social, rank;

-- Análise de sazonalidade (vendas por mês nos últimos 2 anos)
SELECT 
    EXTRACT(MONTH FROM data_emissao) as mes,
    EXTRACT(YEAR FROM data_emissao) as ano,
    COUNT(*) as quantidade,
    SUM(valor_total_nota) as valor_total,
    AVG(valor_total_nota) as ticket_medio
FROM nfe
WHERE data_emissao >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY EXTRACT(MONTH FROM data_emissao), EXTRACT(YEAR FROM data_emissao)
ORDER BY ano DESC, mes;


-- ----------------------------------------------------------------------------
-- 12. VIEWS ÚTEIS
-- ----------------------------------------------------------------------------

-- View para análise simplificada de notas
CREATE OR REPLACE VIEW vw_nfe_resumo AS
SELECT 
    n.chave_acesso,
    n.numero_nota,
    n.serie,
    CASE WHEN n.modelo = '55' THEN 'NF-e' WHEN n.modelo = '65' THEN 'NFC-e' ELSE 'Outro' END as tipo,
    n.data_emissao,
    n.emitente_cnpj,
    n.emitente_razao_social,
    n.emitente_uf,
    n.destinatario_cnpj,
    n.destinatario_razao_social,
    n.destinatario_uf,
    n.valor_produtos,
    n.valor_total_nota,
    n.valor_icms,
    n.valor_ipi,
    n.valor_pis,
    n.valor_cofins,
    n.situacao,
    COUNT(i.id) as quantidade_itens
FROM nfe n
LEFT JOIN nfe_item i ON n.id = i.nfe_id
GROUP BY n.id;

-- View para análise de produtos
CREATE OR REPLACE VIEW vw_produtos_vendas AS
SELECT 
    i.codigo_produto,
    i.descricao,
    i.ncm,
    i.cfop,
    COUNT(*) as quantidade_vendas,
    SUM(i.quantidade_comercial) as quantidade_total,
    SUM(i.valor_total_bruto) as valor_total,
    AVG(i.valor_unitario_comercial) as preco_medio,
    COUNT(DISTINCT n.emitente_cnpj) as quantidade_fornecedores
FROM nfe_item i
JOIN nfe n ON i.nfe_id = n.id
GROUP BY i.codigo_produto, i.descricao, i.ncm, i.cfop;


-- ----------------------------------------------------------------------------
-- FIM
-- ----------------------------------------------------------------------------
