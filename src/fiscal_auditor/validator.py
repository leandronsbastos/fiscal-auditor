"""
Módulo para validação tributária de documentos fiscais.
"""
from decimal import Decimal
from typing import List
from .models import (
    DocumentoFiscal,
    Item,
    Tributo,
    ResultadoValidacao,
    TipoMovimento,
    TipoTributo,
    TipoCredito
)


class ValidadorTributario:
    """Validador de conformidade tributária."""

    # CFOPs que geram direito a crédito de ICMS (entradas)
    CFOPS_CREDITO_ICMS = {
        "1101", "1102", "1111", "1113", "1116", "1117", "1118", "1120", "1121", "1122",
        "1126", "1128", "1131", "1132", "1135", "1401", "1403", "1551", "1552", "1553",
        "2101", "2102", "2111", "2113", "2116", "2117", "2118", "2120", "2121", "2122",
        "2126", "2128", "2131", "2132", "2135", "2401", "2403", "2551", "2552", "2553",
        "3101", "3102", "3126", "3127", "3128", "3551", "3553"
    }

    # CFOPs que geram direito a crédito de IPI (entradas de insumos)
    CFOPS_CREDITO_IPI = {
        "1101", "1102", "1111", "1113", "1116", "1117", "1118", "1120", "1121", "1122",
        "1126", "2101", "2102", "2111", "2113", "2116", "2117", "2118", "2120", "2121",
        "2122", "2126", "3101", "3102", "3126", "3127"
    }

    # CSTs que permitem crédito de ICMS
    CST_CREDITO_ICMS = {"00", "10", "20", "51", "70", "90"}

    # CSTs que permitem crédito de IPI
    CST_CREDITO_IPI = {"00", "01", "02", "03", "04", "05", "49", "50", "51", "52", "53", "54", "55"}

    # CSTs que permitem crédito de PIS/COFINS (regime não-cumulativo)
    CST_CREDITO_PIS_COFINS = {"50", "51", "52", "53", "54", "55", "56", "60", "61", "62", "63", "64", "65", "66"}

    def __init__(self):
        """Inicializa o validador."""
        pass

    def validar_documento(self, documento: DocumentoFiscal) -> ResultadoValidacao:
        """
        Valida a conformidade tributária de um documento.
        
        Args:
            documento: Documento fiscal a ser validado
            
        Returns:
            ResultadoValidacao com o resultado da validação
        """
        resultado = ResultadoValidacao(valido=True, chave_acesso=documento.chave)

        # Valida cada item
        for item in documento.items:
            self._validar_item(item, documento, resultado)

        return resultado

    def _validar_item(self, item: Item, documento: DocumentoFiscal, resultado: ResultadoValidacao):
        """Valida um item do documento."""
        
        # Valida NCM
        if not item.ncm or len(item.ncm) not in [8, 10]:
            resultado.valido = False
            resultado.mensagens.append(f"Item {item.codigo}: NCM inválido ({item.ncm})")

        # Valida CFOP
        if not item.cfop or len(item.cfop) != 4:
            resultado.valido = False
            resultado.mensagens.append(f"Item {item.codigo}: CFOP inválido ({item.cfop})")

        # Valida consistência CFOP com tipo de movimento
        cfop_primeiro_digito = item.cfop[0] if item.cfop else ""
        if documento.tipo_movimento == TipoMovimento.ENTRADA:
            if cfop_primeiro_digito not in ["1", "2", "3"]:
                resultado.valido = False
                resultado.mensagens.append(
                    f"Item {item.codigo}: CFOP {item.cfop} inconsistente com movimento de ENTRADA"
                )
        elif documento.tipo_movimento == TipoMovimento.SAIDA:
            if cfop_primeiro_digito not in ["5", "6", "7"]:
                resultado.valido = False
                resultado.mensagens.append(
                    f"Item {item.codigo}: CFOP {item.cfop} inconsistente com movimento de SAÍDA"
                )

        # Valida tributos
        for tributo in item.tributos:
            self._validar_tributo(tributo, item, documento, resultado)

    def _validar_tributo(self, tributo: Tributo, item: Item, documento: DocumentoFiscal, resultado: ResultadoValidacao):
        """Valida um tributo específico."""
        
        # Valida CST
        if tributo.cst:
            if tributo.tipo == TipoTributo.ICMS:
                if len(tributo.cst) not in [2, 3]:  # 2 para CST, 3 para CSOSN
                    resultado.mensagens.append(
                        f"Item {item.codigo}: CST/CSOSN de ICMS inválido ({tributo.cst})"
                    )
            elif tributo.tipo in [TipoTributo.PIS, TipoTributo.COFINS]:
                if len(tributo.cst) != 2:
                    resultado.mensagens.append(
                        f"Item {item.codigo}: CST de {tributo.tipo.value} inválido ({tributo.cst})"
                    )

        # Valida base de cálculo
        if tributo.base_calculo < 0:
            resultado.valido = False
            resultado.mensagens.append(
                f"Item {item.codigo}: Base de cálculo negativa para {tributo.tipo.value}"
            )

        # Valida alíquota
        if tributo.aliquota < 0 or tributo.aliquota > 100:
            resultado.mensagens.append(
                f"Item {item.codigo}: Alíquota suspeita para {tributo.tipo.value}: {tributo.aliquota}%"
            )

        # Valida cálculo do tributo
        if tributo.base_calculo > 0 and tributo.aliquota > 0:
            valor_calculado = (tributo.base_calculo * tributo.aliquota / 100).quantize(Decimal('0.01'))
            diferenca = abs(tributo.valor - valor_calculado)
            if diferenca > Decimal('0.02'):  # Tolerância de 2 centavos
                resultado.mensagens.append(
                    f"Item {item.codigo}: Valor de {tributo.tipo.value} inconsistente. "
                    f"Calculado: {valor_calculado}, Informado: {tributo.valor}"
                )

        # Classifica créditos (apenas para entradas)
        if documento.tipo_movimento == TipoMovimento.ENTRADA:
            self._classificar_credito(tributo, item, resultado)

    def _classificar_credito(self, tributo: Tributo, item: Item, resultado: ResultadoValidacao):
        """Classifica um crédito como aproveitável, indevido ou glosável."""
        
        aproveitavel = False
        
        if tributo.tipo == TipoTributo.ICMS:
            # Verifica se CFOP e CST permitem crédito
            if item.cfop in self.CFOPS_CREDITO_ICMS:
                # Pega apenas os 2 primeiros dígitos do CST (ignora origem)
                cst_2_digitos = tributo.cst[-2:] if tributo.cst and len(tributo.cst) >= 2 else ""
                if cst_2_digitos in self.CST_CREDITO_ICMS:
                    aproveitavel = True
                else:
                    # CST não permite crédito
                    resultado.creditos_glosaveis.append(tributo)
                    return
            else:
                # CFOP não permite crédito
                resultado.creditos_indevidos.append(tributo)
                return
                
        elif tributo.tipo == TipoTributo.IPI:
            # IPI: crédito apenas em entradas de insumos para industrialização
            if item.cfop in self.CFOPS_CREDITO_IPI:
                cst_2_digitos = tributo.cst[-2:] if tributo.cst and len(tributo.cst) >= 2 else tributo.cst or ""
                if cst_2_digitos in self.CST_CREDITO_IPI:
                    aproveitavel = True
                else:
                    resultado.creditos_glosaveis.append(tributo)
                    return
            else:
                resultado.creditos_indevidos.append(tributo)
                return
                
        elif tributo.tipo in [TipoTributo.PIS, TipoTributo.COFINS]:
            # PIS/COFINS: depende do regime (não-cumulativo)
            if tributo.cst in self.CST_CREDITO_PIS_COFINS:
                # Verifica se CFOP é de entrada de mercadorias/insumos
                if item.cfop.startswith(("110", "111", "120", "121", "210", "211", "220", "221")):
                    aproveitavel = True
                else:
                    resultado.creditos_glosaveis.append(tributo)
                    return
            else:
                resultado.creditos_indevidos.append(tributo)
                return
        
        if aproveitavel:
            resultado.creditos_aproveitaveis.append(tributo)

    def validar_cfop_ncm(self, cfop: str, ncm: str) -> bool:
        """
        Valida a compatibilidade entre CFOP e NCM.
        
        Args:
            cfop: Código CFOP
            ncm: Código NCM
            
        Returns:
            True se compatível
        """
        # Validações básicas
        if not cfop or len(cfop) != 4:
            return False
        
        if not ncm or len(ncm) not in [8, 10]:
            return False

        # Aqui poderia ter regras específicas de compatibilidade
        # Por exemplo: certos NCMs só podem usar certos CFOPs
        # Para esta implementação inicial, apenas valida o formato
        
        return True

    def validar_cst(self, cst: str, tipo_tributo: TipoTributo) -> bool:
        """
        Valida se o CST é válido para o tipo de tributo.
        
        Args:
            cst: Código de Situação Tributária
            tipo_tributo: Tipo do tributo
            
        Returns:
            True se válido
        """
        if not cst:
            return False

        if tipo_tributo == TipoTributo.ICMS:
            # ICMS pode ter CST (2 dígitos) ou CSOSN (3 dígitos)
            return len(cst) in [2, 3]
        elif tipo_tributo in [TipoTributo.IPI, TipoTributo.PIS, TipoTributo.COFINS]:
            return len(cst) == 2
        
        return True
