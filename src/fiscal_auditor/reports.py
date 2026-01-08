"""
Módulo para geração de relatórios fiscais.
"""
import json
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
from .models import (
    DocumentoFiscal,
    MapaApuracao,
    TipoMovimento,
    TipoTributo,
    ResultadoValidacao
)


class GeradorRelatorios:
    """Gerador de relatórios estruturados."""

    def __init__(self):
        """Inicializa o gerador de relatórios."""
        pass

    def gerar_demonstrativo_entradas(self, documentos: List[DocumentoFiscal]) -> Dict[str, Any]:
        """
        Gera demonstrativo de entradas.
        
        Args:
            documentos: Lista de documentos fiscais de entrada
            
        Returns:
            Dicionário com o relatório estruturado
        """
        entradas = [doc for doc in documentos if doc.tipo_movimento == TipoMovimento.ENTRADA]
        
        relatorio = {
            "tipo": "Demonstrativo de Entradas",
            "data_geracao": datetime.now().isoformat(),
            "quantidade_documentos": len(entradas),
            "valor_total": str(sum(doc.valor_total for doc in entradas)),
            "documentos": []
        }

        # Agrupa tributos por tipo
        tributos_totais = {}
        
        for doc in entradas:
            doc_info = {
                "tipo_documento": doc.tipo.value,
                "chave": doc.chave,
                "numero": doc.numero,
                "serie": doc.serie,
                "data_emissao": doc.data_emissao.isoformat(),
                "cnpj_emitente": doc.cnpj_emitente,
                "valor_total": str(doc.valor_total),
                "tributos": {}
            }

            # Agrupa tributos do documento
            for item in doc.items:
                for tributo in item.tributos:
                    tipo_str = tributo.tipo.value
                    if tipo_str not in doc_info["tributos"]:
                        doc_info["tributos"][tipo_str] = Decimal('0')
                    doc_info["tributos"][tipo_str] += tributo.valor

                    # Acumula no total geral
                    if tipo_str not in tributos_totais:
                        tributos_totais[tipo_str] = Decimal('0')
                    tributos_totais[tipo_str] += tributo.valor

            # Converte Decimals para strings
            doc_info["tributos"] = {k: str(v) for k, v in doc_info["tributos"].items()}
            relatorio["documentos"].append(doc_info)

        # Adiciona totais de tributos
        relatorio["tributos_totais"] = {k: str(v) for k, v in tributos_totais.items()}

        return relatorio

    def gerar_demonstrativo_saidas(self, documentos: List[DocumentoFiscal]) -> Dict[str, Any]:
        """
        Gera demonstrativo de saídas.
        
        Args:
            documentos: Lista de documentos fiscais de saída
            
        Returns:
            Dicionário com o relatório estruturado
        """
        saidas = [doc for doc in documentos if doc.tipo_movimento == TipoMovimento.SAIDA]
        
        relatorio = {
            "tipo": "Demonstrativo de Saídas",
            "data_geracao": datetime.now().isoformat(),
            "quantidade_documentos": len(saidas),
            "valor_total": str(sum(doc.valor_total for doc in saidas)),
            "documentos": []
        }

        # Agrupa tributos por tipo
        tributos_totais = {}
        
        for doc in saidas:
            doc_info = {
                "tipo_documento": doc.tipo.value,
                "chave": doc.chave,
                "numero": doc.numero,
                "serie": doc.serie,
                "data_emissao": doc.data_emissao.isoformat(),
                "cnpj_destinatario": doc.cnpj_destinatario,
                "valor_total": str(doc.valor_total),
                "tributos": {}
            }

            # Agrupa tributos do documento
            for item in doc.items:
                for tributo in item.tributos:
                    tipo_str = tributo.tipo.value
                    if tipo_str not in doc_info["tributos"]:
                        doc_info["tributos"][tipo_str] = Decimal('0')
                    doc_info["tributos"][tipo_str] += tributo.valor

                    # Acumula no total geral
                    if tipo_str not in tributos_totais:
                        tributos_totais[tipo_str] = Decimal('0')
                    tributos_totais[tipo_str] += tributo.valor

            # Converte Decimals para strings
            doc_info["tributos"] = {k: str(v) for k, v in doc_info["tributos"].items()}
            relatorio["documentos"].append(doc_info)

        # Adiciona totais de tributos
        relatorio["tributos_totais"] = {k: str(v) for k, v in tributos_totais.items()}

        return relatorio

    def gerar_mapa_apuracao(self, mapa: MapaApuracao) -> Dict[str, Any]:
        """
        Gera relatório do mapa de apuração.
        
        Args:
            mapa: Mapa de apuração
            
        Returns:
            Dicionário com o relatório estruturado
        """
        return mapa.to_dict()

    def gerar_relatorio_validacao(self, validacoes: List[ResultadoValidacao]) -> Dict[str, Any]:
        """
        Gera relatório consolidado de validações.
        
        Args:
            validacoes: Lista de resultados de validação
            
        Returns:
            Dicionário com o relatório estruturado
        """
        relatorio = {
            "tipo": "Relatório de Validação",
            "data_geracao": datetime.now().isoformat(),
            "total_validacoes": len(validacoes),
            "validos": sum(1 for v in validacoes if v.valido),
            "invalidos": sum(1 for v in validacoes if not v.valido),
            "detalhes": []
        }

        # Contadores de créditos
        total_aproveitaveis = 0
        total_indevidos = 0
        total_glosaveis = 0
        valor_aproveitaveis = Decimal('0')
        valor_indevidos = Decimal('0')
        valor_glosaveis = Decimal('0')

        for validacao in validacoes:
            total_aproveitaveis += len(validacao.creditos_aproveitaveis)
            total_indevidos += len(validacao.creditos_indevidos)
            total_glosaveis += len(validacao.creditos_glosaveis)

            for credito in validacao.creditos_aproveitaveis:
                valor_aproveitaveis += credito.valor
            for credito in validacao.creditos_indevidos:
                valor_indevidos += credito.valor
            for credito in validacao.creditos_glosaveis:
                valor_glosaveis += credito.valor

            relatorio["detalhes"].append(validacao.to_dict())

        relatorio["resumo_creditos"] = {
            "aproveitaveis": {
                "quantidade": total_aproveitaveis,
                "valor_total": str(valor_aproveitaveis)
            },
            "indevidos": {
                "quantidade": total_indevidos,
                "valor_total": str(valor_indevidos)
            },
            "glosaveis": {
                "quantidade": total_glosaveis,
                "valor_total": str(valor_glosaveis)
            }
        }

        return relatorio

    def gerar_relatorio_completo(
        self,
        documentos: List[DocumentoFiscal],
        mapa: MapaApuracao,
        validacoes: List[ResultadoValidacao]
    ) -> Dict[str, Any]:
        """
        Gera relatório completo com todas as informações.
        
        Args:
            documentos: Lista de documentos fiscais
            mapa: Mapa de apuração
            validacoes: Lista de validações
            
        Returns:
            Dicionário com o relatório completo
        """
        return {
            "tipo": "Relatório Completo de Auditoria Fiscal",
            "data_geracao": datetime.now().isoformat(),
            "periodo": mapa.periodo,
            "demonstrativo_entradas": self.gerar_demonstrativo_entradas(documentos),
            "demonstrativo_saidas": self.gerar_demonstrativo_saidas(documentos),
            "mapa_apuracao": self.gerar_mapa_apuracao(mapa),
            "validacao": self.gerar_relatorio_validacao(validacoes)
        }

    def exportar_json(self, relatorio: Dict[str, Any], caminho_arquivo: str):
        """
        Exporta relatório para arquivo JSON.
        
        Args:
            relatorio: Dicionário com o relatório
            caminho_arquivo: Caminho do arquivo de saída
        """
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)

    def exportar_json_str(self, relatorio: Dict[str, Any]) -> str:
        """
        Exporta relatório para string JSON.
        
        Args:
            relatorio: Dicionário com o relatório
            
        Returns:
            String JSON
        """
        return json.dumps(relatorio, ensure_ascii=False, indent=2)
