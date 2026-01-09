-- Migração: Adicionar tabela de controle de arquivos processados
-- Data: 2025-01-01
-- Descrição: Cria tabela para rastrear arquivos XML processados, evitar duplicatas e gerenciar deleção

-- Criar tabela etl_arquivo_processado (nome deve corresponder ao modelo SQLAlchemy)
CREATE TABLE IF NOT EXISTS etl_arquivo_processado (
    id SERIAL PRIMARY KEY,
    caminho_arquivo VARCHAR(500) NOT NULL,
    nome_arquivo VARCHAR(255),
    hash_arquivo VARCHAR(64),
    tamanho_arquivo INTEGER,
    chave_acesso VARCHAR(44),
    nfe_id INTEGER REFERENCES nfe(id),
    data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    data_modificacao_arquivo TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    caminho_backup VARCHAR(500),
    deletado BOOLEAN DEFAULT false
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_arquivo_caminho ON etl_arquivo_processado(caminho_arquivo);
CREATE INDEX IF NOT EXISTS idx_arquivo_nome ON etl_arquivo_processado(nome_arquivo);
CREATE INDEX IF NOT EXISTS idx_arquivo_hash ON etl_arquivo_processado(hash_arquivo);
CREATE INDEX IF NOT EXISTS idx_arquivo_chave ON etl_arquivo_processado(chave_acesso);
CREATE INDEX IF NOT EXISTS idx_arquivo_status ON etl_arquivo_processado(status);
CREATE INDEX IF NOT EXISTS idx_arquivo_data ON etl_arquivo_processado(data_processamento);

-- Comentários nas colunas
COMMENT ON TABLE etl_arquivo_processado IS 'Registro de todos os arquivos XML processados pelo ETL';
COMMENT ON COLUMN etl_arquivo_processado.caminho_arquivo IS 'Caminho completo do arquivo XML original';
COMMENT ON COLUMN etl_arquivo_processado.nome_arquivo IS 'Nome do arquivo (sem caminho)';
COMMENT ON COLUMN etl_arquivo_processado.hash_arquivo IS 'Hash SHA256 do conteúdo do arquivo';
COMMENT ON COLUMN etl_arquivo_processado.tamanho_arquivo IS 'Tamanho do arquivo em bytes';
COMMENT ON COLUMN etl_arquivo_processado.chave_acesso IS 'Chave de acesso da NF-e (44 caracteres)';
COMMENT ON COLUMN etl_arquivo_processado.nfe_id IS 'ID da NF-e no banco (se processado)';
COMMENT ON COLUMN etl_arquivo_processado.status IS 'Status do processamento: processado, duplicado, erro';
COMMENT ON COLUMN etl_arquivo_processado.data_processamento IS 'Data e hora do processamento';
COMMENT ON COLUMN etl_arquivo_processado.data_modificacao_arquivo IS 'Data de modificação do arquivo original';
COMMENT ON COLUMN etl_arquivo_processado.deletado IS 'Indica se o arquivo foi deletado após processamento';
COMMENT ON COLUMN etl_arquivo_processado.caminho_backup IS 'Caminho do arquivo no diretório de backup (se movido)';
