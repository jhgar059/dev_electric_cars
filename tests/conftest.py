"""
conftest.py - Configuración compartida para todas las pruebas de pytest

Este archivo contiene fixtures y configuraciones que están disponibles
para todos los archivos de prueba.
"""

import pytest
import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from database import Base
import logging

# Configurar logging para pruebas
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Base de datos en memoria para pruebas
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """
    Crea el engine de SQLAlchemy para toda la sesión de pruebas.
    Usa una base de datos en memoria para velocidad.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False  # Cambiar a True para debug SQL
    )

    # Habilitar foreign keys para SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def tables(engine):
    """
    Crea todas las tablas una vez por sesión de pruebas.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine, tables):
    """
    Crea una nueva sesión de base de datos para cada prueba.
    Todas las transacciones se revierten al final de cada prueba.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """
    Crea un TestClient de FastAPI con la sesión de BD mockeada.
    """
    from fastapi.testclient import TestClient
    from main import app
    from database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """
    Datos de usuario de prueba estándar.
    """
    return {
        "nombre": "Usuario Test",
        "edad": 25,
        "correo": "test@example.com",
        "cedula": "1234567890",
        "celular": "3001234567",
        "password": "TestPassword123"
    }


@pytest.fixture
def authenticated_user(client, db_session, test_user_data):
    """
    Crea un usuario y lo autentica, devolviendo las cookies de sesión.
    """
    # Registrar usuario
    client.post("/register", data=test_user_data)

    # Login
    login_response = client.post(
        "/api/login",
        data={
            "username": test_user_data["cedula"],
            "password": test_user_data["password"]
        }
    )

    # Devolver cookies de sesión
    return login_response.cookies


# Hooks de pytest para personalizar el comportamiento

def pytest_configure(config):
    """
    Hook que se ejecuta antes de iniciar las pruebas.
    """
    print("\n" + "=" * 70)
    print("INICIANDO SUITE DE PRUEBAS - ELECTRIC CARS DATABASE")
    print("=" * 70 + "\n")


def pytest_sessionfinish(session, exitstatus):
    """
    Hook que se ejecuta al finalizar todas las pruebas.
    """
    print("\n" + "=" * 70)
    print("SUITE DE PRUEBAS COMPLETADA")
    print(f"Estado de salida: {exitstatus}")
    print("=" * 70 + "\n")


def pytest_collection_modifyitems(config, items):
    """
    Hook para modificar los items de prueba después de la recolección.
    Útil para agregar marcadores automáticamente.
    """
    for item in items:
        # Marcar automáticamente pruebas lentas
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)

        # Agregar marcador según el módulo
        if "test_auth" in item.nodeid:
            item.add_marker(pytest.mark.auth)
        elif "test_crud" in item.nodeid:
            item.add_marker(pytest.mark.crud)


# Fixtures adicionales para datos de prueba

@pytest.fixture
def sample_auto():
    """Datos de muestra para un auto eléctrico"""
    return {
        "marca": "Tesla",
        "modelo": "Model 3",
        "anio": 2023,
        "capacidad_bateria_kwh": 75.0,
        "autonomia_km": 500.0,
        "disponible": True,
        "url_imagen": "/static/images/test.jpg"
    }


@pytest.fixture
def sample_carga():
    """Datos de muestra para un registro de carga"""
    return {
        "modelo_auto": "Tesla Model 3",
        "tipo_autonomia": "EPA",
        "autonomia_km": 500.0,
        "consumo_kwh_100km": 15.0,
        "tiempo_carga_horas": 8.0,
        "dificultad_carga": "baja",
        "requiere_instalacion_domestica": False,
        "url_imagen": "/static/images/test_carga.jpg"
    }


@pytest.fixture
def sample_estacion():
    """Datos de muestra para una estación de carga"""
    return {
        "nombre": "Supercharger Test",
        "ubicacion": "Calle Test #123",
        "tipo_conector": "Tesla",
        "potencia_kw": 250.0,
        "num_conectores": 12,
        "acceso_publico": True,
        "horario_apertura": "24/7",
        "coste_por_kwh": 0.25,
        "operador": "Tesla",
        "url_imagen": "/static/images/test_estacion.jpg"
    }