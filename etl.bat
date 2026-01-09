@echo off
REM ============================================================================
REM Script de Execução Rápida do Serviço ETL
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                    SERVICO ETL - DOCUMENTOS FISCAIS                      ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python não está instalado ou não está no PATH
    echo Por favor, instale o Python 3.8 ou superior
    pause
    exit /b 1
)

REM Menu principal
:MENU
echo.
echo Escolha uma opção:
echo.
echo 1. Configurar e Inicializar (primeira vez)
echo 2. Processar diretório de XMLs
echo 3. Processar arquivos específicos
echo 4. Ver exemplos de uso
echo 5. Verificar status do banco
echo 6. Sair
echo.
set /p OPCAO="Digite o número da opção: "

if "%OPCAO%"=="1" goto CONFIG
if "%OPCAO%"=="2" goto PROCESSAR_DIR
if "%OPCAO%"=="3" goto PROCESSAR_ARQUIVOS
if "%OPCAO%"=="4" goto EXEMPLOS
if "%OPCAO%"=="5" goto STATUS
if "%OPCAO%"=="6" goto SAIR

echo Opção inválida!
goto MENU

REM ============================================================================
REM Configuração e Inicialização
REM ============================================================================
:CONFIG
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo CONFIGURAÇÃO E INICIALIZAÇÃO
echo ═══════════════════════════════════════════════════════════════════════════
echo.

echo Executando configuração inicial...
python setup_etl.py

if errorlevel 1 (
    echo.
    echo [ERRO] Falha na configuração
    pause
    goto MENU
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo Configuração concluída!
echo ═══════════════════════════════════════════════════════════════════════════
pause
goto MENU

REM ============================================================================
REM Processar Diretório
REM ============================================================================
:PROCESSAR_DIR
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo PROCESSAR DIRETÓRIO DE XMLs
echo ═══════════════════════════════════════════════════════════════════════════
echo.

set /p DIR_XML="Digite o caminho do diretório com XMLs: "

if not exist "%DIR_XML%" (
    echo.
    echo [ERRO] Diretório não encontrado: %DIR_XML%
    pause
    goto MENU
)

echo.
echo Deseja processar subdiretórios também? (S/N)
set /p RECURSIVO="Resposta: "

if /i "%RECURSIVO%"=="N" (
    echo.
    echo Processando diretório (sem recursão)...
    python run_etl.py --diretorio "%DIR_XML%" --no-recursivo
) else (
    echo.
    echo Processando diretório (com recursão)...
    python run_etl.py --diretorio "%DIR_XML%"
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo Processamento concluído!
echo ═══════════════════════════════════════════════════════════════════════════
pause
goto MENU

REM ============================================================================
REM Processar Arquivos Específicos
REM ============================================================================
:PROCESSAR_ARQUIVOS
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo PROCESSAR ARQUIVOS ESPECÍFICOS
echo ═══════════════════════════════════════════════════════════════════════════
echo.

set /p ARQUIVO1="Digite o caminho do primeiro arquivo XML: "

if not exist "%ARQUIVO1%" (
    echo.
    echo [ERRO] Arquivo não encontrado: %ARQUIVO1%
    pause
    goto MENU
)

echo.
echo Deseja adicionar mais arquivos? (S/N)
set /p MAIS="Resposta: "

if /i "%MAIS%"=="S" (
    set /p ARQUIVO2="Digite o caminho do segundo arquivo XML: "
    set /p ARQUIVO3="Digite o caminho do terceiro arquivo XML (deixe vazio para pular): "
    
    if not "%ARQUIVO3%"=="" (
        python run_etl.py --arquivos "%ARQUIVO1%" "%ARQUIVO2%" "%ARQUIVO3%"
    ) else (
        python run_etl.py --arquivos "%ARQUIVO1%" "%ARQUIVO2%"
    )
) else (
    python run_etl.py --arquivos "%ARQUIVO1%"
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo Processamento concluído!
echo ═══════════════════════════════════════════════════════════════════════════
pause
goto MENU

REM ============================================================================
REM Exemplos
REM ============================================================================
:EXEMPLOS
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo EXEMPLOS DE USO
echo ═══════════════════════════════════════════════════════════════════════════
echo.

python exemplo_etl.py

pause
goto MENU

REM ============================================================================
REM Status do Banco
REM ============================================================================
:STATUS
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo STATUS DO BANCO DE DADOS
echo ═══════════════════════════════════════════════════════════════════════════
echo.

python -c "from etl_service.database import SessionLocal; from etl_service.models import NFe; session = SessionLocal(); total = session.query(NFe).count(); print(f'Total de NF-es no banco: {total:,}'); session.close()"

if errorlevel 1 (
    echo.
    echo [ERRO] Não foi possível conectar ao banco de dados
    echo Verifique se o banco está rodando e configurado corretamente
) else (
    echo.
    echo Consulte mais informações em: etl_service/consultas_uteis.sql
)

pause
goto MENU

REM ============================================================================
REM Sair
REM ============================================================================
:SAIR
echo.
echo Encerrando...
echo.
exit /b 0
