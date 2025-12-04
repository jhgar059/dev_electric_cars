@echo off
REM Script para ejecutar pruebas en Windows
REM Uso: run_tests.bat [comando]

echo ========================================
echo ELECTRIC CARS DATABASE - TEST SUITE
echo ========================================
echo.

REM Verificar si pytest está instalado
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pytest no esta instalado
    echo Instalando dependencias de testing...
    pip install pytest pytest-cov pytest-html httpx
    echo.
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
if "%cmd%"=="help" goto show_help

echo [ERROR] Comando no reconocido: %cmd%
goto show_help

:run_all
echo Ejecutando todas las pruebas...
echo.
python -m pytest test/ -v
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
python -m pytest test/test_auth.py -v --tb=short
goto end

:run_crud
echo Ejecutando pruebas CRUD...
echo.
python -m pytest test/test_crud.py -v --tb=short
goto end

:run_fast
echo Ejecutando pruebas rapidas...
echo.
python -m pytest test/ -m "not slow" -v
goto end

:show_coverage
echo Ejecutando pruebas con cobertura...
echo.
python -m pytest test/ -v --cov=. --cov-report=html --cov-report=term-missing
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
python -m pytest test/ --collect-only -q
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
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo [OK] Archivos de prueba limpiados
goto end

:show_help
echo Uso: run_tests.bat [comando]
echo.
echo Comandos disponibles:
echo   all       - Ejecutar todas las pruebas (por defecto)
echo   auth      - Ejecutar solo pruebas de autenticacion
echo   crud      - Ejecutar solo pruebas CRUD
echo   fast      - Ejecutar solo pruebas rapidas
echo   coverage  - Ejecutar con reporte de cobertura HTML
echo   stats     - Mostrar estadisticas de pruebas
echo   clean     - Limpiar archivos de prueba
echo   help      - Mostrar esta ayuda
echo.
echo Ejemplos:
echo   run_tests.bat all
echo   run_tests.bat auth
echo   run_tests.bat coverage
goto end

:end
echo.
pause