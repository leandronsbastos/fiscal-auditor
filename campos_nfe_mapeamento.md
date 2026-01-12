# Mapeamento Completo dos Campos NF-e v4.00

Gerado automaticamente a partir do XSD oficial da NF-e

---

## IDE

**Total de campos:** 31

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `cUF` | TCodUfIBGE | Sim | Não | Código da UF do emitente do Documento Fiscal. Utilizar a Tabela do IBGE. |
| `cNF` |  | Sim | Não | Código numérico que compõe a Chave de Acesso. Número aleatório gerado pelo emitente para cada NF-e. |
| `natOp` |  | Sim | Não | Descrição da Natureza da Operação |
| `mod` | TMod | Sim | Não | Código do modelo do Documento Fiscal. 55 = NF-e; 65 = NFC-e. |
| `serie` | TSerie | Sim | Não | Série do Documento Fiscal série normal 0-889 Avulsa Fisco 890-899 SCAN 900-999 |
| `nNF` | TNF | Sim | Não | Número do Documento Fiscal |
| `dhEmi` | TDateTimeUTC | Sim | Não | Data e Hora de emissão do Documento Fiscal (AAAA-MM-DDThh:mm:ssTZD) ex.: 2012-09-01T13:00:00-03:00 |
| `dhSaiEnt` | TDateTimeUTC | Não | Não | Data e Hora da saída ou de entrada da mercadoria / produto (AAAA-MM-DDTHH:mm:ssTZD) |
| `dPrevEntrega` | TData | Não | Não | Data da previsão de entrega ou disponibilização do bem (AAAA-MM-DD) |
| `tpNF` |  | Sim | Não | Tipo do Documento Fiscal (0 - entrada; 1 - saída) |
| `idDest` |  | Sim | Não | Identificador de Local de destino da operação (1-Interna;2-Interestadual;3-Exterior) |
| `cMunFG` | TCodMunIBGE | Sim | Não | Código do Município de Ocorrência do Fato Gerador (utilizar a tabela do IBGE) |
| `cMunFGIBS` | TCodMunIBGE | Não | Não | Informar o município de ocorrência do fato gerador do fato gerador do IBS / CBS. Campo preenchido somente quando “indPres = 5 (Operação presencial, fora do estabelecimento) ”, e não tiver endereço do destinatário (Grupo: E05) ou local de entrega (Grupo: G01). |
| `tpImp` |  | Sim | Não | Formato de impressão do DANFE (0-sem DANFE;1-DANFe Retrato; 2-DANFe Paisagem;3-DANFe Simplificado; 											4-DANFe NFC-e;5-DANFe NFC-e em mensagem eletrônica) |
| `tpEmis` |  | Sim | Não | Forma de emissão da NF-e 1 - Normal; 2 - Contingência FS 3 - Regime Especial NFF (NT 2021.002) 4 - Contingência DPEC 5 - Contingência FSDA 6 - Contingência SVC - AN 7 - Contingência SVC - RS 9 - Contingência off-line NFC-e |
| `cDV` |  | Sim | Não | Digito Verificador da Chave de Acesso da NF-e |
| `tpAmb` | TAmb | Sim | Não | Identificação do Ambiente: 1 - Produção 2 - Homologação |
| `finNFe` | TFinNFe | Sim | Não | Finalidade da emissão da NF-e: 1 - NFe normal 2 - NFe complementar 3 - NFe de ajuste 4 - Devolução/Retorno 5 - Nota de crédito 6 - Nota de débito |
| `tpNFDebito` | TTpNFDebito | Não | Não | Tipo de Nota de Débito |
| `tpNFCredito` | TTpNFCredito | Não | Não | Tipo de Nota de Crédito |
| `indFinal` |  | Sim | Não | Indica operação com consumidor final (0-Não;1-Consumidor Final) |
| `indPres` |  | Sim | Não | Indicador de presença do comprador no estabelecimento comercial no momento da oepração 											(0-Não se aplica (ex.: Nota Fiscal complementar ou de ajuste;1-Operação presencial;2-Não presencial, internet;3-Não presencial, teleatendimento;4-NFC-e entrega em domicílio;5-Operação presencial, fora do estabelecimento;9-Não presencial, outros) |
| `indIntermed` |  | Não | Não | Indicador de intermediador/marketplace  											0=Operação sem intermediador (em site ou plataforma própria)  											1=Operação em site ou plataforma de terceiros (intermediadores/marketplace) |
| `procEmi` | TProcEmi | Sim | Não | Processo de emissão utilizado com a seguinte codificação: 0 - emissão de NF-e com aplicativo do contribuinte; 1 - emissão de NF-e avulsa pelo Fisco; 2 - emissão de NF-e avulsa, pelo contribuinte com seu certificado digital, através do site do Fisco; 3- emissão de NF-e pelo contribuinte com aplicativo fornecido pelo Fisco. |
| `verProc` |  | Sim | Não | versão do aplicativo utilizado no processo de emissão |
| `NFref` |  | Não | Sim | Grupo de infromações da NF referenciada |
| `gCompraGov` | TCompraGov | Não | Não | Grupo de Compras Governamentais |
| `gPagAntecipado` |  | Não | Não | Informado para abater as parcelas de antecipação de pagamento, conforme Art. 10. § 4º |
| `refNFe` | TChNFe | Sim | Sim | Chave de acesso da NF-e de antecipação de pagamento |
| `dhCont` | TDateTimeUTC | Sim | Não | Informar a data e hora de entrada em contingência contingência no formato  (AAAA-MM-DDThh:mm:ssTZD) ex.: 2012-09-01T13:00:00-03:00. |
| `xJust` |  | Sim | Não | Informar a Justificativa da entrada |

---

## EMIT

**Total de campos:** 10

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `xNome` |  | Sim | Não | Razão Social ou Nome do emitente |
| `xFant` |  | Não | Não | Nome fantasia |
| `enderEmit` | TEnderEmi | Sim | Não | Endereço do emitente |
| `IE` | TIe | Sim | Não | Inscrição Estadual do Emitente |
| `IEST` | TIeST | Não | Não | Inscricao Estadual do Substituto Tributário |
| `CRT` |  | Sim | Não | Código de Regime Tributário.  Este campo será obrigatoriamente preenchido com: 1 – Simples Nacional; 2 – Simples Nacional – excesso de sublimite de receita bruta; 3 – Regime Normal. 4 - Simples Nacional - Microempreendedor individual - MEI |
| `IM` |  | Sim | Não | Inscrição Municipal |
| `CNAE` |  | Não | Não | CNAE Fiscal |
| `CNPJ` | TCnpj | Sim | Não | Número do CNPJ do emitente |
| `CPF` | TCpf | Sim | Não | Número do CPF do emitente |

---

## AVULSA

**Total de campos:** 11

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `CNPJ` | TCnpj | Sim | Não | CNPJ do Órgão emissor |
| `xOrgao` |  | Sim | Não | Órgão emitente |
| `matr` |  | Sim | Não | Matrícula do agente |
| `xAgente` |  | Sim | Não | Nome do agente |
| `fone` |  | Não | Não | Telefone |
| `UF` | TUfEmi | Sim | Não | Sigla da Unidade da Federação |
| `nDAR` |  | Não | Não | Número do Documento de Arrecadação de Receita |
| `dEmi` | TData | Não | Não | Data de emissão do DAR (AAAA-MM-DD) |
| `vDAR` | TDec_1302 | Não | Não | Valor Total constante no DAR |
| `repEmi` |  | Sim | Não | Repartição Fiscal emitente |
| `dPag` | TData | Não | Não | Data de pagamento do DAR (AAAA-MM-DD) |

---

## DEST

**Total de campos:** 10

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `xNome` |  | Não | Não | Razão Social ou nome do destinatário |
| `enderDest` | TEndereco | Não | Não | Dados do endereço |
| `indIEDest` |  | Sim | Não | Indicador da IE do destinatário: 1 – Contribuinte ICMSpagamento à vista; 2 – Contribuinte isento de inscrição; 9 – Não Contribuinte |
| `IE` | TIeDestNaoIsento | Não | Não | Inscrição Estadual (obrigatório nas operações com contribuintes do ICMS) |
| `ISUF` |  | Não | Não | Inscrição na SUFRAMA (Obrigatório nas operações com as áreas com benefícios de incentivos fiscais sob controle da SUFRAMA) PL_005d - 11/08/09 - alterado para aceitar 8 ou 9 dígitos |
| `IM` |  | Não | Não | Inscrição Municipal do tomador do serviço |
| `email` |  | Não | Não | Informar o e-mail do destinatário. O campo pode ser utilizado para informar o e-mail de recepção da NF-e indicada pelo destinatário |
| `CNPJ` | TCnpj | Sim | Não | Número do CNPJ |
| `CPF` | TCpf | Sim | Não | Número do CPF |
| `idEstrangeiro` |  | Sim | Não | Identificador do destinatário, em caso de comprador estrangeiro |

---

## DET

**Total de campos:** 203

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `prod` |  | Sim | Não | Dados dos produtos e serviços da NF-e |
| `cProd` |  | Sim | Não | Código do produto ou serviço. Preencher com CFOP caso se trate de itens não relacionados com mercadorias/produto e que o contribuinte não possua codificação própria Formato ”CFOP9999”. |
| `cEAN` |  | Sim | Não | GTIN (Global Trade Item Number) do produto, antigo código EAN ou código de barras |
| `cBarra` |  | Não | Não | Codigo de barras diferente do padrão GTIN |
| `xProd` |  | Sim | Não | Descrição do produto ou serviço |
| `NCM` |  | Sim | Não | Código NCM (8 posições), será permitida a informação do gênero (posição do capítulo do NCM) quando a operação não for de comércio exterior (importação/exportação) ou o produto não seja tributado pelo IPI. Em caso de item de serviço ou item que não tenham produto (Ex. transferência de crédito, crédito do ativo imobilizado, etc.), informar o código 00 (zeros) (v2.0) |
| `NVE` |  | Não | Sim | Nomenclatura de Valor aduaneio e Estatístico |
| `cBenef` |  | Não | Não |  |
| `gCred` |  | Não | Sim | Grupo de informações sobre o CréditoPresumido |
| `cCredPresumido` |  | Sim | Não | Código de Benefício Fiscal de Crédito Presumido na UF aplicado ao item |
| `pCredPresumido` | TDec_0302a04 | Sim | Não | Percentual do Crédito Presumido |
| `vCredPresumido` | TDec_1302 | Sim | Não | Valor do Crédito Presumido |
| `tpCredPresIBSZFM` | TTpCredPresIBSZFM | Não | Não | Classificação para subapuração do IBS na ZFM |
| `EXTIPI` |  | Não | Não | Código EX TIPI (3 posições) |
| `CFOP` |  | Sim | Não | Cfop |
| `uCom` |  | Sim | Não | Unidade comercial |
| `qCom` | TDec_1104v | Sim | Não | Quantidade Comercial  do produto, alterado para aceitar de 0 a 4 casas decimais e 11 inteiros. |
| `vUnCom` | TDec_1110v | Sim | Não | Valor unitário de comercialização  - alterado para aceitar 0 a 10 casas decimais e 11 inteiros |
| `vProd` | TDec_1302 | Sim | Não | Valor bruto do produto ou serviço. |
| `cEANTrib` |  | Sim | Não | GTIN (Global Trade Item Number) da unidade tributável, antigo código EAN ou código de barras |
| `cBarraTrib` |  | Não | Não | Código de barras da unidade tributável diferente do padrão GTIN |
| `uTrib` |  | Sim | Não | Unidade Tributável |
| `qTrib` | TDec_1104v | Sim | Não | Quantidade Tributável - alterado para aceitar de 0 a 4 casas decimais e 11 inteiros |
| `vUnTrib` | TDec_1110v | Sim | Não | Valor unitário de tributação - alterado para aceitar 0 a 10 casas decimais e 11 inteiros |
| `vFrete` | TDec_1302Opc | Não | Não | Valor Total do Frete |
| `vSeg` | TDec_1302Opc | Não | Não | Valor Total do Seguro |
| `vDesc` | TDec_1302Opc | Não | Não | Valor do Desconto |
| `vOutro` | TDec_1302Opc | Não | Não | Outras despesas acessórias |
| `indTot` |  | Sim | Não | Este campo deverá ser preenchido com:  0 – o valor do item (vProd) não compõe o valor total da NF-e (vProd)  1  – o valor do item (vProd) compõe o valor total da NF-e (vProd) |
| `indBemMovelUsado` |  | Não | Não | Indicador de fornecimento de bem móvel usado: 1-Bem Móvel Usado |
| `DI` |  | Não | Sim | Declaração de Importação (NT 2011/004) |
| `nDI` |  | Sim | Não | Número do Documento de Importação (DI, DSI, DIRE, DUImp) (NT2011/004) |
| `dDI` | TData | Sim | Não | Data de registro da DI/DSI/DA (AAAA-MM-DD) |
| `xLocDesemb` |  | Sim | Não | Local do desembaraço aduaneiro |
| `UFDesemb` | TUfEmi | Sim | Não | UF onde ocorreu o desembaraço aduaneiro |
| `dDesemb` | TData | Sim | Não | Data do desembaraço aduaneiro (AAAA-MM-DD) |
| `tpViaTransp` |  | Sim | Não | Via de transporte internacional informada na DI ou na Declaração Única de Importação (DUImp): 																	1-Maritima;2-Fluvial;3-Lacustre;4-Aerea;5-Postal;6-Ferroviaria;7-Rodoviaria;8-Conduto;9-Meios Proprios;10-Entrada/Saida Ficta; 																	11-Courier;12-Em maos;13-Por reboque. |
| `vAFRMM` | TDec_1302 | Não | Não | Valor Adicional ao frete para renovação de marinha mercante |
| `tpIntermedio` |  | Sim | Não | Forma de Importação quanto a intermediação  																	1-por conta propria;2-por conta e ordem;3-encomenda |
| `UFTerceiro` | TUfEmi | Não | Não | Sigla da UF do adquirente ou do encomendante |
| `cExportador` |  | Sim | Não | Código do exportador (usado nos sistemas internos de informação do emitente da NF-e) |
| `adi` |  | Sim | Sim | Adições (NT 2011/004) |
| `nAdicao` |  | Não | Não | Número da Adição |
| `nSeqAdic` |  | Sim | Não | Número seqüencial do item |
| `cFabricante` |  | Sim | Não | Código do fabricante estrangeiro (usado nos sistemas internos de informação do emitente da NF-e) |
| `vDescDI` | TDec_1302Opc | Não | Não | Valor do desconto do item |
| `nDraw` |  | Não | Não | Número do ato concessório de Drawback |
| `CNPJ` | TCnpj | Sim | Não | CNPJ do adquirente ou do encomendante |
| `CPF` | TCpf | Sim | Não | CPF do adquirente ou do encomendante |
| `detExport` |  | Não | Sim | Detalhe da exportação |
| `nDraw` |  | Não | Não | Número do ato concessório de Drawback |
| `exportInd` |  | Não | Não | Exportação indireta |
| `nRE` |  | Sim | Não | Registro de exportação |
| `chNFe` | TChNFe | Sim | Não | Chave de acesso da NF-e recebida para exportação |
| `qExport` | TDec_1104v | Sim | Não | Quantidade do item efetivamente exportado |
| `xPed` |  | Não | Não | pedido de compra - Informação de interesse do emissor para controle do B2B. |
| `nItemPed` |  | Não | Não | Número do Item do Pedido de Compra - Identificação do número do item do pedido de Compra |
| `nFCI` | TGuid | Não | Não | Número de controle da FCI - Ficha de Conteúdo de Importação. |
| `rastro` |  | Não | Sim |  |
| `nLote` |  | Sim | Não | Número do lote do produto. |
| `qLote` | TDec_0803v | Sim | Não | Quantidade de produto no lote. |
| `dFab` | TData | Sim | Não | Data de fabricação/produção. Formato "AAAA-MM-DD". |
| `dVal` | TData | Sim | Não | Data de validade. Informar o último dia do mês caso a validade não especifique o dia. Formato "AAAA-MM-DD". |
| `cAgreg` |  | Não | Não |  |
| `infProdNFF` |  | Não | Não | Informações mais detalhadas do produto (usada na NFF) |
| `cProdFisco` |  | Sim | Não | Código Fiscal do Produto |
| `cOperNFF` |  | Sim | Não | Código da operação selecionada na NFF e relacionada ao item |
| `infProdEmb` |  | Não | Não | Informações mais detalhadas do produto (usada na NFF) |
| `xEmb` |  | Sim | Não | Embalagem do produto |
| `qVolEmb` | TDec_0803v | Sim | Não | Volume do produto na embalagem |
| `uEmb` |  | Sim | Não | Unidade de Medida da Embalagem |
| `CEST` |  | Sim | Não | Codigo especificador da Substuicao Tributaria - CEST, que identifica a mercadoria sujeita aos regimes de  substituicao tributária e de antecipação do recolhimento  do imposto |
| `indEscala` |  | Não | Não |  |
| `CNPJFab` | TCnpj | Não | Não | CNPJ do Fabricante da Mercadoria, obrigatório para produto em escala NÃO relevante. |
| `veicProd` |  | Sim | Não | Veículos novos |
| `tpOp` |  | Sim | Não | Tipo da Operação (1 - Venda concessionária; 2 - Faturamento direto; 3 - Venda direta; 0 - Outros) |
| `chassi` |  | Sim | Não | Chassi do veículo - VIN (código-identificação-veículo) |
| `cCor` |  | Sim | Não | Cor do veículo (código de cada montadora) |
| `xCor` |  | Sim | Não | Descrição da cor |
| `pot` |  | Sim | Não | Potência máxima do motor do veículo em cavalo vapor (CV). (potência-veículo) |
| `cilin` |  | Sim | Não | Capacidade voluntária do motor expressa em centímetros cúbicos (CC). (cilindradas) |
| `pesoL` |  | Sim | Não | Peso líquido |
| `pesoB` |  | Sim | Não | Peso bruto |
| `nSerie` |  | Sim | Não | Serial (série) |
| `tpComb` |  | Sim | Não | Tipo de combustível-Tabela RENAVAM: 01-Álcool; 02-Gasolina; 03-Diesel; 16-Álcool/Gas.; 17-Gas./Álcool/GNV; 18-Gasolina/Elétrico |
| `nMotor` |  | Sim | Não | Número do motor |
| `CMT` |  | Sim | Não | CMT-Capacidade Máxima de Tração - em Toneladas 4 casas decimais |
| `dist` |  | Sim | Não | Distância entre eixos |
| `anoMod` |  | Sim | Não | Ano Modelo de Fabricação |
| `anoFab` |  | Sim | Não | Ano de Fabricação |
| `tpPint` |  | Sim | Não | Tipo de pintura |
| `tpVeic` |  | Sim | Não | Tipo de veículo (utilizar tabela RENAVAM) |
| `espVeic` |  | Sim | Não | Espécie de veículo (utilizar tabela RENAVAM) |
| `VIN` |  | Sim | Não | Informa-se o veículo tem VIN (chassi) remarcado. R-Remarcado N-NormalVIN |
| `condVeic` |  | Sim | Não | Condição do veículo (1 - acabado; 2 - inacabado; 3 - semi-acabado) |
| `cMod` |  | Sim | Não | Código Marca Modelo (utilizar tabela RENAVAM) |
| `cCorDENATRAN` |  | Sim | Não | Código da Cor Segundo as regras de pré-cadastro do DENATRAN: 01-AMARELO;02-AZUL;03-BEGE;04-BRANCA;05-CINZA;06-DOURADA;07-GRENA  08-LARANJA;09-MARROM;10-PRATA;11-PRETA;12-ROSA;13-ROXA;14-VERDE;15-VERMELHA;16-FANTASIA |
| `lota` |  | Sim | Não | Quantidade máxima de permitida de passageiros sentados, inclusive motorista. |
| `tpRest` |  | Sim | Não | Restrição 0 - Não há; 1 - Alienação Fiduciária; 2 - Arrendamento Mercantil; 3 - Reserva de Domínio; 4 - Penhor de Veículos; 9 - outras. |
| `med` |  | Sim | Não | grupo do detalhamento de Medicamentos e de matérias-primas farmacêuticas |
| `cProdANVISA` |  | Sim | Não | Utilizar o número do registro ANVISA  ou preencher com o literal “ISENTO”, no caso de medicamento isento de registro na ANVISA. |
| `xMotivoIsencao` |  | Não | Não | Obs.: Para medicamento isento de registro na ANVISA, informar o número da decisão que o isenta, como por exemplo o número da Resolução da Diretoria Colegiada da ANVISA (RDC). |
| `vPMC` | TDec_1302 | Sim | Não | Preço Máximo ao Consumidor. |
| `arma` |  | Sim | Sim | Armamentos |
| `tpArma` |  | Sim | Não | Indicador do tipo de arma de fogo (0 - Uso permitido; 1 - Uso restrito) |
| `nSerie` |  | Sim | Não | Número de série da arma |
| `nCano` |  | Sim | Não | Número de série do cano |
| `descr` |  | Sim | Não | Descrição completa da arma, compreendendo: calibre, marca, capacidade, tipo de funcionamento, comprimento e demais elementos que permitam a sua perfeita identificação. |
| `comb` |  | Sim | Não | Informar apenas para operações com combustíveis líquidos |
| `cProdANP` |  | Sim | Não | Código de produto da ANP. codificação de produtos do SIMP (http://www.anp.gov.br) |
| `descANP` |  | Sim | Não | Descrição do Produto conforme ANP. Utilizar a descrição de produtos do Sistema de Informações de Movimentação de Produtos - SIMP (http://www.anp.gov.br/simp/). |
| `pGLP` | TDec_0302a04Max100 | Não | Não | Percentual do GLP derivado do petróleo no produto GLP (cProdANP=210203001). Informar em número decimal o percentual do GLP derivado de petróleo no produto GLP. Valores 0 a 100. |
| `pGNn` | TDec_0302a04Max100 | Não | Não | Percentual de gás natural nacional - GLGNn para o produto GLP (cProdANP=210203001). Informar em número decimal o percentual do Gás Natural Nacional - GLGNn para o produto GLP. Valores de 0 a 100. |
| `pGNi` | TDec_0302a04Max100 | Não | Não | Percentual de gás natural importado GLGNi para o produto GLP (cProdANP=210203001). Informar em número deciaml o percentual do Gás Natural Importado - GLGNi para o produto GLP. Valores de 0 a 100. |
| `vPart` | TDec_1302 | Não | Não | Valor de partida (cProdANP=210203001). Deve ser informado neste campo o valor por quilograma sem ICMS. |
| `CODIF` |  | Não | Não | Código de autorização / registro do CODIF. Informar apenas quando a UF utilizar o CODIF (Sistema de Controle do 			Diferimento do Imposto nas Operações com AEAC - Álcool Etílico Anidro Combustível). |
| `qTemp` | TDec_1204temperatura | Não | Não | Quantidade de combustível faturada à temperatura ambiente. Informar quando a quantidade faturada informada no campo qCom (I10) tiver sido ajustada para uma temperatura diferente da ambiente. |
| `UFCons` | TUf | Sim | Não | Sigla da UF de Consumo |
| `CIDE` |  | Não | Não | CIDE Combustíveis |
| `qBCProd` | TDec_1204v | Sim | Não | BC do CIDE ( Quantidade comercializada) |
| `vAliqProd` | TDec_1104 | Sim | Não | Alíquota do CIDE  (em reais) |
| `vCIDE` | TDec_1302 | Sim | Não | Valor do CIDE |
| `encerrante` |  | Não | Não | Informações do grupo de "encerrante" |
| `nBico` |  | Sim | Não | Numero de identificação do Bico utilizado no abastecimento |
| `nBomba` |  | Não | Não | Numero de identificação da bomba ao qual o bico está interligado |
| `nTanque` |  | Sim | Não | Numero de identificação do tanque ao qual o bico está interligado |
| `vEncIni` | TDec_1203 | Sim | Não | Valor do Encerrante no ínicio do abastecimento |
| `vEncFin` | TDec_1203 | Sim | Não | Valor do Encerrante no final do abastecimento |
| `pBio` | TDec_03v00a04Max100Opc | Não | Não | Percentual do índice de mistura do Biodiesel (B100) no Óleo Diesel B instituído pelo órgão regulamentador |
| `origComb` |  | Não | Sim | Grupo indicador da origem do combustível |
| `indImport` |  | Sim | Não | Indicador de importação 0=Nacional; 1=Importado; |
| `cUFOrig` | TCodUfIBGE | Sim | Não | UF de origem do produtor ou do importado |
| `pOrig` | TDec_03v00a04Max100Opc | Sim | Não | Percentual originário para a UF |
| `nRECOPI` |  | Sim | Não | Número do RECOPI |
| `imposto` |  | Sim | Não | Tributos incidentes nos produtos ou serviços da NF-e |
| `vTotTrib` | TDec_1302 | Não | Não | Valor estimado total de impostos federais, estaduais e municipais |
| `PIS` |  | Não | Não | Dados do PIS |
| `PISST` |  | Não | Não | Dados do PIS Substituição Tributária |
| `vPIS` | TDec_1302 | Sim | Não | Valor do PIS ST |
| `indSomaPISST` |  | Não | Não | Indica se o valor do PISST compõe o valor total da NF-e |
| `vBC` | TDec_1302Opc | Sim | Não | Valor da BC do PIS ST |
| `pPIS` | TDec_0302a04 | Sim | Não | Alíquota do PIS ST (em percentual) |
| `qBCProd` | TDec_1204 | Sim | Não | Quantidade Vendida |
| `vAliqProd` | TDec_1104 | Sim | Não | Alíquota do PIS ST (em reais) |
| `COFINS` |  | Não | Não | Dados do COFINS |
| `COFINSST` |  | Não | Não | Dados do COFINS da Substituição Tributaria; |
| `vCOFINS` | TDec_1302 | Sim | Não | Valor do COFINS ST |
| `indSomaCOFINSST` |  | Não | Não | Indica se o valor da COFINS ST compõe o valor total da NFe |
| `vBC` | TDec_1302 | Sim | Não | Valor da BC do COFINS ST |
| `pCOFINS` | TDec_0302a04 | Sim | Não | Alíquota do COFINS ST(em percentual) |
| `qBCProd` | TDec_1204 | Sim | Não | Quantidade Vendida |
| `vAliqProd` | TDec_1104 | Sim | Não | Alíquota do COFINS ST(em reais) |
| `ICMSUFDest` |  | Não | Não | Grupo a ser informado nas vendas interestarduais para consumidor final, não contribuinte de ICMS |
| `vBCUFDest` | TDec_1302 | Sim | Não | Valor da Base de Cálculo do ICMS na UF do destinatário. |
| `vBCFCPUFDest` | TDec_1302 | Não | Não | Valor da Base de Cálculo do FCP na UF do destinatário. |
| `pFCPUFDest` | TDec_0302a04 | Não | Não | Percentual adicional inserido na alíquota interna da UF de destino, relativo ao Fundo de Combate à Pobreza (FCP) naquela UF. |
| `pICMSUFDest` | TDec_0302a04 | Sim | Não | Alíquota adotada nas operações internas na UF do destinatário para o produto / mercadoria. |
| `pICMSInter` |  | Sim | Não | Alíquota interestadual das UF envolvidas: - 4% alíquota interestadual para produtos importados; - 7% para os Estados de origem do Sul e Sudeste (exceto ES), destinado para os Estados do Norte e Nordeste  ou ES; - 12% para os demais casos. |
| `pICMSInterPart` | TDec_0302a04 | Sim | Não | Percentual de partilha para a UF do destinatário: - 40% em 2016; - 60% em 2017; - 80% em 2018; - 100% a partir de 2019. |
| `vFCPUFDest` | TDec_1302 | Não | Não | Valor do ICMS relativo ao Fundo de Combate à Pobreza (FCP) da UF de destino. |
| `vICMSUFDest` | TDec_1302 | Sim | Não | Valor do ICMS de partilha para a UF do destinatário. |
| `vICMSUFRemet` | TDec_1302 | Sim | Não | Valor do ICMS de partilha para a UF do remetente. Nota: A partir de 2019, este valor será zero. |
| `IS` | TIS | Não | Não | Grupo de informações do Imposto Seletivo |
| `IBSCBS` | TTribNFe | Não | Não | Grupo de informações dos tributos IBS, CBS e Imposto Seletivo |
| `ICMS` |  | Sim | Não | Dados do ICMS Normal e ST |
| `IPI` | TIpi | Não | Não |  |
| `II` |  | Não | Não | Dados do Imposto de Importação |
| `vBC` | TDec_1302 | Sim | Não | Base da BC do Imposto de Importação |
| `vDespAdu` | TDec_1302 | Sim | Não | Valor das despesas aduaneiras |
| `vII` | TDec_1302 | Sim | Não | Valor do Imposto de Importação |
| `vIOF` | TDec_1302 | Sim | Não | Valor do Imposto sobre Operações Financeiras |
| `IPI` | TIpi | Não | Não |  |
| `ISSQN` |  | Sim | Não | ISSQN |
| `vBC` | TDec_1302 | Sim | Não | Valor da BC do ISSQN |
| `vAliq` | TDec_0302a04 | Sim | Não | Alíquota do ISSQN |
| `vISSQN` | TDec_1302 | Sim | Não | Valor da do ISSQN |
| `cMunFG` | TCodMunIBGE | Sim | Não | Informar o município de ocorrência do fato gerador do ISSQN. Utilizar a Tabela do IBGE (Anexo VII - Tabela de UF, Município e País). “Atenção, não vincular com os campos B12, C10 ou E10” v2.0 |
| `cListServ` | TCListServ | Sim | Não | Informar o Item da lista de serviços da LC 116/03 em que se classifica o serviço. |
| `vDeducao` | TDec_1302Opc | Não | Não | Valor dedução para redução da base de cálculo |
| `vOutro` | TDec_1302Opc | Não | Não | Valor outras retenções |
| `vDescIncond` | TDec_1302Opc | Não | Não | Valor desconto incondicionado |
| `vDescCond` | TDec_1302Opc | Não | Não | Valor desconto condicionado |
| `vISSRet` | TDec_1302Opc | Não | Não | Valor Retenção ISS |
| `indISS` |  | Sim | Não | Exibilidade do ISS:1-Exigível;2-Não incidente;3-Isenção;4-Exportação;5-Imunidade;6-Exig.Susp. Judicial;7-Exig.Susp. ADM |
| `cServico` |  | Não | Não | Código do serviço prestado dentro do município |
| `cMun` | TCodMunIBGE | Não | Não | Código do Município de Incidência do Imposto |
| `cPais` |  | Não | Não | Código de Pais |
| `nProcesso` |  | Não | Não | Número do Processo administrativo ou judicial de suspenção do processo |
| `indIncentivo` |  | Sim | Não | Indicador de Incentivo Fiscal. 1=Sim; 2=Não |
| `impostoDevol` |  | Não | Não |  |
| `pDevol` | TDec_0302Max100 | Sim | Não | Percentual de mercadoria devolvida |
| `IPI` |  | Sim | Não | Informação de IPI devolvido |
| `vIPIDevol` | TDec_1302 | Sim | Não | Valor do IPI devolvido |
| `infAdProd` |  | Não | Não | Informações adicionais do produto (norma referenciada, informações complementares, etc) |
| `obsItem` |  | Não | Não | Grupo de observações de uso livre (para o item da NF-e) |
| `obsCont` |  | Não | Não | Grupo de observações de uso livre (para o item da NF-e) |
| `xTexto` |  | Sim | Não |  |
| `obsFisco` |  | Não | Não | Grupo de observações de uso livre (para o item da NF-e) |
| `xTexto` |  | Sim | Não |  |
| `vItem` | TDec_1302 | Não | Não | Valor total do Item, correspondente à sua participação no total da nota. A soma dos itens deverá corresponder ao total da nota. |
| `DFeReferenciado` |  | Não | Não | Referenciamento de item de outros DFe |
| `chaveAcesso` | TChNFe | Sim | Não | Chave de Acesso do DFe referenciado |
| `nItem` |  | Não | Não | Número do item do documento referenciado. Corresponde ao atributo nItem do elemento det do documento original. |

---

## TOTAL

**Total de campos:** 54

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `ICMSTot` |  | Sim | Não | Totais referentes ao ICMS |
| `vBC` | TDec_1302 | Sim | Não | BC do ICMS |
| `vICMS` | TDec_1302 | Sim | Não | Valor Total do ICMS |
| `vICMSDeson` | TDec_1302 | Sim | Não | Valor Total do ICMS desonerado |
| `vFCPUFDest` | TDec_1302 | Não | Não | Valor total do ICMS relativo ao Fundo de Combate à Pobreza (FCP) para a UF de destino. |
| `vICMSUFDest` | TDec_1302 | Não | Não | Valor total do ICMS de partilha para a UF do destinatário |
| `vICMSUFRemet` | TDec_1302 | Não | Não | Valor total do ICMS de partilha para a UF do remetente |
| `vFCP` | TDec_1302 | Sim | Não | Valor Total do FCP (Fundo de Combate à Pobreza). |
| `vBCST` | TDec_1302 | Sim | Não | BC do ICMS ST |
| `vST` | TDec_1302 | Sim | Não | Valor Total do ICMS ST |
| `vFCPST` | TDec_1302 | Sim | Não | Valor Total do FCP (Fundo de Combate à Pobreza) retido por substituição tributária. |
| `vFCPSTRet` | TDec_1302 | Sim | Não | Valor Total do FCP (Fundo de Combate à Pobreza) retido anteriormente por substituição tributária. |
| `qBCMono` | TDec_1302 | Não | Não | Valor total da quantidade tributada do ICMS monofásico próprio |
| `vICMSMono` | TDec_1302 | Não | Não | Valor total do ICMS monofásico próprio |
| `qBCMonoReten` | TDec_1302 | Não | Não | Valor total da quantidade tributada do ICMS monofásico sujeito a retenção |
| `vICMSMonoReten` | TDec_1302 | Não | Não | Valor total do ICMS monofásico sujeito a retenção |
| `qBCMonoRet` | TDec_1302 | Não | Não | Valor total da quantidade tributada do ICMS monofásico retido anteriormente |
| `vICMSMonoRet` | TDec_1302 | Não | Não | Valor do ICMS monofásico retido anteriormente |
| `vProd` | TDec_1302 | Sim | Não | Valor Total dos produtos e serviços |
| `vFrete` | TDec_1302 | Sim | Não | Valor Total do Frete |
| `vSeg` | TDec_1302 | Sim | Não | Valor Total do Seguro |
| `vDesc` | TDec_1302 | Sim | Não | Valor Total do Desconto |
| `vII` | TDec_1302 | Sim | Não | Valor Total do II |
| `vIPI` | TDec_1302 | Sim | Não | Valor Total do IPI |
| `vIPIDevol` | TDec_1302 | Sim | Não | Valor Total do IPI devolvido. Deve ser informado quando preenchido o Grupo Tributos Devolvidos na emissão de nota finNFe=4 (devolução) nas operações com não contribuintes do IPI. Corresponde ao total da soma dos campos id: UA04. |
| `vPIS` | TDec_1302 | Sim | Não | Valor do PIS |
| `vCOFINS` | TDec_1302 | Sim | Não | Valor do COFINS |
| `vOutro` | TDec_1302 | Sim | Não | Outras Despesas acessórias |
| `vNF` | TDec_1302 | Sim | Não | Valor Total da NF-e |
| `vTotTrib` | TDec_1302 | Não | Não | Valor estimado total de impostos federais, estaduais e municipais |
| `ISSQNtot` |  | Não | Não | Totais referentes ao ISSQN |
| `vServ` | TDec_1302Opc | Não | Não | Valor Total dos Serviços sob não-incidência ou não tributados pelo ICMS |
| `vBC` | TDec_1302Opc | Não | Não | Base de Cálculo do ISS |
| `vISS` | TDec_1302Opc | Não | Não | Valor Total do ISS |
| `vPIS` | TDec_1302Opc | Não | Não | Valor do PIS sobre serviços |
| `vCOFINS` | TDec_1302Opc | Não | Não | Valor do COFINS sobre serviços |
| `dCompet` | TData | Sim | Não | Data da prestação do serviço  (AAAA-MM-DD) |
| `vDeducao` | TDec_1302Opc | Não | Não | Valor dedução para redução da base de cálculo |
| `vOutro` | TDec_1302Opc | Não | Não | Valor outras retenções |
| `vDescIncond` | TDec_1302Opc | Não | Não | Valor desconto incondicionado |
| `vDescCond` | TDec_1302Opc | Não | Não | Valor desconto condicionado |
| `vISSRet` | TDec_1302Opc | Não | Não | Valor Total Retenção ISS |
| `cRegTrib` |  | Não | Não | Código do regime especial de tributação |
| `retTrib` |  | Não | Não | Retenção de Tributos Federais |
| `vRetPIS` | TDec_1302Opc | Não | Não | Valor Retido de PIS |
| `vRetCOFINS` | TDec_1302Opc | Não | Não | Valor Retido de COFINS |
| `vRetCSLL` | TDec_1302Opc | Não | Não | Valor Retido de CSLL |
| `vBCIRRF` | TDec_1302Opc | Não | Não | Base de Cálculo do IRRF |
| `vIRRF` | TDec_1302Opc | Não | Não | Valor Retido de IRRF |
| `vBCRetPrev` | TDec_1302Opc | Não | Não | Base de Cálculo da Retenção da Previdêncica Social |
| `vRetPrev` | TDec_1302Opc | Não | Não | Valor da Retenção da Previdêncica Social |
| `ISTot` | TISTot | Não | Não | Valores totais da NF com Imposto Seletivo |
| `IBSCBSTot` | TIBSCBSMonoTot | Não | Não | Valores totais da NF com IBS / CBS |
| `vNFTot` | TDec_1302Opc | Não | Não | Valor Total da NF considerando os impostos por fora IBS, CBS e IS |

---

## TRANSP

**Total de campos:** 29

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `modFrete` |  | Sim | Não | Modalidade do frete 0- Contratação do Frete por conta do Remetente (CIF); 1- Contratação do Frete por conta do destinatário/remetente (FOB); 2- Contratação do Frete por conta de terceiros; 3- Transporte próprio por conta do remetente; 4- Transporte próprio por conta do destinatário; 9- Sem Ocorrência de transporte. |
| `transporta` |  | Não | Não | Dados do transportador |
| `xNome` |  | Não | Não | Razão Social ou nome do transportador |
| `IE` | TIeDest | Não | Não | Inscrição Estadual (v2.0) |
| `xEnder` |  | Não | Não | Endereço completo |
| `xMun` |  | Não | Não | Nome do munícipio |
| `UF` | TUf | Não | Não | Sigla da UF |
| `CNPJ` | TCnpj | Sim | Não | CNPJ do transportador |
| `CPF` | TCpf | Sim | Não | CPF do transportador |
| `retTransp` |  | Não | Não | Dados da retenção  ICMS do Transporte |
| `vServ` | TDec_1302 | Sim | Não | Valor do Serviço |
| `vBCRet` | TDec_1302 | Sim | Não | BC da Retenção do ICMS |
| `pICMSRet` | TDec_0302a04 | Sim | Não | Alíquota da Retenção |
| `vICMSRet` | TDec_1302 | Sim | Não | Valor do ICMS Retido |
| `CFOP` |  | Sim | Não | Código Fiscal de Operações e Prestações |
| `cMunFG` | TCodMunIBGE | Sim | Não | Código do Município de Ocorrência do Fato Gerador (utilizar a tabela do IBGE) |
| `vol` |  | Não | Sim | Dados dos volumes |
| `qVol` |  | Não | Não | Quantidade de volumes transportados |
| `esp` |  | Não | Não | Espécie dos volumes transportados |
| `marca` |  | Não | Não | Marca dos volumes transportados |
| `nVol` |  | Não | Não | Numeração dos volumes transportados |
| `pesoL` | TDec_1203 | Não | Não | Peso líquido (em kg) |
| `pesoB` | TDec_1203 | Não | Não | Peso bruto (em kg) |
| `lacres` |  | Não | Sim |  |
| `nLacre` |  | Sim | Não | Número dos Lacres |
| `vagao` |  | Não | Não | Identificação do vagão (v2.0) |
| `balsa` |  | Não | Não | Identificação da balsa (v2.0) |
| `veicTransp` | TVeiculo | Não | Não | Dados do veículo |
| `reboque` | TVeiculo | Não | Sim | Dados do reboque/Dolly (v2.0) |

---

## COBR

**Total de campos:** 9

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `fat` |  | Não | Não | Dados da fatura |
| `nFat` |  | Não | Não | Número da fatura |
| `vOrig` | TDec_1302 | Não | Não | Valor original da fatura |
| `vDesc` | TDec_1302 | Não | Não | Valor do desconto da fatura |
| `vLiq` | TDec_1302 | Não | Não | Valor líquido da fatura |
| `dup` |  | Não | Sim | Dados das duplicatas NT 2011/004 |
| `nDup` |  | Não | Não | Número da duplicata |
| `dVenc` | TData | Não | Não | Data de vencimento da duplicata (AAAA-MM-DD) |
| `vDup` | TDec_1302Opc | Sim | Não | Valor da duplicata |

---

## PAG

**Total de campos:** 16

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `detPag` |  | Sim | Sim | Grupo de detalhamento da forma de pagamento. |
| `indPag` |  | Não | Não | Indicador da Forma de Pagamento:0-Pagamento à Vista;1-Pagamento à Prazo; |
| `tPag` |  | Sim | Não | Forma de Pagamento: |
| `xPag` |  | Não | Não | Descrição do Meio de Pagamento |
| `vPag` | TDec_1302 | Sim | Não | Valor do Pagamento. Esta tag poderá ser omitida quando a tag tPag=90 (Sem Pagamento), caso contrário deverá ser preenchida. |
| `dPag` | TData | Não | Não | Data do Pagamento |
| `card` |  | Não | Não | Grupo de Cartões, PIX, Boletos e outros Pagamentos Eletrônicos |
| `tpIntegra` |  | Sim | Não | Tipo de Integração do processo de pagamento com o sistema de automação da empresa: 1 - Pagamento integrado com o sistema de automação da empresa (Ex.: equipamento TEF, Comércio Eletrônico, POS Integrado); 2 - Pagamento não integrado com o sistema de automação da empresa (Ex.: equipamento POS Simples). |
| `CNPJ` | TCnpj | Não | Não | CNPJ da instituição de pagamento |
| `tBand` |  | Não | Não | Bandeira da operadora de cartão |
| `cAut` |  | Não | Não | Número de autorização da operação com cartões, PIX, boletos e outros pagamentos eletrônicos |
| `CNPJReceb` | TCnpj | Não | Não | CNPJ do beneficiário do pagamento |
| `idTermPag` |  | Não | Não | Identificador do terminal de pagamento |
| `CNPJPag` | TCnpj | Sim | Não | CNPJ transacional do pagamento - Preencher informando o CNPJ do estabelecimento onde o pagamento foi processado/transacionado/recebido quando a emissão do documento fiscal ocorrer em estabelecimento distinto |
| `UFPag` | TUfEmi | Sim | Não | UF do CNPJ do estabelecimento onde o pagamento foi processado/transacionado/recebido. |
| `vTroco` | TDec_1302 | Não | Não | Valor do Troco. |

---

## INFINTERMED

**Total de campos:** 2

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `CNPJ` | TCnpj | Sim | Não | CNPJ do Intermediador da Transação (agenciador, plataforma de delivery, marketplace e similar) de serviços e de negócios. |
| `idCadIntTran` |  | Sim | Não | Identificador cadastrado no intermediador |

---

## INFADIC

**Total de campos:** 10

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `infAdFisco` |  | Não | Não | Informações adicionais de interesse do Fisco (v2.0) |
| `infCpl` |  | Não | Não | Informações complementares de interesse do Contribuinte |
| `obsCont` |  | Não | Sim | Campo de uso livre do contribuinte informar o nome do campo no atributo xCampo e o conteúdo do campo no xTexto |
| `xTexto` |  | Sim | Não |  |
| `obsFisco` |  | Não | Sim | Campo de uso exclusivo do Fisco informar o nome do campo no atributo xCampo e o conteúdo do campo no xTexto |
| `xTexto` |  | Sim | Não |  |
| `procRef` |  | Não | Sim | Grupo de informações do  processo referenciado |
| `nProc` |  | Sim | Não | Indentificador do processo ou ato concessório |
| `indProc` |  | Sim | Não | Origem do processo, informar com: 0 - SEFAZ; 1 - Justiça Federal; 2 - Justiça Estadual; 3 - Secex/RFB; 4 - CONFAZ; 9 - Outros. |
| `tpAto` |  | Não | Não | Tipo do ato concessório 														Para origem do Processo na SEFAZ (indProc=0), informar o tipo de ato concessório: 08 - Termo de Acordo; 10 - Regime Especial; 12 - Autorização específica; 14 - Ajuste SINIEF; 15 - Convênio ICMS. |

---

## EXPORTA

**Total de campos:** 3

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `UFSaidaPais` | TUfEmi | Sim | Não | Sigla da UF de Embarque ou de transposição de fronteira |
| `xLocExporta` |  | Sim | Não | Local de Embarque ou de transposição de fronteira |
| `xLocDespacho` |  | Não | Não | Descrição do local de despacho |

---

## COMPRA

**Total de campos:** 3

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `xNEmp` |  | Não | Não | Informação da Nota de Empenho de compras públicas (NT2011/004) |
| `xPed` |  | Não | Não | Informação do pedido |
| `xCont` |  | Não | Não | Informação do contrato |

---

## CANA

**Total de campos:** 13

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `safra` |  | Sim | Não | Identificação da safra |
| `ref` |  | Sim | Não | Mês e Ano de Referência, formato: MM/AAAA |
| `forDia` |  | Sim | Sim | Fornecimentos diários |
| `qtde` | TDec_1110v | Sim | Não | Quantidade em quilogramas - peso líquido |
| `qTotMes` | TDec_1110v | Sim | Não | Total do mês |
| `qTotAnt` | TDec_1110v | Sim | Não | Total Anterior |
| `qTotGer` | TDec_1110v | Sim | Não | Total Geral |
| `deduc` |  | Não | Sim | Deduções - Taxas e Contribuições |
| `xDed` |  | Sim | Não | Descrição da Dedução |
| `vDed` | TDec_1302 | Sim | Não | valor da dedução |
| `vFor` | TDec_1302 | Sim | Não | Valor  dos fornecimentos |
| `vTotDed` | TDec_1302 | Sim | Não | Valor Total das Deduções |
| `vLiqFor` | TDec_1302 | Sim | Não | Valor Líquido dos fornecimentos |

---

## INFSOLICNFF

**Total de campos:** 1

| Campo | Tipo | Obrigatório | Múltiplo | Documentação |
|-------|------|-------------|----------|-------------|
| `xSolic` |  | Sim | Não | Solicitação do pedido de emissão da NFF |

---

