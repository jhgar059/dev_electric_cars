# 🧪 Suite de Pruebas - Electric Cars Database

Este directorio contiene todas las pruebas automatizadas del proyecto Electric Cars Database.

## 📋 Tabla de Contenidos

- [Estructura](#estructura)
- [Instalación](#instalación)
- [Ejecución de Pruebas](#ejecución-de-pruebas)
- [Tipos de Pruebas](#tipos-de-pruebas)
- [Cobertura de Código](#cobertura-de-código)
- [Convenciones](#convenciones)
- [CI/CD](#cicd)

## 📁 Estructura

```
test/
├── __init__.py
├── README.md
├── conftest.py              # Configuración compartida y fixtures
├── test_auth.py             # Pruebas de autenticación
├── test_crud.py             # Pruebas de operaciones CRUD
└── test_integration.py      # Pruebas de integración (opcional)
```

## 🔧 Instalación

### 1. Instalar dependencias de testing

```bash
pip install -r requirements-test.txt
```

### 2. Verificar instalación

```bash
pytest --version
```

## 🚀 Ejecución de Pruebas

### Ejecutar todas las pruebas

```bash
# Usando el script
./run_tests.sh all

# O directamente con pytest
pytest test/ -v
```

### Ejecutar pruebas específicas

```bash
# Solo pruebas de autenticación
./run_tests.sh auth

# Solo pruebas CRUD
./run_tests.sh crud

# Por archivo específico
pytest test/test_auth.py -v

# Por clase específica
pytest test/test_auth.py::TestRegistro -v

# Por función específica
pytest test/test_auth.py::TestRegistro::test_registro_exitoso -v
```

### Ejecutar con marcadores

```bash
# Solo pruebas marcadas como 'auth'
pytest test/ -m auth -v

# Excluir pruebas lentas
pytest test/ -m "not slow" -v

# Múltiples marcadores
pytest test/ -m "auth and not slow" -v
```

### Opciones útiles

```bash
# Detener en el primer fallo
pytest test/ -x

# Mostrar variables locales en fallos
pytest test/ -l

# Modo verbose con output completo
pytest test/ -vv -s

# Ejecutar pruebas en paralelo (requiere pytest-xdist)
pytest test/ -n auto

# Repetir pruebas 3 veces
pytest test/ --count=3
```

## 📊 Cobertura de Código

### Generar reporte de cobertura

```bash
# HTML (recomendado)
pytest test/ --cov=. --cov-report=html
./run_tests.sh coverage  # Para abrir el reporte

# Terminal
pytest test/ --cov=. --cov-report=term-missing

# XML (para CI/CD)
pytest test/ --cov=. --cov-report=xml
```

### Ver cobertura actual

El objetivo es mantener una cobertura mínima del **80%**.

```bash
pytest test/ --cov=. --cov-report=term
```

## 🧩 Tipos de Pruebas

### 1. Pruebas de Autenticación (`test_auth.py`)

Cubren:
- ✅ Registro de usuarios
- ✅ Inicio de sesión (con cédula y correo)
- ✅ Cambio de contraseña
- ✅ Cierre de sesión
- ✅ Validaciones de contraseña
- ✅ Manejo de usuarios duplicados
- ✅ Protección de rutas

**Ejemplo:**
```python
def test_registro_exitoso(self, test_db):
    """Test: Registro exitoso de un nuevo usuario"""
    response = client.post("/register", data={...})
    assert response.status_code == 302
```

### 2. Pruebas CRUD (`test_crud.py`)

Cubren operaciones para:
- 🚗 **Autos**: Create, Read, Update, Delete
- ⚡ **Cargas**: Create, Read, Update, Delete
- 🔌 **Estaciones**: Create, Read, Update, Delete
- 📊 **Estadísticas**: Autos por marca, potencia por conector, etc.

**Ejemplo:**
```python
def test_crear_auto_exitoso(self, test_db, auto_test_data):
    """Test: Crear un auto eléctrico exitosamente"""
    response = client.post("/api/autos", json=auto_test_data)
    assert response.status_code == 201
```

### 3. Fixtures Disponibles

En `conftest.py`:

```python
# Fixtures de base de datos
@pytest.fixture
def test_db():
    """Base de datos limpia para cada test"""

@pytest.fixture
def test_user(test_db):
    """Usuario de prueba pre-creado"""

# Fixtures de datos
@pytest.fixture
def auto_test_data():
    """Datos de prueba para auto"""

@pytest.fixture
def carga_test_data():
    """Datos de prueba para carga"""

@pytest.fixture
def estacion_test_data():
    """Datos de prueba para estación"""
```

## 📝 Convenciones

### Nomenclatura

- **Archivos**: `test_*.py`
- **Clases**: `Test*` (ej: `TestRegistro`, `TestAutosCreate`)
- **Funciones**: `test_*` (ej: `test_registro_exitoso`)

### Estructura de un Test

```python
def test_nombre_descriptivo(self, fixtures_necesarias):
    """
    Test: Descripción clara de lo que se prueba

    Pasos:
    1. Preparación (Arrange)
    2. Ejecución (Act)
    3. Verificación (Assert)
    """
    # 1. Arrange - Preparar datos
    data = {...}

    # 2. Act - Ejecutar acción
    response = client.post("/endpoint", json=data)

    # 3. Assert - Verificar resultado
    assert response.status_code == 201
    assert response.json()["campo"] == valor
```

### Assertions Comunes

```python
# Status codes
assert response.status_code == 200
assert response.status_code == 201  # Created
assert response.status_code == 400  # Bad Request
assert response.status_code == 404  # Not Found
assert response.status_code == 422  # Validation Error

# Contenido de respuesta
data = response.json()
assert "campo" in data
assert data["campo"] == valor
assert isinstance(data, list)
assert len(data) > 0

# Base de datos
user = test_db.query(Usuario).first()
assert user is not None
assert user.nombre == "Test"

# Cookies/Headers
assert "user_session" in response.cookies
assert "/login" in response.headers["location"]
```

## 🔄 CI/CD

### GitHub Actions (ejemplo)

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt

    - name: Run tests
      run: |
        pytest test/ --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 🐛 Debugging

### Ver output durante las pruebas

```bash
# Mostrar prints
pytest test/ -s

# Modo verbose máximo
pytest test/ -vv

# Usar debugger
pytest test/ --pdb  # Abre pdb en fallos

# Debugger en warnings
pytest test/ --pdbcls=IPython.terminal.debugger:TerminalPdb
```

### Limpiar archivos de prueba

```bash
./run_tests.sh clean
```

## 📈 Métricas de Calidad

### Objetivos

| Métrica | Objetivo | Actual |
|---------|----------|---------|
| Cobertura | ≥ 80% | 🔄 |
| Tests pasando | 100% | 🔄 |
| Tiempo ejecución | < 30s | 🔄 |

### Verificar calidad del código

```bash
# Linting
flake8 test/

# Formateo
black test/ --check

# Type checking
mypy test/
```

## 🆘 Solución de Problemas

### Error: "ModuleNotFoundError"

```bash
# Asegúrate de estar en el directorio raíz
cd /ruta/al/proyecto

# O agrega al PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Error: Base de datos bloqueada

```bash
# Eliminar bases de datos de prueba
rm test.db test_crud.db
```

### Tests muy lentos

```bash
# Ejecutar solo tests rápidos
./run_tests.sh fast

# O usar ejecución paralela
pytest test/ -n auto
```

## 📚 Recursos Adicionales

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://realpython.com/pytest-python-testing/)

## 🤝 Contribuir

Al agregar nuevas pruebas:

1. Sigue las convenciones de nomenclatura
2. Documenta el propósito del test
3. Usa fixtures cuando sea posible
4. Verifica que todos los tests pasen
5. Mantén la cobertura arriba del 80%

```bash
# Antes de hacer commit
./run_tests.sh all
flake8 test/
black test/
```

---

**Última actualización:** Diciembre 2024
**Mantenedor:** Jhon David Gonzalez Garcia