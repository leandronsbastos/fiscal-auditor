"""
Fiscal Auditor - Sistema modular para auditoria e apuração tributária.
"""

__version__ = "0.1.0"

from .models import (
    TipoDocumento,
    TipoMovimento,
    TipoTributo,
    TipoCredito,
    DocumentoFiscal,
    Item,
    Tributo,
    ResultadoValidacao,
    ApuracaoTributo,
    MapaApuracao,
    MemoriaCalculo,
)

from .xml_reader import XMLReader
from .validator import ValidadorTributario
from .calculator import ApuradorTributario
from .reports import GeradorRelatorios

__all__ = [
    # Modelos
    "TipoDocumento",
    "TipoMovimento",
    "TipoTributo",
    "TipoCredito",
    "DocumentoFiscal",
    "Item",
    "Tributo",
    "ResultadoValidacao",
    "ApuracaoTributo",
    "MapaApuracao",
    "MemoriaCalculo",
    # Módulos principais
    "XMLReader",
    "ValidadorTributario",
    "ApuradorTributario",
    "GeradorRelatorios",
]
