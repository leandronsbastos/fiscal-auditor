#!/usr/bin/env python
"""
Aplicação Web do Fiscal Auditor.
Interface web para consulta de documentos fiscais do datalake e visualização de relatórios tributários.
"""
from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import os
from datetime import datetime
import json
from decimal import Decimal
from contextlib import asynccontextmanager

from fiscal_auditor import (
    XMLReader,
    ValidadorTributario,
    ApuradorTributario,
    GeradorRelatorios
)
from fiscal_auditor.database import get_db, init_db
from fiscal_auditor import crud, schemas, db_models
from fiscal_auditor.auth import criar_token_acesso, obter_usuario_atual, verificar_acesso_empresa
from fiscal_auditor.exportador import ExportadorRelatorios
from fastapi.responses import FileResponse
from datalake_integration import (
    buscar_documentos_periodo,
    verificar_documentos_disponiveis,
    obter_estatisticas_datalake
)


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

# Modelos Pydantic para requisições
class VerificarDatalakeRequest(BaseModel):
    empresa_id: int
    data_inicio: str
    data_fim: str

class ProcessarDatalakeRequest(BaseModel):
    empresa_id: int
    data_inicio: str
    data_fim: str
    tipo_data: str

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa o banco de dados na inicialização."""
    init_db()
    yield

app = FastAPI(
    title="Fiscal Auditor", 
    description="Sistema de Auditoria e Apuração Tributária",
    lifespan=lifespan
)

# Configurar templates e arquivos estáticos
templates = Jinja2Templates(directory="templates")

# Criar diretório para arquivos estáticos se não existir
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Armazenamento temporário dos dados processados
dados_sessao = {
    "documentos": [],
    "validacoes": [],
    "mapa": None,
    "relatorios": {}
}


@app.get("/login", response_class=HTMLResponse, tags=["Autenticação"])
async def pagina_login(request: Request):
    """Página de login."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/painel", response_class=HTMLResponse, tags=["Autenticação"])
async def painel(request: Request):
    """Painel de seleção de empresas."""
    return templates.TemplateResponse("painel.html", {"request": request})


@app.post("/api/login", tags=["Autenticação"])
async def login(credentials: dict, db: Session = Depends(get_db)):
    """Endpoint de login. Retorna token JWT. Aceita JSON com email e senha."""
    email = credentials.get("email")
    senha = credentials.get("senha")
    
    if not email or not senha:
        raise HTTPException(status_code=400, detail="Email e senha são obrigatórios")
    
    # Buscar usuário por email
    usuario = crud.obter_usuario_por_email(db, email)
    
    if not usuario:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    # Verificar senha
    if not crud.verify_password(senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    # Verificar se usuário está ativo
    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo")
    
    # Verificar se tem empresas vinculadas
    if len(usuario.empresas) == 0:
        raise HTTPException(
            status_code=403,
            detail="Usuário não está vinculado a nenhuma empresa. Entre em contato com o administrador."
        )
    
    # Criar token
    token = criar_token_acesso(data={"sub": str(usuario.id)})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "total_empresas": len(usuario.empresas)
        }
    }


@app.get("/api/me", tags=["Autenticação"])
async def usuario_logado(
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual)
):
    """Retorna informações do usuário logado."""
    return usuario_atual


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, empresa_id: int = None):
    """Página inicial - painel ou consulta dependendo do empresa_id."""
    if empresa_id:
        # Se tem empresa_id, mostrar página de consulta
        return templates.TemplateResponse("index.html", {
            "request": request,
            "empresa_id": empresa_id
        })
    else:
        # Se não tem empresa_id, mostrar painel de seleção
        return templates.TemplateResponse("painel.html", {"request": request})


@app.post("/api/verificar-datalake")
async def verificar_datalake(
    dados: VerificarDatalakeRequest,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Verifica quantos documentos existem no datalake para o período."""    
    try:
        # Verificar acesso à empresa
        if not verificar_acesso_empresa(usuario_atual, dados.empresa_id, db):
            raise HTTPException(status_code=403, detail="Você não tem acesso a esta empresa")
        
        # Buscar empresa
        empresa = crud.obter_empresa(db, dados.empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        # Converter datas
        from datetime import datetime
        data_inicio_dt = datetime.strptime(dados.data_inicio, "%Y-%m-%d").date()
        data_fim_dt = datetime.strptime(dados.data_fim, "%Y-%m-%d").date()
        
        # Verificar disponibilidade no datalake
        resultado = verificar_documentos_disponiveis(
            cnpj=empresa.cnpj,
            data_inicio=data_inicio_dt,
            data_fim=data_fim_dt
        )
        
        return JSONResponse({
            "success": True,
            "disponivel": resultado['total'] > 0,
            "total": resultado['total'],
            "entradas": resultado['entradas'],
            "saidas": resultado['saidas']
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Erro ao verificar datalake: {str(e)}"
        }, status_code=500)


@app.post("/processar-datalake")
async def processar_datalake(
    dados: ProcessarDatalakeRequest,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Processa documentos do datalake (banco de dados do ETL)."""    
    try:
        # Verificar acesso à empresa
        if not verificar_acesso_empresa(usuario_atual, dados.empresa_id, db):
            raise HTTPException(status_code=403, detail="Você não tem acesso a esta empresa")
        
        # Buscar empresa
        empresa = crud.obter_empresa(db, dados.empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        # Converter datas
        from datetime import datetime
        data_inicio_dt = datetime.strptime(dados.data_inicio, "%Y-%m-%d").date()
        data_fim_dt = datetime.strptime(dados.data_fim, "%Y-%m-%d").date()
        
        # Limpar dados anteriores
        dados_sessao["documentos"] = []
        dados_sessao["validacoes"] = []
        dados_sessao["mapa"] = None
        dados_sessao["relatorios"] = {}
        dados_sessao["empresa_id"] = dados.empresa_id
        dados_sessao["filtro_data_tipo"] = dados.tipo_data
        dados_sessao["filtro_data_inicio"] = dados.data_inicio
        dados_sessao["filtro_data_fim"] = dados.data_fim
        dados_sessao["fonte_dados"] = "datalake"
        
        # Buscar documentos do datalake
        documentos = buscar_documentos_periodo(
            cnpj=empresa.cnpj,
            data_inicio=data_inicio_dt,
            data_fim=data_fim_dt,
            tipo_data=dados.tipo_data,
            incluir_itens=True
        )
        
        if not documentos:
            return JSONResponse({
                "success": False,
                "message": "Nenhum documento encontrado no datalake para o período selecionado"
            }, status_code=400)
        
        # Inicializar componentes
        validador = ValidadorTributario()
        apurador = ApuradorTributario()
        gerador = GeradorRelatorios()
        
        validacoes = []
        
        # Processar documentos
        for doc in documentos:
            # Validar
            validacao = validador.validar_documento(doc)
            validacoes.append(validacao)
            
            # Adicionar para apuração
            apurador.adicionar_documento(doc)
        
        # Calcular período
        datas = [doc.data_emissao for doc in documentos if doc.data_emissao]
        if datas:
            data_mais_antiga = min(datas)
            periodo = f"{data_mais_antiga.month:02d}/{data_mais_antiga.year}"
        else:
            data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d")
            periodo = f"{data_inicio_obj.month:02d}/{data_inicio_obj.year}"
        
        # Realizar apuração
        mapa = apurador.apurar(periodo)
        
        # Gerar relatórios
        relatorios = {
            "entradas": gerador.gerar_demonstrativo_entradas(documentos),
            "saidas": gerador.gerar_demonstrativo_saidas(documentos),
            "mapa": gerador.gerar_mapa_apuracao(mapa),
            "validacao": gerador.gerar_relatorio_validacao(validacoes),
            "completo": gerador.gerar_relatorio_completo(documentos, mapa, validacoes)
        }
        
        # Armazenar na sessão
        dados_sessao["documentos"] = documentos
        dados_sessao["validacoes"] = validacoes
        dados_sessao["mapa"] = mapa
        dados_sessao["relatorios"] = relatorios
        dados_sessao["empresa"] = {
            "id": empresa.id,
            "cnpj": empresa.cnpj,
            "razao_social": empresa.razao_social
        }
        
        return JSONResponse({
            "success": True,
            "message": f"{len(documentos)} documento(s) processado(s) do datalake",
            "total_documentos": len(documentos),
            "periodo": periodo,
            "fonte": "datalake"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "message": f"Erro ao processar datalake: {str(e)}"
        }, status_code=500)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Exibe o dashboard com os resultados."""
    if not dados_sessao["mapa"]:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Nenhum dado foi processado. Faça o upload de XMLs primeiro."
        })
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "mapa": dados_sessao["mapa"],
        "relatorios": dados_sessao["relatorios"],
        "documentos": dados_sessao["documentos"],
        "validacoes": dados_sessao["validacoes"]
    })


@app.get("/produtos", response_class=HTMLResponse)
async def visao_produtos(request: Request):
    """Exibe a visão por produtos."""
    if not dados_sessao["documentos"]:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Nenhum dado foi processado. Faça o upload de XMLs primeiro."
        })
    
    gerador = GeradorRelatorios()
    relatorio_produtos = gerador.gerar_relatorio_por_produto(dados_sessao["documentos"])
    
    # Calcula totais
    total_entradas_valor = sum(float(p['entradas']['valor_total']) for p in relatorio_produtos['produtos'])
    total_entradas_qtd = sum(float(p['entradas']['quantidade']) for p in relatorio_produtos['produtos'])
    total_entradas_docs = sum(p['entradas']['documentos'] for p in relatorio_produtos['produtos'])
    
    total_saidas_valor = sum(float(p['saidas']['valor_total']) for p in relatorio_produtos['produtos'])
    total_saidas_qtd = sum(float(p['saidas']['quantidade']) for p in relatorio_produtos['produtos'])
    total_saidas_docs = sum(p['saidas']['documentos'] for p in relatorio_produtos['produtos'])
    
    return templates.TemplateResponse("produtos.html", {
        "request": request,
        "relatorio": relatorio_produtos,
        "total_entradas_valor": total_entradas_valor,
        "total_entradas_qtd": total_entradas_qtd,
        "total_entradas_docs": total_entradas_docs,
        "total_saidas_valor": total_saidas_valor,
        "total_saidas_qtd": total_saidas_qtd,
        "total_saidas_docs": total_saidas_docs
    })


@app.get("/analise-tributaria", response_class=HTMLResponse)
async def analise_tributaria(request: Request):
    """Exibe análise tributária detalhada por produto."""
    if not dados_sessao["documentos"]:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Nenhum dado foi processado. Faça o upload de XMLs primeiro."
        })
    
    gerador = GeradorRelatorios()
    analise = gerador.gerar_analise_tributaria_produtos(dados_sessao["documentos"])
    
    return templates.TemplateResponse("analise_tributaria.html", {
        "request": request,
        "analise": analise
    })


@app.get("/api/relatorios/{tipo}")
async def obter_relatorio(tipo: str):
    """Retorna um relatório específico em JSON."""
    if tipo not in dados_sessao["relatorios"]:
        return JSONResponse({
            "success": False,
            "message": "Relatório não encontrado"
        }, status_code=404)
    
    # Usa o encoder customizado para Decimal
    return JSONResponse(
        content=json.loads(json.dumps(dados_sessao["relatorios"][tipo], cls=DecimalEncoder))
    )


@app.get("/api/documentos")
async def listar_documentos():
    """Lista todos os documentos processados."""
    docs = []
    for doc in dados_sessao["documentos"]:
        docs.append({
            "chave": doc.chave,
            "numero": doc.numero,
            "tipo": doc.tipo.value,
            "movimento": doc.tipo_movimento.value,
            "emitente": doc.emitente_nome,
            "destinatario": doc.destinatario_nome,
            "valor_total": float(doc.valor_total),
            "data_emissao": doc.data_emissao.isoformat() if doc.data_emissao else None,
            "items_count": len(doc.items)
        })
    return JSONResponse(docs)


@app.get("/api/apuracao")
async def obter_apuracao():
    """Retorna o mapa de apuração."""
    if not dados_sessao["mapa"]:
        return JSONResponse({
            "success": False,
            "message": "Nenhuma apuração disponível"
        }, status_code=404)
    
    apuracoes = []
    for apuracao in dados_sessao["mapa"].apuracoes:
        apuracoes.append({
            "tributo": apuracao.tipo.value,
            "debitos": float(apuracao.debitos),
            "creditos": float(apuracao.creditos),
            "saldo": float(apuracao.saldo)
        })
    
    return JSONResponse({
        "periodo": dados_sessao["mapa"].periodo,
        "apuracoes": apuracoes
    })


# ============= API DE ESTATÍSTICAS FASE 1 =============

@app.get("/api/estatisticas/fase1", tags=["Estatísticas"])
async def obter_estatisticas_fase1(
    empresa_id: int = None,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Retorna estatísticas dos campos implementados na Fase 1."""
    from etl_service.database import SessionLocal
    from etl_service.models import NFe, NFeItem
    from sqlalchemy import func, and_
    
    etl_db = SessionLocal()
    
    try:
        # Validar empresa_id
        if empresa_id is None:
            raise HTTPException(status_code=400, detail="Parâmetro empresa_id é obrigatório")
        
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        # Filtro por CNPJ da empresa
        cnpj_filtro = empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        # Total de NF-es da empresa
        total_nfes = etl_db.query(func.count(NFe.id)).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).scalar() or 0
        
        # Indicadores
        estatisticas = {
            "total_nfes": total_nfes,
            "indicadores": {
                "presenca": {},
                "final": {},
                "intermediador": {}
            },
            "naturezas_operacao": [],
            "beneficios_fiscais": [],
            "pagamento_eletronico": {
                "total": 0,
                "tipos": []
            },
            "intermediadores": []
        }
        
        # Distribuição de indicador_presenca
        dist_presenca = etl_db.query(
            NFe.indicador_presenca,
            func.count(NFe.id).label('count')
        ).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.indicador_presenca.isnot(None)
            )
        ).group_by(NFe.indicador_presenca).all()
        
        indicadores_presenca_desc = {
            '0': 'Não se aplica',
            '1': 'Operação presencial',
            '2': 'Internet',
            '3': 'Teleatendimento',
            '4': 'Entrega a domicílio',
            '5': 'Fora do estabelecimento',
            '9': 'Outros'
        }
        
        for cod, count in dist_presenca:
            estatisticas["indicadores"]["presenca"][indicadores_presenca_desc.get(cod, cod)] = count
        
        # Distribuição de indicador_final
        dist_final = etl_db.query(
            NFe.indicador_final,
            func.count(NFe.id).label('count')
        ).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.indicador_final.isnot(None)
            )
        ).group_by(NFe.indicador_final).all()
        
        for cod, count in dist_final:
            desc = 'Consumidor final' if cod == '1' else 'Normal'
            estatisticas["indicadores"]["final"][desc] = count
        
        # Distribuição de indicador_intermediador
        dist_inter = etl_db.query(
            NFe.indicador_intermediador,
            func.count(NFe.id).label('count')
        ).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.indicador_intermediador.isnot(None)
            )
        ).group_by(NFe.indicador_intermediador).all()
        
        for cod, count in dist_inter:
            desc = 'Com intermediador' if cod == '1' else 'Sem intermediador'
            estatisticas["indicadores"]["intermediador"][desc] = count
        
        # Top 10 naturezas de operação
        top_naturezas = etl_db.query(
            NFe.natureza_operacao,
            func.count(NFe.id).label('count')
        ).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.natureza_operacao.isnot(None)
            )
        ).group_by(
            NFe.natureza_operacao
        ).order_by(
            func.count(NFe.id).desc()
        ).limit(10).all()
        
        estatisticas["naturezas_operacao"] = [
            {"natureza": nat, "quantidade": count}
            for nat, count in top_naturezas
        ]
        
        # Pagamento eletrônico
        pag_eletronico = etl_db.query(func.count(NFe.id)).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.tipo_integracao_pagamento.isnot(None)
            )
        ).scalar() or 0
        
        estatisticas["pagamento_eletronico"]["total"] = pag_eletronico
        
        # Tipos de integração
        tipos_integracao = etl_db.query(
            NFe.tipo_integracao_pagamento,
            func.count(NFe.id).label('count')
        ).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.tipo_integracao_pagamento.isnot(None)
            )
        ).group_by(NFe.tipo_integracao_pagamento).all()
        
        tipos_desc = {
            '1': 'Pagamento integrado com sistema da empresa',
            '2': 'Pagamento não integrado'
        }
        
        estatisticas["pagamento_eletronico"]["tipos"] = [
            {"tipo": tipos_desc.get(tipo, tipo), "quantidade": count}
            for tipo, count in tipos_integracao
        ]
        
        # Intermediadores
        intermediadores = etl_db.query(
            NFe.cnpj_intermediador,
            func.count(NFe.id).label('count')
        ).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.cnpj_intermediador.isnot(None)
            )
        ).group_by(NFe.cnpj_intermediador).limit(10).all()
        
        estatisticas["intermediadores"] = [
            {"cnpj": cnpj, "quantidade": count}
            for cnpj, count in intermediadores
        ]
        
        # Benefícios fiscais (dos itens)
        beneficios = etl_db.query(
            NFeItem.codigo_beneficio_fiscal,
            func.count(NFeItem.id).label('count')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFeItem.codigo_beneficio_fiscal.isnot(None),
                NFeItem.codigo_beneficio_fiscal != '0000000000'
            )
        ).group_by(
            NFeItem.codigo_beneficio_fiscal
        ).order_by(
            func.count(NFeItem.id).desc()
        ).limit(10).all()
        
        estatisticas["beneficios_fiscais"] = [
            {"codigo": cod, "quantidade": count}
            for cod, count in beneficios
        ]
        
        return JSONResponse(estatisticas)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")
    finally:
        etl_db.close()



# ============= BI FISCAL COMPLETO =============

@app.get("/bi-fiscal", response_class=HTMLResponse, tags=["BI Fiscal"])
async def pagina_bi_fiscal(
    request: Request,
    empresa_id: int = None
):
    """Página principal do Business Intelligence Fiscal."""
    return templates.TemplateResponse("bi_fiscal.html", {
        "request": request,
        "empresa_id": empresa_id
    })


@app.get("/api/bi-fiscal/conformidade", tags=["BI Fiscal"])
async def bi_conformidade(
    empresa_id: int,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Visão 1: Conformidade Fiscal - Validações e erros."""
    from etl_service.database import SessionLocal
    from etl_service.models import NFe
    from sqlalchemy import func, and_
    
    etl_db = SessionLocal()
    
    try:
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        cnpj_filtro = empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        # Total de documentos
        total_docs = etl_db.query(func.count(NFe.id)).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).scalar() or 0
        
        # Documentos cancelados (simulação - baseado em campos)
        cancelados = etl_db.query(func.count(NFe.id)).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.tipo_operacao == 'cancelamento'  # Ajustar conforme modelo
            )
        ).scalar() or 0
        
        # Estimativa de documentos com erro (baseado em validações básicas)
        docs_erro = 0  # Implementar validações específicas
        
        taxa_conformidade = ((total_docs - docs_erro - cancelados) / total_docs * 100) if total_docs > 0 else 100
        
        return {
            "total_documentos": total_docs,
            "taxa_conformidade": round(taxa_conformidade, 2),
            "documentos_erro": docs_erro,
            "cancelamentos": cancelados
        }
        
    finally:
        etl_db.close()


@app.get("/api/bi-fiscal/exposicao", tags=["BI Fiscal"])
async def bi_exposicao(
    empresa_id: int,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Visão 2: Exposição Tributária - Impacto financeiro dos impostos."""
    from etl_service.database import SessionLocal
    from etl_service.models import NFe, NFeItem
    from sqlalchemy import func, and_
    from decimal import Decimal
    
    etl_db = SessionLocal()
    
    try:
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        cnpj_filtro = empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        # Somar todos os impostos
        impostos = etl_db.query(
            func.sum(NFeItem.valor_icms).label('icms'),
            func.sum(NFeItem.valor_ipi).label('ipi'),
            func.sum(NFeItem.valor_pis).label('pis'),
            func.sum(NFeItem.valor_cofins).label('cofins')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).first()
        
        icms_total = float(impostos.icms or 0)
        ipi_total = float(impostos.ipi or 0)
        pis_total = float(impostos.pis or 0)
        cofins_total = float(impostos.cofins or 0)
        
        total_impostos = icms_total + ipi_total + pis_total + cofins_total
        
        # Valor total de operações
        valor_total = etl_db.query(
            func.sum(NFe.valor_total_nota)
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).scalar() or 0
        
        carga_efetiva = (total_impostos / float(valor_total) * 100) if valor_total > 0 else 0
        
        # Créditos (entradas - tipo_operacao '0')
        creditos = etl_db.query(
            func.sum(NFeItem.valor_icms)
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.tipo_operacao == '0'
            )
        ).scalar() or 0
        
        return {
            "total_impostos": round(total_impostos, 2),
            "icms_total": round(icms_total, 2),
            "ipi_total": round(ipi_total, 2),
            "pis_total": round(pis_total, 2),
            "cofins_total": round(cofins_total, 2),
            "creditos_acumulados": round(float(creditos), 2),
            "carga_efetiva": round(carga_efetiva, 2),
            "distribuicao_impostos": {
                "ICMS": round(icms_total, 2),
                "IPI": round(ipi_total, 2),
                "PIS": round(pis_total, 2),
                "COFINS": round(cofins_total, 2)
            }
        }
        
    finally:
        etl_db.close()


@app.get("/api/bi-fiscal/parceiros", tags=["BI Fiscal"])
async def bi_parceiros(
    empresa_id: int,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Visão 3: Operações por Parceiro - Volume e características."""
    from etl_service.database import SessionLocal
    from etl_service.models import NFe
    from sqlalchemy import func, and_, or_
    
    etl_db = SessionLocal()
    
    try:
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        cnpj_filtro = empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        # Top parceiros (clientes e fornecedores)
        parceiros = etl_db.query(
            func.coalesce(NFe.destinatario_razao_social, NFe.emitente_razao_social).label('razao_social'),
            func.count(NFe.id).label('total_operacoes'),
            func.sum(NFe.valor_total_nota).label('valor_total')
        ).filter(
            or_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.destinatario_cnpj == cnpj_filtro
            )
        ).group_by(
            func.coalesce(NFe.destinatario_razao_social, NFe.emitente_razao_social)
        ).order_by(
            func.sum(NFe.valor_total_nota).desc()
        ).limit(10).all()
        
        valor_total_geral = sum(float(p.valor_total or 0) for p in parceiros) or 1
        
        top_parceiros = []
        for p in parceiros:
            valor = float(p.valor_total or 0)
            top_parceiros.append({
                "razao_social": p.razao_social or "Não identificado",
                "total_operacoes": p.total_operacoes,
                "valor_total": round(valor, 2),
                "participacao": round((valor / valor_total_geral) * 100, 2)
            })
        
        # Total de parceiros únicos
        total_parceiros = etl_db.query(
            func.count(func.distinct(
                func.coalesce(NFe.destinatario_cnpj, NFe.emitente_cnpj)
            ))
        ).filter(
            or_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.destinatario_cnpj == cnpj_filtro
            )
        ).scalar() or 0
        
        # Concentração top 5
        top5_valor = sum(p["valor_total"] for p in top_parceiros[:5])
        concentracao_top5 = round((top5_valor / valor_total_geral) * 100, 2) if valor_total_geral > 0 else 0
        
        # Ticket médio
        total_ops = sum(p["total_operacoes"] for p in top_parceiros)
        ticket_medio = round(valor_total_geral / total_ops, 2) if total_ops > 0 else 0
        
        return {
            "total_parceiros": total_parceiros,
            "concentracao_top5": concentracao_top5,
            "ticket_medio": ticket_medio,
            "novos_parceiros": 0,  # Implementar lógica temporal
            "top_parceiros": top_parceiros
        }
        
    finally:
        etl_db.close()


@app.get("/api/bi-fiscal/temporalidade", tags=["BI Fiscal"])
async def bi_temporalidade(
    empresa_id: int,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Visão 4: Temporalidade e Sazonalidade - Padrões temporais."""
    from etl_service.database import SessionLocal
    from etl_service.models import NFe
    from sqlalchemy import func, extract
    from datetime import datetime, timedelta
    
    etl_db = SessionLocal()
    
    try:
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        cnpj_filtro = empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        # Total de documentos
        total_docs = etl_db.query(func.count(NFe.id)).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).scalar() or 1
        
        # Média diária (estimativa simples)
        media_diaria = round(total_docs / 30, 0)  # Ajustar com datas reais
        
        # Pico de emissão por dia
        pico = etl_db.query(
            func.date(NFe.data_emissao).label('data'),
            func.count(NFe.id).label('quantidade')
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).group_by(
            func.date(NFe.data_emissao)
        ).order_by(
            func.count(NFe.id).desc()
        ).first()
        
        pico_emissao = pico.quantidade if pico else 0
        data_pico = pico.data.strftime('%d/%m/%Y') if pico and pico.data else 'N/A'
        
        return {
            "media_diaria": media_diaria,
            "pico_emissao": pico_emissao,
            "data_pico": data_pico,
            "tendencia": 0,  # Implementar cálculo de tendência
            "horario_pico": "14h-16h"  # Implementar análise de horários
        }
        
    finally:
        etl_db.close()


@app.get("/api/bi-fiscal/eficiencia", tags=["BI Fiscal"])
async def bi_eficiencia(
    empresa_id: int,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Visão 5: Eficiência Operacional - Métricas de performance."""
    from etl_service.database import SessionLocal
    from etl_service.models import NFe, NFeItem
    from sqlalchemy import func, and_
    
    etl_db = SessionLocal()
    
    try:
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        cnpj_filtro = empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        # Total de documentos
        total_docs = etl_db.query(func.count(NFe.id)).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).scalar() or 1
        
        # Tempo médio de processamento (simulado)
        tempo_medio = round(total_docs * 0.5, 2)
        
        # Taxa de rejeição
        rejeitados = etl_db.query(func.count(NFe.id)).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.motivo_status.isnot(None)
            )
        ).scalar() or 0
        
        taxa_rejeicao = round((rejeitados / total_docs) * 100, 2) if total_docs > 0 else 0
        
        # Produtividade (docs/dia)
        produtividade = round(total_docs / 30, 0)
        
        # Custo operacional estimado
        custo_operacional = round(total_docs * 2.5, 2)
        
        return {
            "tempo_medio_processamento": tempo_medio,
            "taxa_rejeicao": taxa_rejeicao,
            "produtividade_diaria": produtividade,
            "custo_operacional": custo_operacional,
            "eficiencia_geral": round(100 - taxa_rejeicao, 2)
        }
        
    finally:
        etl_db.close()


@app.get("/api/bi-fiscal/risco", tags=["BI Fiscal"])
async def bi_risco(
    empresa_id: int,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Visão 6: Risco Fiscal e Auditoria - Indicadores de risco."""
    from etl_service.database import SessionLocal
    from etl_service.models import NFe
    from sqlalchemy import func, and_
    
    etl_db = SessionLocal()
    
    try:
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        cnpj_filtro = empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        # Total de documentos
        total_docs = etl_db.query(func.count(NFe.id)).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).scalar() or 1
        
        # Documentos com divergências
        divergencias = etl_db.query(func.count(NFe.id)).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.motivo_status.isnot(None)
            )
        ).scalar() or 0
        
        # Score de risco (0-100, onde 0 é baixo risco)
        score_risco = round((divergencias / total_docs) * 100, 2) if total_docs > 0 else 0
        
        # Documentos cancelados
        cancelados = etl_db.query(func.count(NFe.id)).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFe.situacao == 'Cancelada'
            )
        ).scalar() or 0
        
        # Alertas críticos
        alertas_criticos = divergencias
        
        return {
            "score_risco": score_risco,
            "divergencias_detectadas": divergencias,
            "documentos_suspeitos": cancelados,
            "alertas_criticos": alertas_criticos,
            "status_risco": "Baixo" if score_risco < 5 else ("Médio" if score_risco < 15 else "Alto")
        }
        
    finally:
        etl_db.close()


@app.get("/api/bi-fiscal/produto", tags=["BI Fiscal"])
async def bi_produto(
    empresa_id: int,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Visão 7: Análise por Produto - NCM, CFOP e Tributação detalhada."""
    from etl_service.database import SessionLocal
    from etl_service.models import NFe, NFeItem
    from sqlalchemy import func, case, distinct
    from collections import defaultdict
    
    etl_db = SessionLocal()
    
    try:
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        cnpj_filtro = empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        # ========== ANÁLISE POR NCM ==========
        analise_ncm = etl_db.query(
            NFeItem.ncm,
            func.count(distinct(NFeItem.descricao)).label('produtos_distintos'),
            func.count(NFeItem.id).label('lancamentos'),
            func.sum(NFeItem.quantidade_comercial).label('quantidade'),
            func.sum(NFeItem.valor_total_item).label('valor_contabil'),
            func.sum(NFeItem.base_calculo_icms).label('bc_icms'),
            func.sum(NFeItem.base_calculo_ipi).label('bc_ipi'),
            func.sum(NFeItem.base_calculo_pis).label('bc_pis'),
            func.sum(NFeItem.base_calculo_cofins).label('bc_cofins'),
            func.avg(NFeItem.aliquota_icms).label('aliq_media_icms'),
            func.avg(NFeItem.aliquota_ipi).label('aliq_media_ipi'),
            func.avg(NFeItem.aliquota_pis).label('aliq_media_pis'),
            func.avg(NFeItem.aliquota_cofins).label('aliq_media_cofins'),
            func.sum(NFeItem.valor_icms).label('total_icms'),
            func.sum(NFeItem.valor_ipi).label('total_ipi'),
            func.sum(NFeItem.valor_pis).label('total_pis'),
            func.sum(NFeItem.valor_cofins).label('total_cofins'),
            func.sum(NFeItem.valor_ibs).label('total_ibs'),
            func.sum(NFeItem.valor_cbs).label('total_cbs'),
            func.avg(NFeItem.aliquota_ibs).label('aliq_media_ibs'),
            func.avg(NFeItem.aliquota_cbs).label('aliq_media_cbs')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro,
            NFeItem.ncm.isnot(None)
        ).group_by(
            NFeItem.ncm
        ).order_by(
            func.sum(NFeItem.valor_total_item).desc()
        ).limit(20).all()
        
        ncm_list = []
        for ncm in analise_ncm:
            valor_total = float(ncm.valor_contabil or 0)
            total_tributos = float(ncm.total_icms or 0) + float(ncm.total_ipi or 0) + \
                           float(ncm.total_pis or 0) + float(ncm.total_cofins or 0) + \
                           float(ncm.total_ibs or 0) + float(ncm.total_cbs or 0)
            
            carga_tributaria = (total_tributos / valor_total * 100) if valor_total > 0 else 0
            
            ncm_list.append({
                "ncm": ncm.ncm or "N/A",
                "produtos_distintos": ncm.produtos_distintos,
                "lancamentos": ncm.lancamentos,
                "quantidade": round(float(ncm.quantidade or 0), 2),
                "valor_contabil": round(valor_total, 2),
                "bc_icms": round(float(ncm.bc_icms or 0), 2),
                "bc_ipi": round(float(ncm.bc_ipi or 0), 2),
                "aliq_icms": round(float(ncm.aliq_media_icms or 0), 2),
                "aliq_ipi": round(float(ncm.aliq_media_ipi or 0), 2),
                "aliq_pis": round(float(ncm.aliq_media_pis or 0), 4),
                "aliq_cofins": round(float(ncm.aliq_media_cofins or 0), 4),
                "aliq_ibs": round(float(ncm.aliq_media_ibs or 0), 4),
                "aliq_cbs": round(float(ncm.aliq_media_cbs or 0), 4),
                "valor_icms": round(float(ncm.total_icms or 0), 2),
                "valor_ipi": round(float(ncm.total_ipi or 0), 2),
                "valor_pis": round(float(ncm.total_pis or 0), 2),
                "valor_cofins": round(float(ncm.total_cofins or 0), 2),
                "valor_ibs": round(float(ncm.total_ibs or 0), 2),
                "valor_cbs": round(float(ncm.total_cbs or 0), 2),
                "carga_tributaria": round(carga_tributaria, 2)
            })
        
        # ========== ANÁLISE POR CFOP ==========
        analise_cfop = etl_db.query(
            NFeItem.cfop,
            func.count(NFeItem.id).label('lancamentos'),
            func.sum(NFeItem.quantidade_comercial).label('quantidade'),
            func.sum(NFeItem.valor_total_item).label('valor_total'),
            func.sum(NFeItem.base_calculo_icms).label('bc_icms'),
            func.sum(NFeItem.valor_icms).label('valor_icms'),
            func.sum(NFeItem.valor_ipi).label('valor_ipi'),
            func.sum(NFeItem.valor_pis).label('valor_pis'),
            func.sum(NFeItem.valor_cofins).label('valor_cofins'),
            func.sum(NFeItem.valor_ibs).label('valor_ibs'),
            func.sum(NFeItem.valor_cbs).label('valor_cbs')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro,
            NFeItem.cfop.isnot(None)
        ).group_by(
            NFeItem.cfop
        ).order_by(
            func.sum(NFeItem.valor_total_item).desc()
        ).all()
        
        cfop_list = []
        cfop_entrada = 0
        cfop_saida = 0
        cfop_interno = 0
        cfop_interestadual = 0
        cfop_exportacao = 0
        
        for cfop in analise_cfop:
            cfop_code = cfop.cfop or "0000"
            valor = float(cfop.valor_total or 0)
            
            # Classificar CFOP
            tipo = "Desconhecido"
            if cfop_code.startswith('1'):
                tipo = "Entrada - Estadual"
                cfop_entrada += valor
                cfop_interno += valor
            elif cfop_code.startswith('2'):
                tipo = "Entrada - Interestadual"
                cfop_entrada += valor
                cfop_interestadual += valor
            elif cfop_code.startswith('3'):
                tipo = "Entrada - Exterior"
                cfop_entrada += valor
            elif cfop_code.startswith('5'):
                tipo = "Saída - Estadual"
                cfop_saida += valor
                cfop_interno += valor
            elif cfop_code.startswith('6'):
                tipo = "Saída - Interestadual"
                cfop_saida += valor
                cfop_interestadual += valor
            elif cfop_code.startswith('7'):
                tipo = "Saída - Exterior"
                cfop_saida += valor
                cfop_exportacao += valor
            
            total_tributos = float(cfop.valor_icms or 0) + float(cfop.valor_ipi or 0) + \
                           float(cfop.valor_pis or 0) + float(cfop.valor_cofins or 0) + \
                           float(cfop.valor_ibs or 0) + float(cfop.valor_cbs or 0)
            
            cfop_list.append({
                "cfop": cfop_code,
                "tipo": tipo,
                "lancamentos": cfop.lancamentos,
                "quantidade": round(float(cfop.quantidade or 0), 2),
                "valor_total": round(valor, 2),
                "bc_icms": round(float(cfop.bc_icms or 0), 2),
                "valor_icms": round(float(cfop.valor_icms or 0), 2),
                "valor_ipi": round(float(cfop.valor_ipi or 0), 2),
                "valor_pis": round(float(cfop.valor_pis or 0), 2),
                "valor_cofins": round(float(cfop.valor_cofins or 0), 2),
                "valor_ibs": round(float(cfop.valor_ibs or 0), 2),
                "valor_cbs": round(float(cfop.valor_cbs or 0), 2),
                "total_tributos": round(total_tributos, 2)
            })
        
        # ========== ANÁLISE NCM x CFOP ==========
        analise_ncm_cfop = etl_db.query(
            NFeItem.ncm,
            NFeItem.cfop,
            func.count(NFeItem.id).label('lancamentos'),
            func.avg(NFeItem.aliquota_icms).label('aliq_icms'),
            func.avg(NFeItem.aliquota_ipi).label('aliq_ipi'),
            func.sum(NFeItem.valor_total_item).label('valor_total')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro,
            NFeItem.ncm.isnot(None),
            NFeItem.cfop.isnot(None)
        ).group_by(
            NFeItem.ncm,
            NFeItem.cfop
        ).all()
        
        # Detectar divergências (mesma NCM com alíquotas diferentes)
        ncm_aliquotas = defaultdict(list)
        for item in analise_ncm_cfop:
            if item.aliq_icms is not None:
                ncm_aliquotas[item.ncm].append({
                    'cfop': item.cfop,
                    'aliq_icms': float(item.aliq_icms),
                    'aliq_ipi': float(item.aliq_ipi or 0),
                    'lancamentos': item.lancamentos,
                    'valor': float(item.valor_total or 0)
                })
        
        divergencias = []
        for ncm, aliquotas in ncm_aliquotas.items():
            if len(aliquotas) > 1:
                # Verificar variação de alíquotas
                aliq_icms_list = [a['aliq_icms'] for a in aliquotas if a['aliq_icms'] > 0]
                if len(set(aliq_icms_list)) > 1:  # Alíquotas diferentes
                    aliq_min = min(aliq_icms_list)
                    aliq_max = max(aliq_icms_list)
                    variacao = aliq_max - aliq_min
                    
                    if variacao > 2:  # Variação maior que 2%
                        divergencias.append({
                            "ncm": ncm,
                            "aliq_min": round(aliq_min, 2),
                            "aliq_max": round(aliq_max, 2),
                            "variacao": round(variacao, 2),
                            "cfops": [a['cfop'] for a in aliquotas],
                            "lancamentos_total": sum(a['lancamentos'] for a in aliquotas),
                            "tipo": "ICMS"
                        })
        
        # Ordenar divergências por variação
        divergencias.sort(key=lambda x: x['variacao'], reverse=True)
        
        # ========== TOP PRODUTOS DETALHADO ==========
        top_produtos = etl_db.query(
            NFeItem.descricao,
            NFeItem.ncm,
            NFeItem.cfop,
            func.count(NFeItem.id).label('lancamentos'),
            func.sum(NFeItem.quantidade_comercial).label('quantidade'),
            func.sum(NFeItem.valor_total_item).label('valor_total'),
            func.sum(NFeItem.valor_icms).label('valor_icms'),
            func.sum(NFeItem.valor_ipi).label('valor_ipi'),
            func.sum(NFeItem.valor_pis).label('valor_pis'),
            func.sum(NFeItem.valor_cofins).label('valor_cofins')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).group_by(
            NFeItem.descricao,
            NFeItem.ncm,
            NFeItem.cfop
        ).order_by(
            func.sum(NFeItem.valor_total_item).desc()
        ).limit(15).all()
        
        produtos_list = []
        for prod in top_produtos:
            quantidade = float(prod.quantidade or 0)
            valor = float(prod.valor_total or 0)
            
            produtos_list.append({
                "produto": prod.descricao or "Sem descrição",
                "ncm": prod.ncm or "N/A",
                "cfop": prod.cfop or "N/A",
                "lancamentos": prod.lancamentos,
                "quantidade": round(quantidade, 2),
                "valor_total": round(valor, 2),
                "valor_medio": round(valor / quantidade, 2) if quantidade > 0 else 0,
                "valor_icms": round(float(prod.valor_icms or 0), 2),
                "valor_ipi": round(float(prod.valor_ipi or 0), 2),
                "valor_pis": round(float(prod.valor_pis or 0), 2),
                "valor_cofins": round(float(prod.valor_cofins or 0), 2)
            })
        
        # ========== TOTALIZADORES ==========
        total_itens = etl_db.query(
            func.count(func.distinct(NFeItem.codigo_produto))
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).scalar() or 0
        
        total_ncm_distintos = etl_db.query(
            func.count(func.distinct(NFeItem.ncm))
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro,
            NFeItem.ncm.isnot(None)
        ).scalar() or 0
        
        total_cfop_distintos = etl_db.query(
            func.count(func.distinct(NFeItem.cfop))
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro,
            NFeItem.cfop.isnot(None)
        ).scalar() or 0
        
        # ========== ANÁLISE POR CST ==========
        # CST de ICMS
        cst_icms_dict = {
            '00': 'Tributada integralmente',
            '10': 'Tributada com cobrança de ICMS por ST',
            '20': 'Com redução de base de cálculo',
            '30': 'Isenta ou não tributada com cobrança de ICMS por ST',
            '40': 'Isenta',
            '41': 'Não tributada',
            '50': 'Suspensão',
            '51': 'Diferimento',
            '60': 'ICMS cobrado anteriormente por ST',
            '70': 'Com redução de BC e cobrança de ICMS por ST',
            '90': 'Outras',
            '101': 'Simples Nacional - Tributada com permissão de crédito',
            '102': 'Simples Nacional - Tributada sem permissão de crédito',
            '103': 'Simples Nacional - Isenção de ICMS',
            '201': 'Simples Nacional - Tributada com permissão de crédito e com cobrança do ICMS por ST',
            '202': 'Simples Nacional - Tributada sem permissão de crédito e com cobrança do ICMS por ST',
            '203': 'Simples Nacional - Isenção de ICMS e com cobrança do ICMS por ST',
            '300': 'Simples Nacional - Imune',
            '400': 'Simples Nacional - Não tributada',
            '500': 'Simples Nacional - ICMS cobrado anteriormente por ST ou por antecipação',
            '900': 'Simples Nacional - Outros'
        }
        
        # CST ICMS - ENTRADA
        analise_cst_icms_entrada = etl_db.query(
            NFeItem.situacao_tributaria_icms,
            func.count(NFeItem.id).label('lancamentos'),
            func.sum(NFeItem.valor_total_item).label('valor_total'),
            func.sum(NFeItem.base_calculo_icms).label('bc_icms'),
            func.sum(NFeItem.valor_icms).label('valor_icms'),
            func.avg(NFeItem.aliquota_icms).label('aliq_media')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro,
            NFe.tipo_operacao == '0',  # Entrada
            NFeItem.situacao_tributaria_icms.isnot(None)
        ).group_by(
            NFeItem.situacao_tributaria_icms
        ).order_by(
            func.sum(NFeItem.valor_total_item).desc()
        ).all()
        
        cst_icms_entrada_list = []
        for cst in analise_cst_icms_entrada:
            cst_code = cst.situacao_tributaria_icms or "N/A"
            cst_icms_entrada_list.append({
                "cst": cst_code,
                "descricao": cst_icms_dict.get(cst_code, "Desconhecido"),
                "lancamentos": cst.lancamentos,
                "valor_total": round(float(cst.valor_total or 0), 2),
                "bc_icms": round(float(cst.bc_icms or 0), 2),
                "valor_icms": round(float(cst.valor_icms or 0), 2),
                "aliq_media": round(float(cst.aliq_media or 0), 2)
            })
        
        # CST ICMS - SAÍDA
        analise_cst_icms_saida = etl_db.query(
            NFeItem.situacao_tributaria_icms,
            func.count(NFeItem.id).label('lancamentos'),
            func.sum(NFeItem.valor_total_item).label('valor_total'),
            func.sum(NFeItem.base_calculo_icms).label('bc_icms'),
            func.sum(NFeItem.valor_icms).label('valor_icms'),
            func.avg(NFeItem.aliquota_icms).label('aliq_media')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro,
            NFe.tipo_operacao == '1',  # Saída
            NFeItem.situacao_tributaria_icms.isnot(None)
        ).group_by(
            NFeItem.situacao_tributaria_icms
        ).order_by(
            func.sum(NFeItem.valor_total_item).desc()
        ).all()
        
        cst_icms_saida_list = []
        for cst in analise_cst_icms_saida:
            cst_code = cst.situacao_tributaria_icms or "N/A"
            cst_icms_saida_list.append({
                "cst": cst_code,
                "descricao": cst_icms_dict.get(cst_code, "Desconhecido"),
                "lancamentos": cst.lancamentos,
                "valor_total": round(float(cst.valor_total or 0), 2),
                "bc_icms": round(float(cst.bc_icms or 0), 2),
                "valor_icms": round(float(cst.valor_icms or 0), 2),
                "aliq_media": round(float(cst.aliq_media or 0), 2)
            })
        
        # CST de PIS
        cst_pis_dict = {
            '01': 'Operação Tributável com Alíquota Básica',
            '02': 'Operação Tributável com Alíquota Diferenciada',
            '03': 'Operação Tributável com Alíquota por Unidade de Medida de Produto',
            '04': 'Operação Tributável Monofásica - Revenda a Alíquota Zero',
            '05': 'Operação Tributável por Substituição Tributária',
            '06': 'Operação Tributável a Alíquota Zero',
            '07': 'Operação Isenta da Contribuição',
            '08': 'Operação sem Incidência da Contribuição',
            '09': 'Operação com Suspensão da Contribuição',
            '49': 'Outras Operações de Saída',
            '50': 'Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Tributada no Mercado Interno',
            '51': 'Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Não Tributada no Mercado Interno',
            '52': 'Operação com Direito a Crédito - Vinculada Exclusivamente a Receita de Exportação',
            '53': 'Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno',
            '54': 'Operação com Direito a Crédito - Vinculada a Receitas Tributadas no Mercado Interno e de Exportação',
            '55': 'Operação com Direito a Crédito - Vinculada a Receitas Não-Tributadas no Mercado Interno e de Exportação',
            '56': 'Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno e de Exportação',
            '60': 'Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Tributada no Mercado Interno',
            '61': 'Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Não-Tributada no Mercado Interno',
            '62': 'Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita de Exportação',
            '63': 'Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno',
            '64': 'Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas no Mercado Interno e de Exportação',
            '65': 'Crédito Presumido - Operação de Aquisição Vinculada a Receitas Não-Tributadas no Mercado Interno e de Exportação',
            '66': 'Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno e de Exportação',
            '67': 'Crédito Presumido - Outras Operações',
            '70': 'Operação de Aquisição sem Direito a Crédito',
            '71': 'Operação de Aquisição com Isenção',
            '72': 'Operação de Aquisição com Suspensão',
            '73': 'Operação de Aquisição a Alíquota Zero',
            '74': 'Operação de Aquisição sem Incidência da Contribuição',
            '75': 'Operação de Aquisição por Substituição Tributária',
            '98': 'Outras Operações de Entrada',
            '99': 'Outras Operações'
        }
        
        # CST PIS - ENTRADA
        analise_cst_pis_entrada = etl_db.query(
            NFeItem.situacao_tributaria_pis,
            func.count(NFeItem.id).label('lancamentos'),
            func.sum(NFeItem.valor_total_item).label('valor_total'),
            func.sum(NFeItem.base_calculo_pis).label('bc_pis'),
            func.sum(NFeItem.valor_pis).label('valor_pis'),
            func.avg(NFeItem.aliquota_pis).label('aliq_media')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro,
            NFe.tipo_operacao == '0',  # Entrada
            NFeItem.situacao_tributaria_pis.isnot(None)
        ).group_by(
            NFeItem.situacao_tributaria_pis
        ).order_by(
            func.sum(NFeItem.valor_total_item).desc()
        ).all()
        
        cst_pis_entrada_list = []
        for cst in analise_cst_pis_entrada:
            cst_code = cst.situacao_tributaria_pis or "N/A"
            cst_pis_entrada_list.append({
                "cst": cst_code,
                "descricao": cst_pis_dict.get(cst_code, "Desconhecido"),
                "lancamentos": cst.lancamentos,
                "valor_total": round(float(cst.valor_total or 0), 2),
                "bc_pis": round(float(cst.bc_pis or 0), 2),
                "valor_pis": round(float(cst.valor_pis or 0), 2),
                "aliq_media": round(float(cst.aliq_media or 0), 4)
            })
        
        # CST PIS - SAÍDA
        analise_cst_pis_saida = etl_db.query(
            NFeItem.situacao_tributaria_pis,
            func.count(NFeItem.id).label('lancamentos'),
            func.sum(NFeItem.valor_total_item).label('valor_total'),
            func.sum(NFeItem.base_calculo_pis).label('bc_pis'),
            func.sum(NFeItem.valor_pis).label('valor_pis'),
            func.avg(NFeItem.aliquota_pis).label('aliq_media')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro,
            NFe.tipo_operacao == '1',  # Saída
            NFeItem.situacao_tributaria_pis.isnot(None)
        ).group_by(
            NFeItem.situacao_tributaria_pis
        ).order_by(
            func.sum(NFeItem.valor_total_item).desc()
        ).all()
        
        cst_pis_saida_list = []
        for cst in analise_cst_pis_saida:
            cst_code = cst.situacao_tributaria_pis or "N/A"
            cst_pis_saida_list.append({
                "cst": cst_code,
                "descricao": cst_pis_dict.get(cst_code, "Desconhecido"),
                "lancamentos": cst.lancamentos,
                "valor_total": round(float(cst.valor_total or 0), 2),
                "bc_pis": round(float(cst.bc_pis or 0), 2),
                "valor_pis": round(float(cst.valor_pis or 0), 2),
                "aliq_media": round(float(cst.aliq_media or 0), 4)
            })
        
        # CST de COFINS
        cst_cofins_dict = cst_pis_dict  # COFINS usa mesma tabela de CST do PIS
        
        # CST COFINS - ENTRADA
        analise_cst_cofins_entrada = etl_db.query(
            NFeItem.situacao_tributaria_cofins,
            func.count(NFeItem.id).label('lancamentos'),
            func.sum(NFeItem.valor_total_item).label('valor_total'),
            func.sum(NFeItem.base_calculo_cofins).label('bc_cofins'),
            func.sum(NFeItem.valor_cofins).label('valor_cofins'),
            func.avg(NFeItem.aliquota_cofins).label('aliq_media')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro,
            NFe.tipo_operacao == '0',  # Entrada
            NFeItem.situacao_tributaria_cofins.isnot(None)
        ).group_by(
            NFeItem.situacao_tributaria_cofins
        ).order_by(
            func.sum(NFeItem.valor_total_item).desc()
        ).all()
        
        cst_cofins_entrada_list = []
        for cst in analise_cst_cofins_entrada:
            cst_code = cst.situacao_tributaria_cofins or "N/A"
            cst_cofins_entrada_list.append({
                "cst": cst_code,
                "descricao": cst_cofins_dict.get(cst_code, "Desconhecido"),
                "lancamentos": cst.lancamentos,
                "valor_total": round(float(cst.valor_total or 0), 2),
                "bc_cofins": round(float(cst.bc_cofins or 0), 2),
                "valor_cofins": round(float(cst.valor_cofins or 0), 2),
                "aliq_media": round(float(cst.aliq_media or 0), 4)
            })
        
        # CST COFINS - SAÍDA
        analise_cst_cofins_saida = etl_db.query(
            NFeItem.situacao_tributaria_cofins,
            func.count(NFeItem.id).label('lancamentos'),
            func.sum(NFeItem.valor_total_item).label('valor_total'),
            func.sum(NFeItem.base_calculo_cofins).label('bc_cofins'),
            func.sum(NFeItem.valor_cofins).label('valor_cofins'),
            func.avg(NFeItem.aliquota_cofins).label('aliq_media')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro,
            NFe.tipo_operacao == '1',  # Saída
            NFeItem.situacao_tributaria_cofins.isnot(None)
        ).group_by(
            NFeItem.situacao_tributaria_cofins
        ).order_by(
            func.sum(NFeItem.valor_total_item).desc()
        ).all()
        
        cst_cofins_saida_list = []
        for cst in analise_cst_cofins_saida:
            cst_code = cst.situacao_tributaria_cofins or "N/A"
            cst_cofins_saida_list.append({
                "cst": cst_code,
                "descricao": cst_cofins_dict.get(cst_code, "Desconhecido"),
                "lancamentos": cst.lancamentos,
                "valor_total": round(float(cst.valor_total or 0), 2),
                "bc_cofins": round(float(cst.bc_cofins or 0), 2),
                "valor_cofins": round(float(cst.valor_cofins or 0), 2),
                "aliq_media": round(float(cst.aliq_media or 0), 4)
            })
        
        return {
            "analise_ncm": ncm_list,
            "analise_cfop": cfop_list,
            "analise_cst_icms_entrada": cst_icms_entrada_list,
            "analise_cst_icms_saida": cst_icms_saida_list,
            "analise_cst_pis_entrada": cst_pis_entrada_list,
            "analise_cst_pis_saida": cst_pis_saida_list,
            "analise_cst_cofins_entrada": cst_cofins_entrada_list,
            "analise_cst_cofins_saida": cst_cofins_saida_list,
            "cfop_resumo": {
                "total_entrada": round(cfop_entrada, 2),
                "total_saida": round(cfop_saida, 2),
                "operacoes_internas": round(cfop_interno, 2),
                "operacoes_interestaduais": round(cfop_interestadual, 2),
                "exportacoes": round(cfop_exportacao, 2)
            },
            "divergencias": divergencias[:10],  # Top 10 divergências
            "top_produtos": produtos_list,
            "totalizadores": {
                "produtos_unicos": total_itens,
                "ncm_distintos": total_ncm_distintos,
                "cfop_distintos": total_cfop_distintos,
                "divergencias_detectadas": len(divergencias),
                "cst_icms_entrada_distintos": len(cst_icms_entrada_list),
                "cst_icms_saida_distintos": len(cst_icms_saida_list),
                "cst_pis_entrada_distintos": len(cst_pis_entrada_list),
                "cst_pis_saida_distintos": len(cst_pis_saida_list),
                "cst_cofins_entrada_distintos": len(cst_cofins_entrada_list),
                "cst_cofins_saida_distintos": len(cst_cofins_saida_list)
            }
        }
        
    finally:
        etl_db.close()


@app.get("/api/bi-fiscal/integracao", tags=["BI Fiscal"])
async def bi_integracao(
    empresa_id: int,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Visão 8: Performance de Integrações - Qualidade dos dados."""
    from etl_service.database import SessionLocal
    from etl_service.models import NFe, ArquivoProcessado
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    etl_db = SessionLocal()
    
    try:
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        # Total de arquivos processados
        total_arquivos = etl_db.query(
            func.count(ArquivoProcessado.id)
        ).filter(
            ArquivoProcessado.status == 'sucesso'
        ).scalar() or 0
        
        # Taxa de sucesso
        total_tentativas = etl_db.query(
            func.count(ArquivoProcessado.id)
        ).scalar() or 1
        
        taxa_sucesso = round((total_arquivos / total_tentativas) * 100, 2)
        
        # Tempo médio de processamento
        tempo_medio = etl_db.query(
            func.avg(func.extract('epoch', ArquivoProcessado.data_processamento - ArquivoProcessado.data_processamento))
        ).scalar() or 0
        
        # Documentos processados hoje
        docs_hoje = 0  # Implementar filtro de data
        
        return {
            "total_arquivos_processados": total_arquivos,
            "taxa_sucesso_integracao": taxa_sucesso,
            "tempo_medio_integracao": round(float(tempo_medio), 2),
            "documentos_processados_hoje": docs_hoje,
            "status_sistema": "Operacional"
        }
        
    finally:
        etl_db.close()


@app.get("/api/bi-fiscal/benchmarking", tags=["BI Fiscal"])
async def bi_benchmarking(
    empresa_id: int,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Visão 9: Benchmarking Interno - Comparações entre períodos."""
    from etl_service.database import SessionLocal
    from etl_service.models import NFe
    from sqlalchemy import func, extract
    
    etl_db = SessionLocal()
    
    try:
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        cnpj_filtro = empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        # Performance por mês
        performance_mensal = etl_db.query(
            extract('month', NFe.data_emissao).label('mes'),
            func.count(NFe.id).label('quantidade'),
            func.sum(NFe.valor_total_nota).label('valor_total')
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).group_by(
            extract('month', NFe.data_emissao)
        ).order_by(
            extract('month', NFe.data_emissao)
        ).all()
        
        meses = []
        for perf in performance_mensal:
            meses.append({
                "mes": int(perf.mes) if perf.mes else 0,
                "quantidade": perf.quantidade,
                "valor_total": round(float(perf.valor_total or 0), 2)
            })
        
        # Crescimento médio
        crescimento = 5.2  # Implementar cálculo real
        
        return {
            "crescimento_medio": crescimento,
            "performance_mensal": meses,
            "melhor_mes": max(meses, key=lambda x: x["valor_total"])["mes"] if meses else 0,
            "variacao_trimestral": 0  # Implementar cálculo
        }
        
    finally:
        etl_db.close()


@app.get("/api/bi-fiscal/preditiva", tags=["BI Fiscal"])
async def bi_preditiva(
    empresa_id: int,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Visão 10: Visão Preditiva e de Otimização - Projeções e insights."""
    from etl_service.database import SessionLocal
    from etl_service.models import NFe
    from sqlalchemy import func
    
    etl_db = SessionLocal()
    
    try:
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        cnpj_filtro = empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        # Valor total atual
        valor_atual = etl_db.query(
            func.sum(NFe.valor_total_nota)
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).scalar() or 0
        
        # Projeção próximo mês (estimativa simples)
        projecao = round(float(valor_atual) * 1.05, 2)
        
        # Economia potencial
        economia = round(float(valor_atual) * 0.03, 2)
        
        # Oportunidades
        oportunidades = [
            "Otimizar créditos de ICMS",
            "Revisar enquadramento tributário",
            "Consolidar fornecedores principais"
        ]
        
        return {
            "projecao_proximo_mes": projecao,
            "tendencia": "Crescimento",
            "economia_potencial": economia,
            "oportunidades": oportunidades,
            "confianca_predicao": 85.5
        }
        
    finally:
        etl_db.close()


@app.get("/api/bi-fiscal/reforma", tags=["BI Fiscal"])
async def bi_reforma(
    empresa_id: int,
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Visão 11: Reforma Tributária - IBS e CBS."""
    from etl_service.database import SessionLocal
    from etl_service.models import NFe, NFeItem
    from sqlalchemy import func, and_
    
    etl_db = SessionLocal()
    
    try:
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        cnpj_filtro = empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")
        
        # Total de documentos
        total_docs = etl_db.query(func.count(NFe.id)).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).scalar() or 1
        
        # Somar IBS e CBS
        totais_reforma = etl_db.query(
            func.sum(NFeItem.valor_ibs).label('ibs'),
            func.sum(NFeItem.valor_cbs).label('cbs'),
            func.avg(NFeItem.aliquota_ibs).label('aliq_ibs'),
            func.avg(NFeItem.aliquota_cbs).label('aliq_cbs')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).first()
        
        total_ibs = float(totais_reforma.ibs or 0)
        total_cbs = float(totais_reforma.cbs or 0)
        total_reforma = total_ibs + total_cbs
        aliquota_media_ibs = float(totais_reforma.aliq_ibs or 0)
        aliquota_media_cbs = float(totais_reforma.aliq_cbs or 0)
        
        # Documentos com campos da reforma preenchidos
        docs_com_reforma = etl_db.query(func.count(func.distinct(NFeItem.nfe_id))).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFeItem.valor_ibs.isnot(None)
            )
        ).scalar() or 0
        
        # Total de PIS + COFINS para comparação
        totais_antigos = etl_db.query(
            func.sum(NFeItem.valor_pis).label('pis'),
            func.sum(NFeItem.valor_cofins).label('cofins')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            NFe.emitente_cnpj == cnpj_filtro
        ).first()
        
        total_pis_cofins = float((totais_antigos.pis or 0) + (totais_antigos.cofins or 0))
        
        # Variação percentual
        variacao = 0
        if total_pis_cofins > 0:
            variacao = ((total_reforma - total_pis_cofins) / total_pis_cofins) * 100
        
        # Top produtos com maior impacto da reforma
        top_produtos = etl_db.query(
            NFeItem.descricao.label('produto'),
            func.count(NFeItem.id).label('quantidade'),
            func.sum(NFeItem.valor_ibs).label('ibs'),
            func.sum(NFeItem.valor_cbs).label('cbs')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFeItem.valor_ibs.isnot(None)
            )
        ).group_by(
            NFeItem.descricao
        ).order_by(
            (func.sum(NFeItem.valor_ibs) + func.sum(NFeItem.valor_cbs)).desc()
        ).limit(10).all()
        
        produtos_list = []
        for prod in top_produtos:
            valor_ibs = float(prod.ibs or 0)
            valor_cbs = float(prod.cbs or 0)
            produtos_list.append({
                "produto": prod.produto or "Sem descrição",
                "quantidade": prod.quantidade,
                "valor_ibs": round(valor_ibs, 2),
                "valor_cbs": round(valor_cbs, 2),
                "total": round(valor_ibs + valor_cbs, 2)
            })
        
        # Distribuição por situação tributária
        situacoes = etl_db.query(
            NFeItem.situacao_tributaria_ibscbs.label('situacao'),
            func.count(NFeItem.id).label('quantidade')
        ).join(
            NFe, NFe.id == NFeItem.nfe_id
        ).filter(
            and_(
                NFe.emitente_cnpj == cnpj_filtro,
                NFeItem.situacao_tributaria_ibscbs.isnot(None)
            )
        ).group_by(
            NFeItem.situacao_tributaria_ibscbs
        ).all()
        
        situacoes_dict = {}
        for sit in situacoes:
            situacoes_dict[sit.situacao or 'Não informada'] = sit.quantidade
        
        # Insights automáticos
        insights = []
        
        if variacao > 0:
            insights.append(f"⚠️ A nova tributação (IBS + CBS) representa um aumento de {round(variacao, 2)}% em relação ao sistema anterior (PIS + COFINS)")
        elif variacao < 0:
            insights.append(f"✅ A nova tributação (IBS + CBS) representa uma redução de {abs(round(variacao, 2))}% em relação ao sistema anterior (PIS + COFINS)")
        else:
            insights.append("ℹ️ A carga tributária permanece equivalente entre os sistemas antigo e novo")
        
        if docs_com_reforma > 0:
            percentual_docs = (docs_com_reforma / total_docs) * 100
            insights.append(f"📊 {docs_com_reforma} documentos ({round(percentual_docs, 1)}%) já contêm informações dos novos tributos IBS e CBS")
        else:
            insights.append("⚠️ Nenhum documento processado contém informações dos novos tributos. A empresa precisa se preparar para a reforma tributária")
        
        if aliquota_media_ibs > 0:
            insights.append(f"📈 Alíquota média efetiva de IBS: {round(aliquota_media_ibs, 4)}%")
        
        if aliquota_media_cbs > 0:
            insights.append(f"📈 Alíquota média efetiva de CBS: {round(aliquota_media_cbs, 4)}%")
        
        if len(produtos_list) > 0:
            top1 = produtos_list[0]
            insights.append(f"🔝 Produto com maior impacto: '{top1['produto']}' com R$ {round(top1['total'], 2)} em novos tributos")
        
        return {
            "total_ibs": round(total_ibs, 2),
            "total_cbs": round(total_cbs, 2),
            "total_reforma": round(total_reforma, 2),
            "aliquota_media_ibs": round(aliquota_media_ibs, 4),
            "aliquota_media_cbs": round(aliquota_media_cbs, 4),
            "docs_com_reforma": docs_com_reforma,
            "total_docs": total_docs,
            "total_pis_cofins": round(total_pis_cofins, 2),
            "variacao": round(variacao, 2),
            "top_produtos": produtos_list,
            "situacoes_tributarias": situacoes_dict,
            "insights": insights
        }
        
    finally:
        etl_db.close()


@app.get("/relatorios-fase1", response_class=HTMLResponse, tags=["Relatórios"])
async def pagina_relatorios_fase1(
    request: Request,
    empresa_id: int = None
):
    """Página de relatórios dos campos da Fase 1."""
    return templates.TemplateResponse("relatorios_fase1.html", {
        "request": request,
        "empresa_id": empresa_id
    })


# ============= API DE USUÁRIOS =============

@app.post("/api/usuarios", response_model=schemas.UsuarioResponse, tags=["Usuários"])
async def criar_usuario(
    usuario: schemas.UsuarioCreate,
    db: Session = Depends(get_db)
):
    """Cria um novo usuário (público - sem autenticação)."""
    # Verificar se email já existe
    db_usuario = crud.obter_usuario_por_email(db, usuario.email)
    if db_usuario:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    return crud.criar_usuario(db, usuario)


@app.get("/api/usuarios", response_model=List[schemas.UsuarioResponse], tags=["Usuários"])
async def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual)
):
    """Lista todos os usuários (requer autenticação)."""
    return crud.listar_usuarios(db, skip=skip, limit=limit)


@app.get("/api/usuarios/{usuario_id}", response_model=schemas.UsuarioResponse, tags=["Usuários"])
async def obter_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual)
):
    """Obtém um usuário por ID (requer autenticação)."""
    db_usuario = crud.obter_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return db_usuario


@app.put("/api/usuarios/{usuario_id}", response_model=schemas.UsuarioResponse, tags=["Usuários"])
async def atualizar_usuario(
    usuario_id: int,
    usuario_update: schemas.UsuarioUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza dados de um usuário."""
    db_usuario = crud.atualizar_usuario(db, usuario_id, usuario_update)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return db_usuario


@app.delete("/api/usuarios/{usuario_id}", tags=["Usuários"])
async def deletar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Deleta um usuário."""
    sucesso = crud.deletar_usuario(db, usuario_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"success": True, "message": "Usuário deletado com sucesso"}


# ============= API DE EMPRESAS =============

@app.post("/api/empresas", response_model=schemas.EmpresaResponse, tags=["Empresas"])
async def criar_empresa(
    empresa: schemas.EmpresaCreate,
    db: Session = Depends(get_db),
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual)
):
    """Cria uma nova empresa (requer autenticação)."""
    # Verificar se CNPJ já existe
    db_empresa = crud.obter_empresa_por_cnpj(db, empresa.cnpj)
    if db_empresa:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
    
    return crud.criar_empresa(db, empresa)


@app.get("/api/empresas", response_model=List[schemas.EmpresaResponse], tags=["Empresas"])
async def listar_empresas(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual)
):
    """Lista todas as empresas (requer autenticação)."""
    return crud.listar_empresas(db, skip=skip, limit=limit)


@app.get("/api/empresas/{empresa_id}", response_model=schemas.EmpresaResponse, tags=["Empresas"])
async def obter_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual)
):
    """Obtém uma empresa por ID (requer autenticação)."""
    db_empresa = crud.obter_empresa(db, empresa_id)
    if not db_empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return db_empresa


@app.put("/api/empresas/{empresa_id}", response_model=schemas.EmpresaResponse, tags=["Empresas"])
async def atualizar_empresa(
    empresa_id: int,
    empresa_update: schemas.EmpresaUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza dados de uma empresa."""
    db_empresa = crud.atualizar_empresa(db, empresa_id, empresa_update)
    if not db_empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return db_empresa


@app.delete("/api/empresas/{empresa_id}", tags=["Empresas"])
async def deletar_empresa(empresa_id: int, db: Session = Depends(get_db)):
    """Deleta uma empresa."""
    sucesso = crud.deletar_empresa(db, empresa_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return {"success": True, "message": "Empresa deletada com sucesso"}


# ============= API DE VÍNCULOS =============

@app.post("/api/vinculos", tags=["Vínculos"])
async def vincular_usuario_empresa(
    vinculo: schemas.VincularEmpresa,
    db: Session = Depends(get_db)
):
    """Vincula um usuário a uma empresa."""
    sucesso = crud.vincular_usuario_empresa(db, vinculo.usuario_id, vinculo.empresa_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Usuário ou empresa não encontrados")
    return {"success": True, "message": "Vínculo criado com sucesso"}


@app.delete("/api/vinculos/{usuario_id}/{empresa_id}", tags=["Vínculos"])
async def desvincular_usuario_empresa(
    usuario_id: int,
    empresa_id: int,
    db: Session = Depends(get_db)
):
    """Desvincula um usuário de uma empresa."""
    sucesso = crud.desvincular_usuario_empresa(db, usuario_id, empresa_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Usuário ou empresa não encontrados")
    return {"success": True, "message": "Vínculo removido com sucesso"}


@app.get("/api/usuarios/{usuario_id}/empresas", response_model=List[schemas.EmpresaResponse], tags=["Vínculos"])
async def listar_empresas_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual)
):
    """Lista empresas vinculadas a um usuário (requer autenticação)."""
    # Usuário só pode ver suas próprias empresas (ou admin pode ver de todos)
    if usuario_atual.id != usuario_id:
        raise HTTPException(
            status_code=403,
            detail="Você só pode ver suas próprias empresas"
        )
    return crud.listar_empresas_usuario(db, usuario_id)


@app.get("/api/empresas/{empresa_id}/usuarios", response_model=List[schemas.UsuarioResponse], tags=["Vínculos"])
async def listar_usuarios_empresa(empresa_id: int, db: Session = Depends(get_db)):
    """Lista usuários vinculados a uma empresa."""
    return crud.listar_usuarios_empresa(db, empresa_id)


# ============= API DE ANÁLISES =============

@app.get("/api/empresas/{empresa_id}/analises", response_model=List[schemas.AnaliseResponse], tags=["Análises"])
async def listar_analises_empresa(
    empresa_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual)
):
    """Lista análises de uma empresa (requer autenticação e acesso à empresa)."""
    # Verificar se usuário tem acesso à empresa
    if not verificar_acesso_empresa(usuario_atual, empresa_id, db):
        raise HTTPException(
            status_code=403,
            detail="Você não tem acesso a esta empresa"
        )
    return crud.listar_analises_empresa(db, empresa_id, skip=skip, limit=limit)


@app.get("/api/analises/{analise_id}", tags=["Análises"])
async def obter_analise(analise_id: int, db: Session = Depends(get_db)):
    """Obtém detalhes de uma análise."""
    db_analise = crud.obter_analise(db, analise_id)
    if not db_analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    
    # Retornar dados completos
    dados = json.loads(db_analise.relatorio_completo)
    dados['id'] = db_analise.id
    dados['periodo'] = db_analise.periodo
    dados['data_processamento'] = db_analise.data_processamento.isoformat()
    
    return dados


@app.delete("/api/analises/{analise_id}", tags=["Análises"])
async def deletar_analise(analise_id: int, db: Session = Depends(get_db)):
    """Deleta uma análise."""
    sucesso = crud.deletar_analise(db, analise_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    return {"success": True, "message": "Análise deletada com sucesso"}


@app.get("/api/export/excel", tags=["Exportação"])
async def exportar_excel(
    analise_id: int = None,
    usuario_atual: db_models.Usuario = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Exporta o relatório para Excel."""
    # Se analise_id foi fornecido, busca do banco
    if analise_id:
        db_analise = crud.obter_analise(db, analise_id)
        if not db_analise:
            raise HTTPException(status_code=404, detail="Análise não encontrada")
        
        # Verificar acesso à empresa
        if not any(e.id == db_analise.empresa_id for e in usuario_atual.empresas):
            raise HTTPException(status_code=403, detail="Acesso negado a esta análise")
        
        # Carregar dados do banco
        dados_relatorio = json.loads(db_analise.relatorio_completo)
        periodo = db_analise.periodo
    else:
        # Usar dados da sessão atual
        if not dados_sessao["documentos"]:
            raise HTTPException(status_code=400, detail="Nenhum documento processado")
        
        dados_relatorio = {
            "mapa": dados_sessao["mapa"],
            "documentos": dados_sessao["documentos"],
            "validacoes": dados_sessao["validacoes"],
            "empresa": {}
        }
        periodo = dados_sessao["mapa"].periodo if dados_sessao["mapa"] else "Período não definido"
    
    # Gerar Excel
    exportador = ExportadorRelatorios()
    arquivo_excel = exportador.gerar_excel(dados_relatorio)
    
    # Retornar arquivo
    return StreamingResponse(
        arquivo_excel,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=relatorio_fiscal_{periodo.replace('/', '_')}.xlsx"}
    )


@app.get("/api/export/pdf", tags=["Exportação"])
async def exportar_pdf(
    analise_id: int = None,
    usuario_atual: db_models.Usuario = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Exporta o relatório para PDF."""
    # Se analise_id foi fornecido, busca do banco
    if analise_id:
        db_analise = crud.obter_analise(db, analise_id)
        if not db_analise:
            raise HTTPException(status_code=404, detail="Análise não encontrada")
        
        # Verificar acesso à empresa
        if not any(e.id == db_analise.empresa_id for e in usuario_atual.empresas):
            raise HTTPException(status_code=403, detail="Acesso negado a esta análise")
        
        # Carregar dados do banco
        dados_relatorio = json.loads(db_analise.relatorio_completo)
        periodo = db_analise.periodo
    else:
        # Usar dados da sessão atual
        if not dados_sessao["documentos"]:
            raise HTTPException(status_code=400, detail="Nenhum documento processado")
        
        dados_relatorio = {
            "mapa": dados_sessao["mapa"],
            "documentos": dados_sessao["documentos"],
            "validacoes": dados_sessao["validacoes"],
            "empresa": {}
        }
        periodo = dados_sessao["mapa"].periodo if dados_sessao["mapa"] else "Período não definido"
    
    # Gerar PDF
    exportador = ExportadorRelatorios()
    arquivo_pdf = exportador.gerar_pdf(dados_relatorio)
    
    # Retornar arquivo
    return StreamingResponse(
        arquivo_pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=relatorio_fiscal_{periodo.replace('/', '_')}.pdf"}
    )


if __name__ == "__main__":
    import uvicorn
    print("=" * 80)
    print("FISCAL AUDITOR - Aplicação Web")
    print("=" * 80)
    print()
    print("Servidor iniciando em: http://localhost:8000")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
