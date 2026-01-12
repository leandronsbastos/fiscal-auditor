"""
Modelos do banco de dados para o datalake de documentos fiscais.

Este módulo contém todos os modelos necessários para armazenar completamente
os dados extraídos dos arquivos XML de NF-e e NFC-e.
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Numeric, Boolean, Text, Date
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class ProcessamentoETL(Base):
    """Registro de execuções do processo ETL."""
    __tablename__ = 'etl_processamento'

    id = Column(Integer, primary_key=True, index=True)
    data_processamento = Column(DateTime, default=datetime.now, nullable=False)
    tipo_processamento = Column(String(50), nullable=False)  # 'completo', 'incremental'
    arquivos_processados = Column(Integer, default=0)
    arquivos_erro = Column(Integer, default=0)
    tempo_execucao = Column(Numeric(10, 2))  # em segundos
    status = Column(String(20), nullable=False)  # 'executando', 'concluido', 'erro'
    mensagem = Column(Text)


class NFe(Base):
    """Nota Fiscal Eletrônica - Dados principais."""
    __tablename__ = 'nfe'

    id = Column(Integer, primary_key=True, index=True)
    
    # Identificação
    chave_acesso = Column(String(44), unique=True, index=True, nullable=False)
    numero_nota = Column(String(20), nullable=False, index=True)
    serie = Column(String(10), nullable=False)
    modelo = Column(String(2), nullable=False)  # '55' para NF-e, '65' para NFC-e
    tipo_emissao = Column(String(1))  # 1=Normal, 2=Contingência, etc
    tipo_operacao = Column(String(1))  # 0=Entrada, 1=Saída
    finalidade_emissao = Column(String(1))  # 1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução
    natureza_operacao = Column(String(60))  # Descrição da natureza da operação
    
    # Indicadores (NT 2016.002)
    indicador_presenca = Column(String(1))  # 0=Não se aplica, 1=Operação presencial, etc
    indicador_final = Column(String(1))  # 0=Normal, 1=Consumidor final
    indicador_intermediador = Column(String(1))  # 0=Operação sem intermediador, 1=Com intermediador
    
    # Município de FG do IBS/CBS (Reforma Tributária)
    codigo_municipio_fg_ibs = Column(String(10))  # Código IBGE do município de FG do IBS/CBS
    
    # Processo de emissão
    processo_emissao = Column(String(1))  # 0=Emissão própria, 1=Terceiros, etc
    versao_processo = Column(String(20))  # Versão do aplicativo emissor
    
    # Datas
    data_emissao = Column(DateTime, nullable=False, index=True)
    data_saida_entrada = Column(DateTime)
    data_autorizacao = Column(DateTime)
    data_processamento_etl = Column(DateTime, default=datetime.now, nullable=False)
    
    # Situação
    situacao = Column(String(20))  # 'Autorizada', 'Cancelada', 'Denegada', etc
    codigo_status = Column(String(3))
    motivo_status = Column(Text)
    protocolo_autorizacao = Column(String(20))
    
    # Emitente
    emitente_cnpj = Column(String(14), index=True)
    emitente_cpf = Column(String(11))
    emitente_razao_social = Column(String(200))
    emitente_nome_fantasia = Column(String(200))
    emitente_ie = Column(String(20))
    emitente_im = Column(String(20))
    emitente_cnae = Column(String(10))
    emitente_crt = Column(String(1))  # Código de Regime Tributário
    emitente_logradouro = Column(String(200))
    emitente_numero = Column(String(20))
    emitente_complemento = Column(String(200))
    emitente_bairro = Column(String(100))
    emitente_codigo_municipio = Column(String(10))
    emitente_municipio = Column(String(100))
    emitente_uf = Column(String(2))
    emitente_cep = Column(String(8))
    emitente_telefone = Column(String(20))
    emitente_email = Column(String(200))
    
    # Destinatário
    destinatario_cnpj = Column(String(14), index=True)
    destinatario_cpf = Column(String(11))
    destinatario_razao_social = Column(String(200))
    destinatario_ie = Column(String(20))
    destinatario_im = Column(String(20))
    destinatario_logradouro = Column(String(200))
    destinatario_numero = Column(String(20))
    destinatario_complemento = Column(String(200))
    destinatario_bairro = Column(String(100))
    destinatario_codigo_municipio = Column(String(10))
    destinatario_municipio = Column(String(100))
    destinatario_uf = Column(String(2))
    destinatario_cep = Column(String(8))
    destinatario_telefone = Column(String(20))
    destinatario_email = Column(String(200))
    destinatario_indicador_ie = Column(String(1))  # 1=Contribuinte, 2=Isento, 9=Não Contribuinte
    
    # Totalizadores
    valor_produtos = Column(Numeric(15, 2))
    valor_frete = Column(Numeric(15, 2))
    valor_seguro = Column(Numeric(15, 2))
    valor_desconto = Column(Numeric(15, 2))
    valor_outras_despesas = Column(Numeric(15, 2))
    valor_ipi = Column(Numeric(15, 2))
    valor_total_nota = Column(Numeric(15, 2))
    
    # ICMS
    base_calculo_icms = Column(Numeric(15, 2))
    valor_icms = Column(Numeric(15, 2))
    valor_icms_desonerado = Column(Numeric(15, 2))
    base_calculo_icms_st = Column(Numeric(15, 2))
    valor_icms_st = Column(Numeric(15, 2))
    valor_fcp = Column(Numeric(15, 2))  # Fundo de Combate à Pobreza
    valor_fcp_st = Column(Numeric(15, 2))
    valor_fcp_st_retido = Column(Numeric(15, 2))
    
    # PIS/COFINS
    valor_pis = Column(Numeric(15, 2))
    valor_cofins = Column(Numeric(15, 2))
    
    # IBS/CBS (Reforma Tributária)
    valor_ibs = Column(Numeric(15, 2))
    valor_cbs = Column(Numeric(15, 2))
    
    # ICMS Monofásico (NT 2023.003)
    quantidade_bc_mono = Column(Numeric(15, 4))  # Quantidade tributada ICMS monofásico próprio
    valor_icms_mono = Column(Numeric(15, 2))  # Valor ICMS monofásico próprio
    quantidade_bc_mono_reten = Column(Numeric(15, 4))  # Quantidade tributada ICMS monofásico sujeito a retenção
    valor_icms_mono_reten = Column(Numeric(15, 2))  # Valor ICMS monofásico sujeito a retenção
    quantidade_bc_mono_ret = Column(Numeric(15, 4))  # Quantidade tributada ICMS monofásico retido anteriormente
    valor_icms_mono_ret = Column(Numeric(15, 2))  # Valor ICMS monofásico retido anteriormente
    
    # Outros
    valor_aproximado_tributos = Column(Numeric(15, 2))
    informacoes_adicionais_fisco = Column(Text)
    informacoes_complementares = Column(Text)
    
    # Transporte
    modalidade_frete = Column(String(1))  # 0=Emitente, 1=Destinatário, 2=Terceiros, 9=Sem frete
    transportadora_cnpj = Column(String(14))
    transportadora_cpf = Column(String(11))
    transportadora_razao_social = Column(String(200))
    transportadora_ie = Column(String(20))
    transportadora_endereco = Column(String(300))
    transportadora_municipio = Column(String(100))
    transportadora_uf = Column(String(2))
    veiculo_placa = Column(String(10))
    veiculo_uf = Column(String(2))
    veiculo_rntc = Column(String(20))
    
    # Volume
    quantidade_volumes = Column(Integer)
    especie_volumes = Column(String(100))
    marca_volumes = Column(String(100))
    numeracao_volumes = Column(String(100))
    peso_liquido = Column(Numeric(15, 3))
    peso_bruto = Column(Numeric(15, 3))
    
    # Pagamento
    forma_pagamento = Column(String(2))  # 0=À vista, 1=À prazo, etc
    meio_pagamento = Column(String(2))  # 01=Dinheiro, 02=Cheque, 03=Cartão Crédito, etc
    valor_pagamento = Column(Numeric(15, 2))
    
    # Pagamento Eletrônico (NT 2023.001)
    tipo_integracao_pagamento = Column(String(1))  # 1=Integrado, 2=Não integrado
    cnpj_instituicao_pagamento = Column(String(14))  # CNPJ da credenciadora de cartão/PIX
    bandeira_operadora = Column(String(2))  # 01=Visa, 02=Mastercard, 99=Outros
    numero_autorizacao_pagamento = Column(String(128))  # Número de autorização PIX/Cartão
    cnpj_beneficiario_pagamento = Column(String(14))  # CNPJ do recebedor
    terminal_pagamento = Column(String(8))  # ID do terminal
    cnpj_transacional_pagamento = Column(String(14))  # CNPJ transacional
    uf_pagamento = Column(String(2))  # UF do CNPJ onde pagamento foi processado
    
    # Intermediário da Transação (Marketplace - NT 2019.001)
    cnpj_intermediador = Column(String(14), index=True)  # CNPJ do intermediador (marketplace)
    identificador_intermediador = Column(String(60))  # ID cadastrado no intermediador
    
    # Cobrança
    numero_fatura = Column(String(20))
    valor_original_fatura = Column(Numeric(15, 2))
    valor_desconto_fatura = Column(Numeric(15, 2))
    valor_liquido_fatura = Column(Numeric(15, 2))
    
    # NFe referenciadas
    chaves_nfe_referenciadas = Column(Text)  # JSON array de chaves
    
    # XML completo
    xml_completo = Column(Text)  # XML original completo
    xml_assinatura = Column(Text)  # Assinatura digital
    
    # Relacionamentos
    itens = relationship("NFeItem", back_populates="nfe", cascade="all, delete-orphan")
    duplicatas = relationship("NFeDuplicata", back_populates="nfe", cascade="all, delete-orphan")
    
    # Índices adicionais
    # data_emissao já tem index
    # emitente_cnpj já tem index
    # destinatario_cnpj já tem index


class NFeItem(Base):
    """Itens da Nota Fiscal Eletrônica."""
    __tablename__ = 'nfe_item'

    id = Column(Integer, primary_key=True, index=True)
    nfe_id = Column(Integer, ForeignKey('nfe.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Identificação do item
    numero_item = Column(Integer, nullable=False)
    codigo_produto = Column(String(100), index=True)
    codigo_ean = Column(String(14))
    codigo_ean_tributavel = Column(String(14))
    descricao = Column(Text, nullable=False)
    ncm = Column(String(8), index=True)
    nve = Column(String(20))  # Nomenclatura de Valor Aduaneiro e Estatística
    cest = Column(String(10))  # Código Especificador da Substituição Tributária
    ex_tipi = Column(String(3))
    cfop = Column(String(4), nullable=False, index=True)
    unidade_comercial = Column(String(10))
    quantidade_comercial = Column(Numeric(15, 4))
    valor_unitario_comercial = Column(Numeric(15, 10))
    valor_total_bruto = Column(Numeric(15, 2))
    codigo_ean_comercial = Column(String(14))
    
    # Benefício Fiscal (NT 2021.004)
    codigo_beneficio_fiscal = Column(String(10))  # Código de benefício fiscal na UF
    codigo_beneficio_fiscal_ibs = Column(String(10))  # Código de benefício fiscal IBS
    
    # Crédito Presumido (NT 2023.002)
    codigo_credito_presumido = Column(String(3))  # Código de benefício fiscal de crédito presumido
    percentual_credito_presumido = Column(Numeric(5, 2))  # Percentual do crédito presumido
    valor_credito_presumido = Column(Numeric(15, 2))  # Valor do crédito presumido
    tipo_credito_pres_ibs_zfm = Column(String(1))  # Classificação para subapur. IBS na ZFM
    
    # Indicadores
    indicador_escala_relevante = Column(String(1))  # S=Produzido em escala relevante, N=Não
    cnpj_fabricante = Column(String(14))  # CNPJ do fabricante da mercadoria
    codigo_beneficio_fiscal_uf = Column(String(10))  # Código de benefício fiscal UF (antigo)
    
    # Unidade tributável
    unidade_tributavel = Column(String(10))
    quantidade_tributavel = Column(Numeric(15, 4))
    valor_unitario_tributavel = Column(Numeric(15, 10))
    
    # Valores
    valor_frete = Column(Numeric(15, 2))
    valor_seguro = Column(Numeric(15, 2))
    valor_desconto = Column(Numeric(15, 2))
    valor_outras_despesas = Column(Numeric(15, 2))
    valor_total_item = Column(Numeric(15, 2))
    indicador_total = Column(String(1))  # 0=Não compõe total, 1=Compõe total
    
    # ICMS
    origem_mercadoria = Column(String(1))  # 0=Nacional, 1=Estrangeira, etc
    situacao_tributaria_icms = Column(String(3))  # CST ou CSOSN
    modalidade_bc_icms = Column(String(1))
    base_calculo_icms = Column(Numeric(15, 2))
    aliquota_icms = Column(Numeric(5, 2))
    valor_icms = Column(Numeric(15, 2))
    percentual_reducao_bc_icms = Column(Numeric(5, 2))
    valor_icms_desonerado = Column(Numeric(15, 2))
    motivo_desoneracao_icms = Column(String(2))
    
    # ICMS ST
    modalidade_bc_icms_st = Column(String(1))
    percentual_mva_st = Column(Numeric(5, 2))
    percentual_reducao_bc_icms_st = Column(Numeric(5, 2))
    base_calculo_icms_st = Column(Numeric(15, 2))
    aliquota_icms_st = Column(Numeric(5, 2))
    valor_icms_st = Column(Numeric(15, 2))
    base_calculo_fcp_st = Column(Numeric(15, 2))
    percentual_fcp_st = Column(Numeric(5, 2))
    valor_fcp_st = Column(Numeric(15, 2))
    
    # FCP (Fundo de Combate à Pobreza)
    base_calculo_fcp = Column(Numeric(15, 2))
    percentual_fcp = Column(Numeric(5, 2))
    valor_fcp = Column(Numeric(15, 2))
    
    # ICMS Interestadual
    valor_bcfcp_uf_destino = Column(Numeric(15, 2))
    valor_fcp_uf_destino = Column(Numeric(15, 2))
    percentual_fcp_uf_destino = Column(Numeric(5, 2))
    aliquota_interna_uf_destino = Column(Numeric(5, 2))
    aliquota_interestadual = Column(Numeric(5, 2))
    percentual_partilha = Column(Numeric(5, 2))
    valor_icms_uf_destino = Column(Numeric(15, 2))
    valor_icms_uf_remetente = Column(Numeric(15, 2))
    
    # IPI
    situacao_tributaria_ipi = Column(String(2))
    classe_enquadramento_ipi = Column(String(5))
    codigo_enquadramento_ipi = Column(String(3))
    cnpj_produtor = Column(String(14))
    codigo_selo_ipi = Column(String(60))
    quantidade_selo_ipi = Column(Integer)
    base_calculo_ipi = Column(Numeric(15, 2))
    aliquota_ipi = Column(Numeric(5, 2))
    valor_ipi = Column(Numeric(15, 2))
    
    # PIS
    situacao_tributaria_pis = Column(String(2))
    base_calculo_pis = Column(Numeric(15, 2))
    aliquota_pis = Column(Numeric(5, 4))
    valor_pis = Column(Numeric(15, 2))
    quantidade_vendida_pis = Column(Numeric(15, 4))
    aliquota_pis_reais = Column(Numeric(15, 4))
    
    # COFINS
    situacao_tributaria_cofins = Column(String(2))
    base_calculo_cofins = Column(Numeric(15, 2))
    aliquota_cofins = Column(Numeric(5, 4))
    valor_cofins = Column(Numeric(15, 2))
    quantidade_vendida_cofins = Column(Numeric(15, 4))
    aliquota_cofins_reais = Column(Numeric(15, 4))
    
    # IBS (Imposto sobre Bens e Serviços - Reforma Tributária)
    situacao_tributaria_ibscbs = Column(String(2))
    base_calculo_ibs = Column(Numeric(15, 2))
    aliquota_ibs = Column(Numeric(5, 4))
    valor_ibs = Column(Numeric(15, 2))
    
    # CBS (Contribuição sobre Bens e Serviços - Reforma Tributária)
    base_calculo_cbs = Column(Numeric(15, 2))
    aliquota_cbs = Column(Numeric(5, 4))
    valor_cbs = Column(Numeric(15, 2))
    
    # Importação
    numero_di = Column(String(20))  # Declaração de Importação
    data_di = Column(Date)
    local_desembaraco = Column(String(100))
    uf_desembaraco = Column(String(2))
    data_desembaraco = Column(Date)
    via_transporte = Column(String(2))
    valor_afrmm = Column(Numeric(15, 2))  # Adicional ao Frete para Renovação da Marinha Mercante
    forma_intermediacao = Column(String(1))
    
    # Produto específico
    tipo_produto = Column(String(50))  # combustível, medicamento, veículo, etc
    informacoes_adicionais = Column(Text)
    
    # Rastreabilidade
    numero_lote = Column(String(50))
    data_fabricacao = Column(Date)
    data_validade = Column(Date)
    codigo_agregacao = Column(String(50))
    
    # Relacionamento
    nfe = relationship("NFe", back_populates="itens")


class NFeDuplicata(Base):
    """Duplicatas/Parcelas da Nota Fiscal."""
    __tablename__ = 'nfe_duplicata'

    id = Column(Integer, primary_key=True, index=True)
    nfe_id = Column(Integer, ForeignKey('nfe.id', ondelete='CASCADE'), nullable=False, index=True)
    
    numero_duplicata = Column(String(20))
    data_vencimento = Column(Date)
    valor_duplicata = Column(Numeric(15, 2))
    
    # Relacionamento
    nfe = relationship("NFe", back_populates="duplicatas")


class LogProcessamento(Base):
    """Log detalhado do processamento de cada arquivo."""
    __tablename__ = 'etl_log_processamento'

    id = Column(Integer, primary_key=True, index=True)
    processamento_id = Column(Integer, ForeignKey('etl_processamento.id'))
    
    data_hora = Column(DateTime, default=datetime.now, nullable=False)
    arquivo = Column(String(500), nullable=False)
    chave_acesso = Column(String(44), index=True)
    status = Column(String(20), nullable=False)  # 'sucesso', 'erro', 'duplicado'
    mensagem = Column(Text)
    tempo_processamento = Column(Numeric(10, 3))  # em segundos
    tamanho_arquivo = Column(Integer)  # em bytes


class ArquivoProcessado(Base):
    """Registro de arquivos XML já processados para evitar reprocessamento."""
    __tablename__ = 'etl_arquivo_processado'

    id = Column(Integer, primary_key=True, index=True)
    
    # Identificação do arquivo
    caminho_arquivo = Column(String(500), nullable=False, index=True)
    nome_arquivo = Column(String(255), nullable=False, index=True)
    hash_arquivo = Column(String(64), index=True)  # SHA256 do conteúdo
    tamanho_arquivo = Column(Integer)  # em bytes
    
    # NF-e associada
    chave_acesso = Column(String(44), index=True)
    nfe_id = Column(Integer, ForeignKey('nfe.id'))
    
    # Timestamps
    data_processamento = Column(DateTime, default=datetime.now, nullable=False, index=True)
    data_modificacao_arquivo = Column(DateTime)
    
    # Status
    status = Column(String(20), nullable=False)  # 'processado', 'erro', 'deletado', 'movido'
    caminho_backup = Column(String(500))  # Se foi movido para backup
    deletado = Column(Boolean, default=False)

