#!/usr/bin/env python
"""
Aplicação Web do Fiscal Auditor.
Interface web para upload de XMLs e visualização de relatórios tributários.
"""
from fastapi import FastAPI, UploadFile, File, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
import os
import tempfile
import shutil
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


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

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
    """Página inicial - painel ou upload dependendo do empresa_id."""
    if empresa_id:
        # Se tem empresa_id, mostrar página de upload
        return templates.TemplateResponse("index.html", {
            "request": request,
            "empresa_id": empresa_id
        })
    else:
        # Se não tem empresa_id, mostrar painel de seleção
        return templates.TemplateResponse("painel.html", {"request": request})


@app.post("/upload")
async def upload_xmls(
    request: Request,
    empresa_id: int = Form(...),
    tipo_data: str = Form(...),
    data_inicio: str = Form(...),
    data_fim: str = Form(...),
    arquivos: List[UploadFile] = File(...),
    usuario_atual: schemas.UsuarioResponse = Depends(obter_usuario_atual),
    db: Session = Depends(get_db)
):
    """Processa os arquivos XML enviados."""
    try:
        # Verificar acesso à empresa
        if not verificar_acesso_empresa(usuario_atual, empresa_id, db):
            raise HTTPException(status_code=403, detail="Você não tem acesso a esta empresa")
        
        # Buscar empresa
        empresa = crud.obter_empresa(db, empresa_id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        
        # Converter datas
        from datetime import datetime
        data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
        data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
        
        # Limpar dados anteriores
        dados_sessao["documentos"] = []
        dados_sessao["validacoes"] = []
        dados_sessao["mapa"] = None
        dados_sessao["relatorios"] = {}
        dados_sessao["empresa_id"] = empresa_id
        dados_sessao["filtro_data_tipo"] = tipo_data
        dados_sessao["filtro_data_inicio"] = data_inicio
        dados_sessao["filtro_data_fim"] = data_fim
        
        # Inicializar componentes
        cnpj_limpo = empresa.cnpj.replace(".", "").replace("/", "").replace("-", "")
        reader = XMLReader(cnpj_limpo)
        validador = ValidadorTributario()
        apurador = ApuradorTributario()
        gerador = GeradorRelatorios()
        
        documentos = []
        validacoes = []
        erros = []
        documentos_filtrados = 0
        
        # Processar cada arquivo
        for arquivo in arquivos:
            if not arquivo.filename.endswith('.xml'):
                erros.append(f"{arquivo.filename}: Não é um arquivo XML")
                continue
            
            try:
                # Salvar temporariamente
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp:
                    conteudo = await arquivo.read()
                    tmp.write(conteudo)
                    tmp_path = tmp.name
                
                # Processar XML
                doc = reader.ler_xml(tmp_path)
                
                # Aplicar filtro de data
                data_documento = None
                if tipo_data == "emissao":
                    data_documento = doc.data_emissao
                elif tipo_data == "autorizacao" and hasattr(doc, 'data_autorizacao'):
                    data_documento = doc.data_autorizacao or doc.data_emissao
                else:
                    data_documento = doc.data_emissao
                
                # Verificar se está no período
                if data_documento:
                    if data_inicio_dt.date() <= data_documento.date() <= data_fim_dt.date():
                        documentos.append(doc)
                        
                        # Validar
                        validacao = validador.validar_documento(doc)
                        validacoes.append(validacao)
                        
                        # Adicionar para apuração
                        apurador.adicionar_documento(doc)
                    else:
                        documentos_filtrados += 1
                
                # Remover arquivo temporário
                os.unlink(tmp_path)
                
            except Exception as e:
                erros.append(f"{arquivo.filename}: {str(e)}")
        
        if not documentos:
            mensagem = "Nenhum documento válido foi encontrado"
            if documentos_filtrados > 0:
                mensagem += f". {documentos_filtrados} documento(s) fora do período selecionado"
            return JSONResponse({
                "success": False,
                "message": "Nenhum documento foi processado com sucesso",
                "erros": erros
            }, status_code=400)
        
        # Calcular período automaticamente baseado nos documentos
        datas = [doc.data_emissao for doc in documentos if doc.data_emissao]
        if datas:
            data_mais_antiga = min(datas)
            periodo = f"{data_mais_antiga.month:02d}/{data_mais_antiga.year}"
        else:
            periodo = f"{data_inicio_dt.month:02d}/{data_inicio_dt.year}"
        
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
        
        mensagem = f"{len(documentos)} documento(s) processado(s) com sucesso"
        if documentos_filtrados > 0:
            mensagem += f" ({documentos_filtrados} documento(s) filtrado(s) por data)"
        
        return JSONResponse({
            "success": True,
            "message": mensagem,
            "total_documentos": len(documentos),
            "documentos_filtrados": documentos_filtrados,
            "periodo": periodo,
            "erros": erros if erros else None
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Erro ao processar: {str(e)}"
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
    return FileResponse(
        arquivo_excel,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"relatorio_fiscal_{periodo.replace('/', '_')}.xlsx",
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
    return FileResponse(
        arquivo_pdf,
        media_type="application/pdf",
        filename=f"relatorio_fiscal_{periodo.replace('/', '_')}.pdf",
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
