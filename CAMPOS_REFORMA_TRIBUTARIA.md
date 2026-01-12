# Campos da Reforma Tributária - IBS e CBS

## Visão Geral

Este documento descreve a implementação dos campos relacionados à **Reforma Tributária** no sistema Fiscal Auditor, especificamente os novos impostos **IBS** (Imposto sobre Bens e Serviços) e **CBS** (Contribuição sobre Bens e Serviços).

## Alterações Realizadas

### 1. Extrator XML (`etl_service/extractor.py`)

Adicionada extração dos campos IBS e CBS dos arquivos XML:

```python
# IBS e CBS (Reforma Tributária)
ibscbs = imposto.find('nfe:IBSCBS', self.NAMESPACES)
if ibscbs is not None:
    impostos_data['ibscbs'] = {
        'situacao_tributaria': ...,
        'ibs': {
            'base_calculo': ...,
            'aliquota': ...,
            'valor': ...
        },
        'cbs': {
            'base_calculo': ...,
            'aliquota': ...,
            'valor': ...
        }
    }
```

**Campos extraídos:**
- Situação tributária (CST)
- Base de cálculo (IBS e CBS)
- Alíquota (IBS e CBS)
- Valor do imposto (IBS e CBS)

### 2. Modelos do Banco de Dados (`etl_service/models.py`)

#### Tabela `nfe` (Totalizadores)
Novos campos adicionados:
- `valor_ibs`: Total de IBS da nota
- `valor_cbs`: Total de CBS da nota

#### Tabela `nfe_item` (Itens)
Novos campos adicionados:
- `situacao_tributaria_ibscbs`: CST do IBS/CBS
- `base_calculo_ibs`: Base de cálculo do IBS
- `aliquota_ibs`: Alíquota do IBS
- `valor_ibs`: Valor do IBS
- `base_calculo_cbs`: Base de cálculo do CBS
- `aliquota_cbs`: Alíquota do CBS
- `valor_cbs`: Valor do CBS

### 3. Transformador (`etl_service/transformer.py`)

Adicionado mapeamento dos dados extraídos para os modelos do banco:

**Para totalizadores (NFe):**
```python
valor_ibs=self._to_decimal(totais.get('valor_ibs')),
valor_cbs=self._to_decimal(totais.get('valor_cbs')),
```

**Para itens (NFeItem):**
```python
situacao_tributaria_ibscbs=impostos.get('ibscbs', {}).get('situacao_tributaria'),
base_calculo_ibs=self._to_decimal(impostos.get('ibscbs', {}).get('ibs', {}).get('base_calculo')),
aliquota_ibs=self._to_decimal(impostos.get('ibscbs', {}).get('ibs', {}).get('aliquota')),
valor_ibs=self._to_decimal(impostos.get('ibscbs', {}).get('ibs', {}).get('valor')),
base_calculo_cbs=self._to_decimal(impostos.get('ibscbs', {}).get('cbs', {}).get('base_calculo')),
aliquota_cbs=self._to_decimal(impostos.get('ibscbs', {}).get('cbs', {}).get('aliquota')),
valor_cbs=self._to_decimal(impostos.get('ibscbs', {}).get('cbs', {}).get('valor')),
```

### 4. Migração do Banco de Dados

**Arquivo:** `etl_service/migrations/002_adicionar_campos_reforma_tributaria.sql`

Script SQL para adicionar as novas colunas nas tabelas existentes.

## Como Aplicar as Mudanças

### Passo 1: Executar a Migração

Execute o script de migração para adicionar os campos no banco de dados:

```bash
python executar_migracao_reforma.py
```

Ou execute manualmente o SQL:

```bash
python
>>> from etl_service.database import get_engine
>>> from sqlalchemy import text
>>> engine = get_engine()
>>> with open('etl_service/migrations/002_adicionar_campos_reforma_tributaria.sql', 'r') as f:
...     sql = f.read()
>>> with engine.connect() as conn:
...     for cmd in sql.split(';'):
...         if cmd.strip():
...             conn.execute(text(cmd))
...     conn.commit()
```

### Passo 2: Reprocessar XMLs (Opcional)

Se você já tem XMLs processados e quer atualizar os dados com IBS/CBS:

```bash
python run_etl.py --diretorio "caminho/para/xmls" --tipo incremental
```

## Estrutura XML Esperada

Os campos IBS/CBS devem estar no XML da NFe dentro da tag de impostos de cada item:

```xml
<imposto>
    <IBSCBS>
        <CST>00</CST>
        <IBS>
            <vBC>1000.00</vBC>
            <pAliq>12.50</pAliq>
            <vIBS>125.00</vIBS>
        </IBS>
        <CBS>
            <vBC>1000.00</vBC>
            <pAliq>10.00</pAliq>
            <vCBS>100.00</vCBS>
        </CBS>
    </IBSCBS>
</imposto>
```

E nos totalizadores:

```xml
<total>
    <ICMSTot>
        <!-- ... outros campos ... -->
        <vIBS>125.00</vIBS>
        <vCBS>100.00</vCBS>
    </ICMSTot>
</total>
```

## Consultas SQL Úteis

### Verificar documentos com IBS/CBS

```sql
-- Contar notas com IBS/CBS
SELECT 
    COUNT(*) as total_notas,
    SUM(CASE WHEN valor_ibs IS NOT NULL AND valor_ibs > 0 THEN 1 ELSE 0 END) as com_ibs,
    SUM(CASE WHEN valor_cbs IS NOT NULL AND valor_cbs > 0 THEN 1 ELSE 0 END) as com_cbs
FROM nfe;

-- Listar itens com IBS/CBS
SELECT 
    n.numero_nota,
    n.data_emissao,
    i.descricao,
    i.valor_ibs,
    i.valor_cbs
FROM nfe_item i
JOIN nfe n ON i.nfe_id = n.id
WHERE i.valor_ibs IS NOT NULL OR i.valor_cbs IS NOT NULL
ORDER BY n.data_emissao DESC;

-- Totalizadores por período
SELECT 
    DATE_TRUNC('month', data_emissao) as mes,
    SUM(valor_ibs) as total_ibs,
    SUM(valor_cbs) as total_cbs
FROM nfe
WHERE valor_ibs IS NOT NULL OR valor_cbs IS NOT NULL
GROUP BY mes
ORDER BY mes DESC;
```

## Observações Importantes

1. **Compatibilidade**: Os campos são **opcionais** (nullable), portanto XMLs antigos sem IBS/CBS continuarão funcionando normalmente.

2. **Reforma em Transição**: A reforma tributária está em fase de transição, então nem todos os XMLs terão esses campos preenchidos.

3. **Validação**: O sistema não valida a presença obrigatória de IBS/CBS. Se os campos estiverem no XML, serão extraídos e armazenados.

4. **Performance**: A adição desses campos não impacta a performance do sistema, pois são apenas colunas adicionais nas tabelas existentes.

## Próximos Passos

Para utilizar esses dados na interface web e relatórios, será necessário:

1. Atualizar o módulo `datalake_integration.py` para incluir IBS/CBS nas consultas
2. Atualizar os modelos Pydantic em `fiscal_auditor/models.py`
3. Atualizar os cálculos em `fiscal_auditor/calculator.py`
4. Adicionar IBS/CBS nos relatórios (`fiscal_auditor/reports.py`)
5. Atualizar os templates HTML para exibir esses valores

---

**Data da implementação:** 12/01/2026
**Versão do sistema:** 1.1.0
