@echo off
REM Script para ejecutar pruebas en Windows
REM SOLUCION: Usar 'tests' en lugar de 'test'

REM Configurar codificacion UTF-8 para Windows
chcp 65001 > nul

REM Establecer variable de entorno para pruebas
set DATABASE_URL=sqlite:///:memory:

echo ========================================
echo ELECTRIC CARS DATABASE - TEST SUITE
echo ========================================
echo.

REM Verificar dependencias criticas
echo Verificando dependencias...
python -c "import sqlalchemy" 2>nul
if errorlevel 1 (
    echo [ERROR] SQLAlchemy no esta instalado
    echo.
    echo Por favor ejecuta primero:
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

python -c "import pytest" 2>nul
if errorlevel 1 (
    echo [ERROR] pytest no esta instalado
    echo Instalando dependencias de testing...
    pip install pytest pytest-cov httpx
    echo.
)

REM Verificar que existe el directorio tests (CON 'S')
if not exist "tests" (
    echo [ERROR] No se encuentra el directorio 'tests'
    echo Asegurate de estar en el directorio raiz del proyecto
    pause
    exit /b 1
)

REM Crear directorios necesarios
if not exist "htmlcov" mkdir htmlcov
if not exist "test-results" mkdir test-results

REM Procesar el comando
set "cmd=%~1"
if "%cmd%"=="" set "cmd=all"

if "%cmd%"=="all" goto run_all
if "%cmd%"=="auth" goto run_auth
if "%cmd%"=="crud" goto run_crud
if "%cmd%"=="fast" goto run_fast
if "%cmd%"=="coverage" goto show_coverage
if "%cmd%"=="stats" goto show_stats
if "%cmd%"=="clean" goto clean_files
if "%cmd%"=="check" goto check_deps
if "%cmd%"=="help" goto show_help

echo [ERROR] Comando no reconocido: %cmd%
goto show_help

:check_deps
echo Verificando todas las dependencias...
echo.
python check_dependencies.py
goto end

:run_all
echo Ejecutando todas las pruebas...
echo.
python -m pytest tests/ -v
if errorlevel 1 (
    echo.
    echo [ERROR] Algunas pruebas fallaron
    exit /b 1
) else (
    echo.
    echo [OK] PRUEBAS COMPLETADAS EXITOSAMENTE
)
goto end

:run_auth
echo Ejecutando pruebas de autenticacion...
echo.
python -m pytest tests/test_auth.py -v --tb=short
goto end

:run_crud
echo Ejecutando pruebas CRUD...
echo.
python -m pytest tests/test_crud.py -v --tb=short
goto end

:run_fast
echo Ejecutando pruebas rapidas...
echo.
python -m pytest tests/ -m "not slow" -v
goto end

:show_coverage
echo Ejecutando pruebas con cobertura...
echo.
python -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
if exist "htmlcov\index.html" (
    echo.
    echo Abriendo reporte de cobertura...
    start htmlcov\index.html
) else (
    echo [ERROR] No se encuentra el reporte de cobertura
)
goto end

:show_stats
echo Mostrando estadisticas de pruebas...
echo.
python -m pytest tests/ --collect-only -q
goto end

:clean_files
echo Limpiando archivos de prueba...
echo.
if exist ".pytest_cache" rmdir /s /q .pytest_cache
if exist "htmlcov" rmdir /s /q htmlcov
if exist "test-results" rmdir /s /q test-results
if exist ".coverage" del /f /q .coverage
if exist "test.db" del /f /q test.db
if exist "test_crud.db" del /f /q test_crud.db
if exist "test_local.db" del /f /q test_local.db
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo [OK] Archivos de prueba limpiados
goto end

:show_help
echo Uso: run_test.bat [comando]
echo.
echo Comandos disponibles:
echo   all       - Ejecutar todas las pruebas (por defecto)
echo   auth      - Ejecutar solo pruebas de autenticacion
echo   crud      - Ejecutar solo pruebas CRUD
echo   fast      - Ejecutar solo pruebas rapidas
echo   coverage  - Ejecutar con reporte de cobertura HTML
echo   stats     - Mostrar estadisticas de pruebas
echo   check     - Verificar dependencias instaladas
echo   clean     - Limpiar archivos de prueba
echo   help      - Mostrar esta ayuda
echo.
echo Ejemplos:
echo   run_test.bat all
echo   run_test.bat auth
echo   run_test.bat coverage
echo   run_test.bat check
goto end

:end
echo.
pause