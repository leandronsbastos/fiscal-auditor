"""
Módulo de estruturas de dados para o sistema de auditoria fiscal.
Define modelos para documentos, tributos e cálculos com memória de cálculo.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any


class TipoDocumento(Enum):
    """Tipos de documentos fiscais eletrônicos."""
    NFE = "NF-e"
    NFCE = "NFC-e"
    CTE = "CT-e"
    NFSE = "NFS-e"


class TipoMovimento(Enum):
    """Tipo de movimento fiscal."""
    ENTRADA = "Entrada"
    SAIDA = "Saída"


class TipoTributo(Enum):
    """Tipos de tributos."""
    ICMS = "ICMS"
    IPI = "IPI"
    PIS = "PIS"
    COFINS = "COFINS"
    IBS = "IBS"
    CBS = "CBS"


class TipoCredito(Enum):
    """Classificação de créditos fiscais."""
    APROVEITAVEL = "Aproveitável"
    INDEVIDO = "Indevido"
    GLOSAVEL = "Glosável"


@dataclass
class MemoriaCalculo:
    """Memória de cálculo para rastreabilidade."""
    descricao: str
    valores: Dict[str, Any]
    formula: Optional[str] = None
    resultado: Optional[Decimal] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "descricao": self.descricao,
            "valores": {k: str(v) if isinstance(v, Decimal) else v for k, v in self.valores.items()},
            "formula": self.formula,
            "resultado": str(self.resultado) if self.resultado else None,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Tributo:
    """Representa um tributo com seus valores e memória de cálculo."""
    tipo: TipoTributo
    base_calculo: Decimal
    aliquota: Decimal
    valor: Decimal
    cst: Optional[str] = None
    memoria_calculo: Optional[MemoriaCalculo] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "tipo": self.tipo.value,
            "base_calculo": str(self.base_calculo),
            "aliquota": str(self.aliquota),
            "valor": str(self.valor),
            "cst": self.cst,
            "memoria_calculo": self.memoria_calculo.to_dict() if self.memoria_calculo else None
        }


@dataclass
class Item:
    """Item de documento fiscal."""
    codigo: str
    descricao: str
    ncm: str
    cfop: str
    quantidade: Decimal
    valor_unitario: Decimal
    valor_total: Decimal
    tributos: List[Tributo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "codigo": self.codigo,
            "descricao": self.descricao,
            "ncm": self.ncm,
            "cfop": self.cfop,
            "quantidade": str(self.quantidade),
            "valor_unitario": str(self.valor_unitario),
            "valor_total": str(self.valor_total),
            "tributos": [t.to_dict() for t in self.tributos]
        }


@dataclass
class DocumentoFiscal:
    """Documento fiscal eletrônico."""
    tipo: TipoDocumento
    chave: str
    numero: str
    serie: str
    data_emissao: datetime
    cnpj_emitente: str
    cnpj_destinatario: str
    tipo_movimento: TipoMovimento
    valor_total: Decimal
    items: List[Item] = field(default_factory=list)
    tp_nf: Optional[str] = None  # 0=Entrada, 1=Saída
    observacoes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "tipo": self.tipo.value,
            "chave": self.chave,
            "numero": self.numero,
            "serie": self.serie,
            "data_emissao": self.data_emissao.isoformat(),
            "cnpj_emitente": self.cnpj_emitente,
            "cnpj_destinatario": self.cnpj_destinatario,
            "tipo_movimento": self.tipo_movimento.value,
            "valor_total": str(self.valor_total),
            "items": [i.to_dict() for i in self.items],
            "tp_nf": self.tp_nf,
            "observacoes": self.observacoes
        }


@dataclass
class ResultadoValidacao:
    """Resultado da validação tributária."""
    valido: bool
    chave_acesso: str = ""
    mensagens: List[str] = field(default_factory=list)
    creditos_aproveitaveis: List[Tributo] = field(default_factory=list)
    creditos_indevidos: List[Tributo] = field(default_factory=list)
    creditos_glosaveis: List[Tributo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "valido": self.valido,
            "chave_acesso": self.chave_acesso,
            "mensagens": self.mensagens,
            "creditos_aproveitaveis": [c.to_dict() for c in self.creditos_aproveitaveis],
            "creditos_indevidos": [c.to_dict() for c in self.creditos_indevidos],
            "creditos_glosaveis": [c.to_dict() for c in self.creditos_glosaveis]
        }


@dataclass
class ApuracaoTributo:
    """Apuração de um tributo específico."""
    tipo: TipoTributo
    debitos: Decimal
    creditos: Decimal
    saldo: Decimal
    memoria_calculo: MemoriaCalculo

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "tipo": self.tipo.value,
            "debitos": str(self.debitos),
            "creditos": str(self.creditos),
            "saldo": str(self.saldo),
            "memoria_calculo": self.memoria_calculo.to_dict()
        }


@dataclass
class MapaApuracao:
    """Mapa de apuração tributária."""
    periodo: str
    apuracoes: List[ApuracaoTributo] = field(default_factory=list)
    data_geracao: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "periodo": self.periodo,
            "apuracoes": [a.to_dict() for a in self.apuracoes],
            "data_geracao": self.data_geracao.isoformat()
        }
