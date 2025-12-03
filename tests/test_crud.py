import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
import models_sql
from auth_utils import get_password_hash

# Base de datos en memoria para testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_crud.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de la dependencia de base de datos para testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Fixture que crea y limpia la base de datos para cada test"""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auto_test_data():
    """Datos de prueba para un auto eléctrico"""
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
def carga_test_data():
    """Datos de prueba para un registro de carga"""
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
def estacion_test_data():
    """Datos de prueba para una estación de carga"""
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


# ==================== TESTS PARA AUTOS ====================

class TestAutosCreate:
    """Pruebas para crear autos eléctricos"""

    def test_crear_auto_exitoso(self, test_db, auto_test_data):
        """Test: Crear un auto eléctrico exitosamente"""
        response = client.post("/api/autos", json=auto_test_data)
        assert response.status_code == 201
        data = response.json()
        assert data["marca"] == auto_test_data["marca"]
        assert data["modelo"] == auto_test_data["modelo"]
        assert "id" in data

    def test_crear_auto_duplicado(self, test_db, auto_test_data):
        """Test: Fallo al crear auto duplicado"""
        # Crear el primer auto
        client.post("/api/autos", json=auto_test_data)

        # Intentar crear el mismo auto de nuevo
        response = client.post("/api/autos", json=auto_test_data)
        assert response.status_code == 400
        assert "ya existe" in response.json()["detail"].lower()

    def test_crear_auto_datos_invalidos(self, test_db):
        """Test: Fallo al crear auto con datos inválidos"""
        invalid_data = {
            "marca": "T",  # Muy corto (mínimo 2)
            "modelo": "Model 3",
            "anio": 2030,  # Año futuro no permitido
            "capacidad_bateria_kwh": -10,  # Negativo
            "autonomia_km": 500.0,
            "disponible": True
        }
        response = client.post("/api/autos", json=invalid_data)
        assert response.status_code == 422

    def test_crear_auto_campos_faltantes(self, test_db):
        """Test: Fallo al crear auto sin campos requeridos"""
        incomplete_data = {
            "marca": "Tesla",
            # Falta modelo, año, etc.
        }
        response = client.post("/api/autos", json=incomplete_data)
        assert response.status_code == 422


class TestAutosRead:
    """Pruebas para leer autos eléctricos"""

    def test_obtener_todos_los_autos(self, test_db, auto_test_data):
        """Test: Obtener lista de todos los autos"""
        # Crear varios autos
        client.post("/api/autos", json=auto_test_data)
        auto_test_data["modelo"] = "Model Y"
        client.post("/api/autos", json=auto_test_data)

        response = client.get("/api/autos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert isinstance(data, list)

    def test_obtener_auto_por_id(self, test_db, auto_test_data):
        """Test: Obtener un auto específico por ID"""
        create_response = client.post("/api/autos", json=auto_test_data)
        auto_id = create_response.json()["id"]

        response = client.get(f"/api/autos/{auto_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == auto_id
        assert data["marca"] == auto_test_data["marca"]

    def test_obtener_auto_inexistente(self, test_db):
        """Test: Fallo al obtener auto que no existe"""
        response = client.get("/api/autos/9999")
        assert response.status_code == 404

    def test_buscar_autos_por_modelo(self, test_db, auto_test_data):
        """Test: Buscar autos por modelo"""
        client.post("/api/autos", json=auto_test_data)

        response = client.get("/api/autos/search/?modelo=Model")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "Model" in data[0]["modelo"]

    def test_buscar_autos_sin_resultados(self, test_db):
        """Test: Búsqueda sin resultados"""
        response = client.get("/api/autos/search/?modelo=ModeloInexistente")
        assert response.status_code == 404


class TestAutosUpdate:
    """Pruebas para actualizar autos eléctricos"""

    def test_actualizar_auto_exitoso(self, test_db, auto_test_data):
        """Test: Actualizar un auto exitosamente"""
        create_response = client.post("/api/autos", json=auto_test_data)
        auto_id = create_response.json()["id"]

        update_data = {"autonomia_km": 600.0}
        response = client.put(f"/api/autos/{auto_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["autonomia_km"] == 600.0

    def test_actualizar_auto_inexistente(self, test_db):
        """Test: Fallo al actualizar auto que no existe"""
        update_data = {"autonomia_km": 600.0}
        response = client.put("/api/autos/9999", json=update_data)
        assert response.status_code == 404

    def test_actualizar_auto_datos_invalidos(self, test_db, auto_test_data):
        """Test: Fallo al actualizar con datos inválidos"""
        create_response = client.post("/api/autos", json=auto_test_data)
        auto_id = create_response.json()["id"]

        invalid_update = {"autonomia_km": -100}  # Negativo
        response = client.put(f"/api/autos/{auto_id}", json=invalid_update)
        assert response.status_code == 422


class TestAutosDelete:
    """Pruebas para eliminar autos eléctricos"""

    def test_eliminar_auto_exitoso(self, test_db, auto_test_data):
        """Test: Eliminar un auto exitosamente"""
        create_response = client.post("/api/autos", json=auto_test_data)
        auto_id = create_response.json()["id"]

        response = client.delete(f"/api/autos/{auto_id}")
        assert response.status_code == 204

        # Verificar que el auto fue movido al historial
        deleted_autos = test_db.query(models_sql.AutoEliminadoSQL).all()
        assert len(deleted_autos) == 1

    def test_eliminar_auto_inexistente(self, test_db):
        """Test: Fallo al eliminar auto que no existe"""
        response = client.delete("/api/autos/9999")
        assert response.status_code == 404


# ==================== TESTS PARA CARGAS ====================

class TestCargasCreate:
    """Pruebas para crear registros de carga"""

    def test_crear_carga_exitoso(self, test_db, carga_test_data):
        """Test: Crear un registro de carga exitosamente"""
        response = client.post("/api/cargas", json=carga_test_data)
        assert response.status_code == 201
        data = response.json()
        assert data["modelo_auto"] == carga_test_data["modelo_auto"]
        assert "id" in data

    def test_crear_carga_datos_invalidos(self, test_db):
        """Test: Fallo al crear carga con datos inválidos"""
        invalid_data = {
            "modelo_auto": "",  # Vacío
            "tipo_autonomia": "EPA",
            "autonomia_km": -100,  # Negativo
            "consumo_kwh_100km": 15.0,
            "tiempo_carga_horas": 8.0,
            "dificultad_carga": "baja",
            "requiere_instalacion_domestica": False
        }
        response = client.post("/api/cargas", json=invalid_data)
        assert response.status_code == 422


class TestCargasRead:
    """Pruebas para leer registros de carga"""

    def test_obtener_todas_las_cargas(self, test_db, carga_test_data):
        """Test: Obtener lista de todas las cargas"""
        client.post("/api/cargas", json=carga_test_data)

        response = client.get("/api/cargas")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_buscar_cargas_por_modelo(self, test_db, carga_test_data):
        """Test: Buscar cargas por modelo de auto"""
        client.post("/api/cargas", json=carga_test_data)

        response = client.get("/api/cargas/search/?modelo_auto=Tesla")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0


class TestCargasUpdate:
    """Pruebas para actualizar registros de carga"""

    def test_actualizar_carga_exitoso(self, test_db, carga_test_data):
        """Test: Actualizar un registro de carga exitosamente"""
        create_response = client.post("/api/cargas", json=carga_test_data)
        carga_id = create_response.json()["id"]

        update_data = {"dificultad_carga": "media"}
        response = client.put(f"/api/cargas/{carga_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["dificultad_carga"] == "media"


class TestCargasDelete:
    """Pruebas para eliminar registros de carga"""

    def test_eliminar_carga_exitoso(self, test_db, carga_test_data):
        """Test: Eliminar un registro de carga exitosamente"""
        create_response = client.post("/api/cargas", json=carga_test_data)
        carga_id = create_response.json()["id"]

        response = client.delete(f"/api/cargas/{carga_id}")
        assert response.status_code == 204


# ==================== TESTS PARA ESTACIONES ====================

class TestEstacionesCreate:
    """Pruebas para crear estaciones de carga"""

    def test_crear_estacion_exitoso(self, test_db, estacion_test_data):
        """Test: Crear una estación de carga exitosamente"""
        response = client.post("/api/estaciones", json=estacion_test_data)
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == estacion_test_data["nombre"]
        assert "id" in data

    def test_crear_estacion_datos_invalidos(self, test_db):
        """Test: Fallo al crear estación con datos inválidos"""
        invalid_data = {
            "nombre": "T",  # Muy corto
            "ubicacion": "Test",  # Muy corto
            "tipo_conector": "Tesla",
            "potencia_kw": -50,  # Negativo
            "num_conectores": 0,  # Debe ser al menos 1
            "acceso_publico": True,
            "horario_apertura": "24/7",
            "coste_por_kwh": 0.25,
            "operador": "Tesla"
        }
        response = client.post("/api/estaciones", json=invalid_data)
        assert response.status_code == 422


class TestEstacionesRead:
    """Pruebas para leer estaciones de carga"""

    def test_obtener_todas_las_estaciones(self, test_db, estacion_test_data):
        """Test: Obtener lista de todas las estaciones"""
        client.post("/api/estaciones", json=estacion_test_data)

        response = client.get("/api/estaciones")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_buscar_estaciones_por_nombre(self, test_db, estacion_test_data):
        """Test: Buscar estaciones por nombre"""
        client.post("/api/estaciones", json=estacion_test_data)

        response = client.get("/api/estaciones/search/?nombre=Supercharger")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0


class TestEstacionesUpdate:
    """Pruebas para actualizar estaciones de carga"""

    def test_actualizar_estacion_exitoso(self, test_db, estacion_test_data):
        """Test: Actualizar una estación exitosamente"""
        create_response = client.post("/api/estaciones", json=estacion_test_data)
        estacion_id = create_response.json()["id"]

        update_data = {"potencia_kw": 300.0}
        response = client.put(f"/api/estaciones/{estacion_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["potencia_kw"] == 300.0


class TestEstacionesDelete:
    """Pruebas para eliminar estaciones de carga"""

    def test_eliminar_estacion_exitoso(self, test_db, estacion_test_data):
        """Test: Eliminar una estación exitosamente"""
        create_response = client.post("/api/estaciones", json=estacion_test_data)
        estacion_id = create_response.json()["id"]

        response = client.delete(f"/api/estaciones/{estacion_id}")
        assert response.status_code == 204


# ==================== TESTS DE ESTADÍSTICAS ====================

class TestEstadisticas:
    """Pruebas para los endpoints de estadísticas"""

    def test_obtener_estadisticas_autos_por_marca(self, test_db, auto_test_data):
        """Test: Obtener estadísticas de autos por marca"""
        client.post("/api/autos", json=auto_test_data)

        response = client.get("/api/statistics/cars_by_brand")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "marca" in data[0]
        assert "count" in data[0]

    def test_obtener_potencia_estaciones_por_conector(self, test_db, estacion_test_data):
        """Test: Obtener potencia promedio por tipo de conector"""
        client.post("/api/estaciones", json=estacion_test_data)

        response = client.get("/api/statistics/station_power_by_connector_type")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_obtener_distribucion_dificultad_carga(self, test_db, carga_test_data):
        """Test: Obtener distribución de dificultad de carga"""
        client.post("/api/cargas", json=carga_test_data)

        response = client.get("/api/statistics/charge_difficulty_distribution")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])