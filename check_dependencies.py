#!/usr/bin/env python
"""
Script para verificar que todas las dependencias necesarias están instaladas
"""

import sys

# Colores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def check_module(module_name, package_name=None):
    """Verifica si un módulo está instalado"""
    if package_name is None:
        package_name = module_name

    try:
        __import__(module_name)
        print(f"{GREEN}✅ {package_name}{RESET}")
        return True
    except ImportError:
        print(f"{RED}❌ {package_name} - NO INSTALADO{RESET}")
        return False


def main():
    print(f"\n{BLUE}{'=' * 70}")
    print("VERIFICACIÓN DE DEPENDENCIAS - ELECTRIC CARS DATABASE")
    print(f"{'=' * 70}{RESET}\n")

    dependencies = {
        # Módulo a importar: Nombre del paquete
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'jinja2': 'Jinja2',
        'sqlalchemy': 'SQLAlchemy',
        'dotenv': 'python-dotenv',
        'pandas': 'pandas',
        'multipart': 'python-multipart',
        'loguru': 'loguru',
        'werkzeug': 'Werkzeug',
        'jose': 'python-jose[cryptography]',
        'pytest': 'pytest',
        'pytest_cov': 'pytest-cov',
        'httpx': 'httpx',
    }

    print(f"{YELLOW}Dependencias Principales:{RESET}")
    main_deps = ['fastapi', 'uvicorn', 'jinja2', 'sqlalchemy', 'dotenv',
                 'pandas', 'multipart', 'loguru', 'werkzeug', 'jose']

    main_ok = all(check_module(mod, dependencies[mod]) for mod in main_deps)

    print(f"\n{YELLOW}Driver de PostgreSQL:{RESET}")
    psycopg3_ok = check_module('psycopg', 'psycopg[binary]')
    psycopg2_ok = check_module('psycopg2', 'psycopg2-binary')

    if not psycopg3_ok and not psycopg2_ok:
        print(f"{RED}⚠️  Necesitas instalar UN driver de PostgreSQL{RESET}")

    print(f"\n{YELLOW}Dependencias de Testing:{RESET}")
    test_deps = ['pytest', 'pytest_cov', 'httpx']
    test_ok = all(check_module(mod, dependencies[mod]) for mod in test_deps)

    # Resumen
    print(f"\n{BLUE}{'=' * 70}")
    print("RESUMEN")
    print(f"{'=' * 70}{RESET}\n")

    if main_ok and (psycopg3_ok or psycopg2_ok) and test_ok:
        print(f"{GREEN}✅ Todas las dependencias están instaladas correctamente{RESET}")
        print(f"\n{GREEN}Puedes ejecutar los tests con:{RESET}")
        print(f"  {YELLOW}run_tests.bat all{RESET}")
        print(f"  {YELLOW}python -m pytest test/ -v{RESET}")
        return 0
    else:
        print(f"{RED}❌ Faltan dependencias por instalar{RESET}")
        print(f"\n{YELLOW}Para instalar todas las dependencias:{RESET}")
        print(f"  {BLUE}pip install -r requirements-dev-windows.txt{RESET}")
        print(f"\n{YELLOW}O instala las mínimas necesarias:{RESET}")
        print(f"  {BLUE}pip install sqlalchemy fastapi uvicorn jinja2 python-dotenv pandas{RESET}")
        print(f"  {BLUE}pip install python-multipart werkzeug python-jose[cryptography] loguru{RESET}")
        print(f"  {BLUE}pip install pytest pytest-cov httpx{RESET}")
        print(f"  {BLUE}pip install \"psycopg[binary]\"{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())