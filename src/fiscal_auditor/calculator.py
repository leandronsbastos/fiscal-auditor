"""
Módulo para apuração e cálculo de tributos.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Dict
from .models import (
    DocumentoFiscal,
    ApuracaoTributo,
    MapaApuracao,
    TipoMovimento,
    TipoTributo,
    MemoriaCalculo
)


class ApuradorTributario:
    """Apurador de tributos."""

    def __init__(self):
        """Inicializa o apurador."""
        self.documentos: List[DocumentoFiscal] = []

    def adicionar_documento(self, documento: DocumentoFiscal):
        """
        Adiciona um documento para apuração.
        
        Args:
            documento: Documento fiscal a ser incluído na apuração
        """
        self.documentos.append(documento)

    def adicionar_documentos(self, documentos: List[DocumentoFiscal]):
        """
        Adiciona múltiplos documentos para apuração.
        
        Args:
            documentos: Lista de documentos fiscais
        """
        self.documentos.extend(documentos)

    def apurar(self, periodo: str) -> MapaApuracao:
        """
        Realiza a apuração de todos os tributos.
        
        Args:
            periodo: Período da apuração (ex: "01/2024")
            
        Returns:
            MapaApuracao com os resultados
        """
        mapa = MapaApuracao(periodo=periodo)

        # Apura cada tipo de tributo
        for tipo_tributo in [TipoTributo.ICMS, TipoTributo.IPI, TipoTributo.PIS, 
                             TipoTributo.COFINS, TipoTributo.IBS, TipoTributo.CBS]:
            apuracao = self._apurar_tributo(tipo_tributo)
            if apuracao:
                mapa.apuracoes.append(apuracao)

        return mapa

    def _apurar_tributo(self, tipo_tributo: TipoTributo) -> ApuracaoTributo:
        """
        Apura um tributo específico.
        
        Fórmula: Saldo = Débitos de Saída - Créditos de Entrada
        
        Args:
            tipo_tributo: Tipo do tributo a ser apurado
            
        Returns:
            ApuracaoTributo com o resultado
        """
        debitos = Decimal('0')
        creditos = Decimal('0')
        
        documentos_debito = []
        documentos_credito = []

        # Separa documentos de entrada e saída
        for doc in self.documentos:
            for item in doc.items:
                for tributo in item.tributos:
                    if tributo.tipo == tipo_tributo:
                        if doc.tipo_movimento == TipoMovimento.SAIDA:
                            debitos += tributo.valor
                            documentos_debito.append({
                                'documento': doc.numero,
                                'item': item.codigo,
                                'valor': tributo.valor
                            })
                        elif doc.tipo_movimento == TipoMovimento.ENTRADA:
                            creditos += tributo.valor
                            documentos_credito.append({
                                'documento': doc.numero,
                                'item': item.codigo,
                                'valor': tributo.valor
                            })

        # Calcula saldo
        saldo = debitos - creditos

        # Cria memória de cálculo
        memoria = MemoriaCalculo(
            descricao=f"Apuração de {tipo_tributo.value}",
            valores={
                'debitos_saida': debitos,
                'creditos_entrada': creditos,
                'num_documentos_debito': len(documentos_debito),
                'num_documentos_credito': len(documentos_credito),
                'documentos_debito': documentos_debito[:10],  # Limita a 10 para não ficar muito grande
                'documentos_credito': documentos_credito[:10]
            },
            formula="Saldo = Débitos de Saída - Créditos de Entrada",
            resultado=saldo
        )

        return ApuracaoTributo(
            tipo=tipo_tributo,
            debitos=debitos,
            creditos=creditos,
            saldo=saldo,
            memoria_calculo=memoria
        )

    def calcular_total_debitos(self, tipo_tributo: TipoTributo) -> Decimal:
        """
        Calcula o total de débitos de um tributo.
        
        Args:
            tipo_tributo: Tipo do tributo
            
        Returns:
            Total de débitos
        """
        total = Decimal('0')
        for doc in self.documentos:
            if doc.tipo_movimento == TipoMovimento.SAIDA:
                for item in doc.items:
                    for tributo in item.tributos:
                        if tributo.tipo == tipo_tributo:
                            total += tributo.valor
        return total

    def calcular_total_creditos(self, tipo_tributo: TipoTributo) -> Decimal:
        """
        Calcula o total de créditos de um tributo.
        
        Args:
            tipo_tributo: Tipo do tributo
            
        Returns:
            Total de créditos
        """
        total = Decimal('0')
        for doc in self.documentos:
            if doc.tipo_movimento == TipoMovimento.ENTRADA:
                for item in doc.items:
                    for tributo in item.tributos:
                        if tributo.tipo == tipo_tributo:
                            total += tributo.valor
        return total

    def obter_documentos_por_tipo(self, tipo_movimento: TipoMovimento) -> List[DocumentoFiscal]:
        """
        Retorna documentos filtrados por tipo de movimento.
        
        Args:
            tipo_movimento: Tipo de movimento (ENTRADA ou SAIDA)
            
        Returns:
            Lista de documentos
        """
        return [doc for doc in self.documentos if doc.tipo_movimento == tipo_movimento]

    def calcular_saldo_periodo(self, tipo_tributo: TipoTributo) -> Dict[str, Decimal]:
        """
        Calcula o saldo de um tributo no período.
        
        Args:
            tipo_tributo: Tipo do tributo
            
        Returns:
            Dicionário com débitos, créditos e saldo
        """
        debitos = self.calcular_total_debitos(tipo_tributo)
        creditos = self.calcular_total_creditos(tipo_tributo)
        saldo = debitos - creditos

        return {
            'debitos': debitos,
            'creditos': creditos,
            'saldo': saldo
        }

    def limpar_documentos(self):
        """Remove todos os documentos da apuração."""
        self.documentos.clear()
