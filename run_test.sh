#!/bin/bash

# Script para ejecutar las pruebas de Electric Cars Database
# Uso: ./run_tests.sh [opciones]

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ELECTRIC CARS DATABASE - TEST SUITE${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Verificar que pytest esté instalado
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest no está instalado${NC}"
    echo -e "${YELLOW}Instalando dependencias de testing...${NC}"
    pip install -r requirements-test.txt
fi

# Crear directorios necesarios si no existen
mkdir -p htmlcov
mkdir -p test-results

# Función para ejecutar todas las pruebas
run_all_tests() {
    echo -e "${YELLOW}📋 Ejecutando todas las pruebas...${NC}\n"
    pytest test/ \
        --verbose \
        --cov=. \
        --cov-report=html \
        --cov-report=term-missing \
        --html=test-results/report.html \
        --self-contained-html
}

# Función para ejecutar solo pruebas de autenticación
run_auth_tests() {
    echo -e "${YELLOW}🔐 Ejecutando pruebas de autenticación...${NC}\n"
    pytest test/test_auth.py -v --tb=short
}

# Función para ejecutar solo pruebas CRUD
run_crud_tests() {
    echo -e "${YELLOW}📝 Ejecutando pruebas CRUD...${NC}\n"
    pytest test/test_crud.py -v --tb=short
}

# Función para ejecutar pruebas con marcador específico
run_marked_tests() {
    local marker=$1
    echo -e "${YELLOW}🏷️  Ejecutando pruebas marcadas como '${marker}'...${NC}\n"
    pytest test/ -m "${marker}" -v
}

# Función para ejecutar pruebas rápidas (excluyendo lentas)
run_fast_tests() {
    echo -e "${YELLOW}⚡ Ejecutando pruebas rápidas...${NC}\n"
    pytest test/ -m "not slow" -v
}

# Función para ver reporte de cobertura
show_coverage() {
    echo -e "${YELLOW}📊 Abriendo reporte de cobertura...${NC}\n"
    if [ -f "htmlcov/index.html" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open htmlcov/index.html
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            xdg-open htmlcov/index.html
        else
            echo -e "${YELLOW}Abre manualmente: htmlcov/index.html${NC}"
        fi
    else
        echo -e "${RED}❌ No se encuentra el reporte de cobertura${NC}"
        echo -e "${YELLOW}Ejecuta primero las pruebas con: ./run_tests.sh all${NC}"
    fi
}

# Función para limpiar archivos de prueba
clean_test_files() {
    echo -e "${YELLOW}🧹 Limpiando archivos de prueba...${NC}\n"
    rm -rf .pytest_cache
    rm -rf htmlcov
    rm -rf test-results
    rm -f .coverage
    rm -f test.db test_crud.db
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
    echo -e "${GREEN}✅ Archivos de prueba limpiados${NC}"
}

# Función para mostrar estadísticas
show_stats() {
    echo -e "${YELLOW}📈 Mostrando estadísticas de pruebas...${NC}\n"
    pytest test/ --collect-only -q
}

# Función para mostrar ayuda
show_help() {
    echo -e "${GREEN}Uso: ./run_tests.sh [comando]${NC}\n"
    echo "Comandos disponibles:"
    echo "  all       - Ejecutar todas las pruebas con reporte de cobertura (por defecto)"
    echo "  auth      - Ejecutar solo pruebas de autenticación"
    echo "  crud      - Ejecutar solo pruebas CRUD"
    echo "  fast      - Ejecutar solo pruebas rápidas (excluye lentas)"
    echo "  mark      - Ejecutar pruebas con marcador específico"
    echo "  coverage  - Abrir reporte de cobertura HTML"
    echo "  stats     - Mostrar estadísticas de pruebas"
    echo "  clean     - Limpiar archivos de prueba"
    echo "  help      - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  ./run_tests.sh all"
    echo "  ./run_tests.sh auth"
    echo "  ./run_tests.sh mark crud"
}

# Procesar argumentos
case "${1:-all}" in
    all)
        run_all_tests
        ;;
    auth)
        run_auth_tests
        ;;
    crud)
        run_crud_tests
        ;;
    fast)
        run_fast_tests
        ;;
    mark)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Debes especificar un marcador${NC}"
            echo "Ejemplo: ./run_tests.sh mark auth"
            exit 1
        fi
        run_marked_tests "$2"
        ;;
    coverage)
        show_coverage
        ;;
    stats)
        show_stats
        ;;
    clean)
        clean_test_files
        ;;
    help)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Comando no reconocido: $1${NC}"
        show_help
        exit 1
        ;;
esac

# Verificar el resultado
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ PRUEBAS COMPLETADAS EXITOSAMENTE${NC}"
    echo -e "${YELLOW}📊 Para ver el reporte de cobertura: ./run_tests.sh coverage${NC}"
else
    echo -e "\n${RED}❌ ALGUNAS PRUEBAS FALLARON${NC}"
    exit 1
fi