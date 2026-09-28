@echo off
cls

:MENU
cls
echo =======================================================================
echo              MENU DE INICIALIZACAO - AUTOMACAO RH
echo =======================================================================
echo.
echo [1] Iniciar Backend e Frontend (Janelas separadas)
echo [2] Iniciar apenas o Backend (FastAPI)
echo [3] Iniciar apenas o Frontend (React + Vite)
echo [4] Instalar/Atualizar Dependencias (Pip & Npm)
echo [5] Executar Migracoes do Banco de Dados (Alembic)
echo [6] Sair
echo.
echo =======================================================================
set /p opcao="Escolha uma opcao (1-6): "

if "%opcao%"=="1" goto AMBOS
if "%opcao%"=="2" goto BACKEND
if "%opcao%"=="3" goto FRONTEND
if "%opcao%"=="4" goto DEPENDENCIAS
if "%opcao%"=="5" goto MIGRACOES
if "%opcao%"=="6" goto SAIR

echo Opcao invalida! Tente novamente...
timeout /t 2 > nul
goto MENU

:AMBOS
echo.
echo Iniciando Backend e Frontend em janelas separadas...
start "Backend - FastAPI" cmd /k "cd backend && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
start "Frontend - React Vite" cmd /k "cd frontend && npm run dev"
goto FIM

:BACKEND
echo.
echo Iniciando Backend...
start "Backend - FastAPI" cmd /k "cd backend && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
goto FIM

:FRONTEND
echo.
echo Iniciando Frontend...
start "Frontend - React Vite" cmd /k "cd frontend && npm run dev"
goto FIM

:DEPENDENCIAS
echo.
echo Instalar/Atualizar Dependencias...
echo.
echo [1/2] Configurando Backend (Python venv)...
cd backend
if not exist venv (
    echo Criando ambiente virtual venv...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Instalando dependencias do backend...
pip install -r requirements.txt
cd ..

echo.
echo [2/2] Configurando Frontend (Npm)...
cd frontend
echo Instalando dependencias do frontend...
call npm install
cd ..

echo.
echo Dependencias instaladas com sucesso!
pause
goto MENU

:MIGRACOES
echo.
echo Executando migracoes do banco de dados (Alembic)...
cd backend
call venv\Scripts\activate.bat
alembic upgrade head
cd ..
echo.
echo Migracoes concluidas!
pause
goto MENU

:FIM
echo.
echo Pronto! Os processos foram iniciados em janelas separadas.
timeout /t 3 > nul
exit

:SAIR
exit
