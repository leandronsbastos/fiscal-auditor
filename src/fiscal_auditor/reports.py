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


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


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
            json.dump(relatorio, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)

    def exportar_json_str(self, relatorio: Dict[str, Any]) -> str:
        """
        Exporta relatório para string JSON.
        
        Args:
            relatorio: Dicionário com o relatório
            
        Returns:
            String JSON
        """
        return json.dumps(relatorio, ensure_ascii=False, indent=2, cls=DecimalEncoder)

    def gerar_relatorio_por_produto(self, documentos: List[DocumentoFiscal]) -> Dict[str, Any]:
        """
        Gera relatório agrupado por produto (NCM).
        
        Args:
            documentos: Lista de documentos fiscais
            
        Returns:
            Dicionário com o relatório por produto
        """
        produtos = {}
        
        for doc in documentos:
            for item in doc.items:
                # Chave: NCM + Descrição
                chave = f"{item.ncm}|{item.descricao}"
                
                if chave not in produtos:
                    produtos[chave] = {
                        "ncm": item.ncm,
                        "descricao": item.descricao,
                        "entradas": {
                            "quantidade": Decimal('0'),
                            "valor_total": Decimal('0'),
                            "documentos": 0,
                            "tributos": {}
                        },
                        "saidas": {
                            "quantidade": Decimal('0'),
                            "valor_total": Decimal('0'),
                            "documentos": 0,
                            "tributos": {}
                        }
                    }
                
                # Define se é entrada ou saída
                movimento = "entradas" if doc.tipo_movimento == TipoMovimento.ENTRADA else "saidas"
                
                # Acumula quantidades e valores
                produtos[chave][movimento]["quantidade"] += item.quantidade
                produtos[chave][movimento]["valor_total"] += item.valor_total
                produtos[chave][movimento]["documentos"] += 1
                
                # Acumula tributos por tipo
                for tributo in item.tributos:
                    tipo_trib = tributo.tipo.value
                    if tipo_trib not in produtos[chave][movimento]["tributos"]:
                        produtos[chave][movimento]["tributos"][tipo_trib] = Decimal('0')
                    produtos[chave][movimento]["tributos"][tipo_trib] += tributo.valor
        
        # Converte para lista e formata valores
        produtos_lista = []
        for chave, dados in produtos.items():
            produto_info = {
                "ncm": dados["ncm"],
                "descricao": dados["descricao"],
                "entradas": {
                    "quantidade": str(dados["entradas"]["quantidade"]),
                    "valor_total": str(dados["entradas"]["valor_total"]),
                    "documentos": dados["entradas"]["documentos"],
                    "tributos": {k: str(v) for k, v in dados["entradas"]["tributos"].items()}
                },
                "saidas": {
                    "quantidade": str(dados["saidas"]["quantidade"]),
                    "valor_total": str(dados["saidas"]["valor_total"]),
                    "documentos": dados["saidas"]["documentos"],
                    "tributos": {k: str(v) for k, v in dados["saidas"]["tributos"].items()}
                },
                "saldo": {
                    "quantidade": str(dados["entradas"]["quantidade"] - dados["saidas"]["quantidade"]),
                    "valor": str(dados["entradas"]["valor_total"] - dados["saidas"]["valor_total"])
                }
            }
            produtos_lista.append(produto_info)
        
        # Ordena por NCM
        produtos_lista.sort(key=lambda x: x["ncm"])
        
        return {
            "tipo": "Relatório por Produto",
            "data_geracao": datetime.now().isoformat(),
            "total_produtos": len(produtos_lista),
            "produtos": produtos_lista
        }

    def gerar_analise_tributaria_produtos(self, documentos: List[DocumentoFiscal]) -> Dict[str, Any]:
        """
        Gera análise tributária detalhada por produto.
        
        Args:
            documentos: Lista de documentos fiscais
            
        Returns:
            Dicionário com análise tributária detalhada
        """
        produtos = {}
        
        for doc in documentos:
            for item in doc.items:
                chave = f"{item.ncm}|{item.descricao}"
                
                if chave not in produtos:
                    produtos[chave] = {
                        "ncm": item.ncm,
                        "descricao": item.descricao,
                        "cfop_entradas": set(),
                        "cfop_saidas": set(),
                        "entradas": {
                            "quantidade": Decimal('0'),
                            "valor_total": Decimal('0'),
                            "documentos": 0,
                            "tributos": {
                                "ICMS": {"base": Decimal('0'), "valor": Decimal('0'), "aliquota_media": Decimal('0'), "count": 0},
                                "IPI": {"base": Decimal('0'), "valor": Decimal('0'), "aliquota_media": Decimal('0'), "count": 0},
                                "PIS": {"base": Decimal('0'), "valor": Decimal('0'), "aliquota_media": Decimal('0'), "count": 0},
                                "COFINS": {"base": Decimal('0'), "valor": Decimal('0'), "aliquota_media": Decimal('0'), "count": 0},
                                "IBS": {"base": Decimal('0'), "valor": Decimal('0'), "aliquota_media": Decimal('0'), "count": 0},
                                "CBS": {"base": Decimal('0'), "valor": Decimal('0'), "aliquota_media": Decimal('0'), "count": 0}
                            }
                        },
                        "saidas": {
                            "quantidade": Decimal('0'),
                            "valor_total": Decimal('0'),
                            "documentos": 0,
                            "tributos": {
                                "ICMS": {"base": Decimal('0'), "valor": Decimal('0'), "aliquota_media": Decimal('0'), "count": 0},
                                "IPI": {"base": Decimal('0'), "valor": Decimal('0'), "aliquota_media": Decimal('0'), "count": 0},
                                "PIS": {"base": Decimal('0'), "valor": Decimal('0'), "aliquota_media": Decimal('0'), "count": 0},
                                "COFINS": {"base": Decimal('0'), "valor": Decimal('0'), "aliquota_media": Decimal('0'), "count": 0},
                                "IBS": {"base": Decimal('0'), "valor": Decimal('0'), "aliquota_media": Decimal('0'), "count": 0},
                                "CBS": {"base": Decimal('0'), "valor": Decimal('0'), "aliquota_media": Decimal('0'), "count": 0}
                            }
                        }
                    }
                
                movimento = "entradas" if doc.tipo_movimento == TipoMovimento.ENTRADA else "saidas"
                
                # Registra CFOPs
                if movimento == "entradas":
                    produtos[chave]["cfop_entradas"].add(item.cfop)
                else:
                    produtos[chave]["cfop_saidas"].add(item.cfop)
                
                # Acumula quantidades e valores
                produtos[chave][movimento]["quantidade"] += item.quantidade
                produtos[chave][movimento]["valor_total"] += item.valor_total
                produtos[chave][movimento]["documentos"] += 1
                
                # Acumula tributos detalhadamente
                for tributo in item.tributos:
                    tipo_trib = tributo.tipo.value
                    if tipo_trib in produtos[chave][movimento]["tributos"]:
                        produtos[chave][movimento]["tributos"][tipo_trib]["base"] += tributo.base_calculo
                        produtos[chave][movimento]["tributos"][tipo_trib]["valor"] += tributo.valor
                        produtos[chave][movimento]["tributos"][tipo_trib]["aliquota_media"] += tributo.aliquota
                        produtos[chave][movimento]["tributos"][tipo_trib]["count"] += 1
        
        # Converte para lista e calcula alíquotas médias
        produtos_lista = []
        for chave, dados in produtos.items():
            # Calcula alíquotas médias
            for movimento in ["entradas", "saidas"]:
                for tipo_trib, info in dados[movimento]["tributos"].items():
                    if info["count"] > 0:
                        info["aliquota_media"] = info["aliquota_media"] / info["count"]
                    else:
                        info["aliquota_media"] = Decimal('0')
            
            # Calcula diferenças tributárias (crédito - débito)
            diferencas = {}
            for tipo_trib in ["ICMS", "IPI", "PIS", "COFINS", "IBS", "CBS"]:
                credito = dados["entradas"]["tributos"][tipo_trib]["valor"]
                debito = dados["saidas"]["tributos"][tipo_trib]["valor"]
                diferencas[tipo_trib] = {
                    "credito": str(credito),
                    "debito": str(debito),
                    "diferenca": str(credito - debito),
                    "percentual_entrada": str(dados["entradas"]["tributos"][tipo_trib]["aliquota_media"]),
                    "percentual_saida": str(dados["saidas"]["tributos"][tipo_trib]["aliquota_media"])
                }
            
            produto_info = {
                "ncm": dados["ncm"],
                "descricao": dados["descricao"],
                "cfop_entradas": sorted(list(dados["cfop_entradas"])),
                "cfop_saidas": sorted(list(dados["cfop_saidas"])),
                "entradas": {
                    "quantidade": str(dados["entradas"]["quantidade"]),
                    "valor_total": str(dados["entradas"]["valor_total"]),
                    "documentos": dados["entradas"]["documentos"],
                    "tributos": {
                        k: {
                            "base": str(v["base"]),
                            "valor": str(v["valor"]),
                            "aliquota_media": str(v["aliquota_media"])
                        } for k, v in dados["entradas"]["tributos"].items()
                    }
                },
                "saidas": {
                    "quantidade": str(dados["saidas"]["quantidade"]),
                    "valor_total": str(dados["saidas"]["valor_total"]),
                    "documentos": dados["saidas"]["documentos"],
                    "tributos": {
                        k: {
                            "base": str(v["base"]),
                            "valor": str(v["valor"]),
                            "aliquota_media": str(v["aliquota_media"])
                        } for k, v in dados["saidas"]["tributos"].items()
                    }
                },
                "analise_tributaria": diferencas
            }
            produtos_lista.append(produto_info)
        
        produtos_lista.sort(key=lambda x: x["ncm"])
        
        return {
            "tipo": "Análise Tributária por Produto",
            "data_geracao": datetime.now().isoformat(),
            "total_produtos": len(produtos_lista),
            "produtos": produtos_lista
        }
