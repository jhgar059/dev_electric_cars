import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
import models_sql
from auth_utils import get_password_hash

# Base de datos en memoria para testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de la dependencia de base de datos para testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override de dependencia
app.dependency_overrides[get_db] = override_get_db

# Cliente de testing
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Fixture que crea y limpia la base de datos para cada test"""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(test_db):
    """Fixture que crea un usuario de prueba"""
    user_data = {
        "nombre": "Test User",
        "edad": 25,
        "correo": "test@example.com",
        "cedula": "1234567890",
        "celular": "3001234567",
        "hashed_password": get_password_hash("Password123"),
        "activo": True
    }
    user = models_sql.UsuarioSQL(**user_data)
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestRegistro:
    """Pruebas para el registro de usuarios"""

    def test_registro_exitoso(self, test_db):
        """Test: Registro exitoso de un nuevo usuario"""
        response = client.post(
            "/register",
            data={
                "nombre": "Nuevo Usuario",
                "edad": 30,
                "correo": "nuevo@example.com",
                "cedula": "9876543210",
                "celular": "3109876543",
                "password": "Password123"
            },
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirección exitosa
        assert "/login" in response.headers["location"]

        # Verificar que el usuario fue creado en la BD
        user = test_db.query(models_sql.UsuarioSQL).filter(
            models_sql.UsuarioSQL.cedula == "9876543210"
        ).first()
        assert user is not None
        assert user.nombre == "Nuevo Usuario"
        assert user.correo == "nuevo@example.com"

    def test_registro_cedula_duplicada(self, test_db, test_user):
        """Test: Fallo al registrar con cédula duplicada"""
        response = client.post(
            "/register",
            data={
                "nombre": "Usuario Duplicado",
                "edad": 28,
                "correo": "otro@example.com",
                "cedula": test_user.cedula,  # Cédula ya existente
                "celular": "3001111111",
                "password": "Password123"
            }
        )
        assert response.status_code == 400
        assert "cédula ya está registrada" in response.text.lower()

    def test_registro_correo_duplicado(self, test_db, test_user):
        """Test: Fallo al registrar con correo duplicado"""
        response = client.post(
            "/register",
            data={
                "nombre": "Usuario Duplicado",
                "edad": 28,
                "correo": test_user.correo,  # Correo ya existente
                "cedula": "1111111111",
                "celular": "3001111111",
                "password": "Password123"
            }
        )
        assert response.status_code == 400
        assert "correo ya está registrado" in response.text.lower()

    def test_registro_contrasena_sin_numero(self, test_db):
        """Test: Fallo al registrar con contraseña sin número"""
        response = client.post(
            "/register",
            data={
                "nombre": "Test User",
                "edad": 25,
                "correo": "test2@example.com",
                "cedula": "2222222222",
                "celular": "3002222222",
                "password": "PasswordSinNumero"
            }
        )
        # La validación debe ocurrir en el frontend, pero Pydantic también valida
        assert response.status_code in [400, 422]

    def test_registro_contrasena_corta(self, test_db):
        """Test: Fallo al registrar con contraseña menor a 8 caracteres"""
        response = client.post(
            "/register",
            data={
                "nombre": "Test User",
                "edad": 25,
                "correo": "test3@example.com",
                "cedula": "3333333333",
                "celular": "3003333333",
                "password": "Pass1"
            }
        )
        assert response.status_code in [400, 422]

    def test_registro_edad_menor(self, test_db):
        """Test: Fallo al registrar con edad menor a 18"""
        response = client.post(
            "/register",
            data={
                "nombre": "Usuario Menor",
                "edad": 17,
                "correo": "menor@example.com",
                "cedula": "4444444444",
                "celular": "3004444444",
                "password": "Password123"
            }
        )
        assert response.status_code in [400, 422]


class TestLogin:
    """Pruebas para el inicio de sesión"""

    def test_login_exitoso_con_cedula(self, test_db, test_user):
        """Test: Login exitoso usando cédula"""
        response = client.post(
            "/api/login",
            data={
                "username": test_user.cedula,
                "password": "Password123"
            },
            follow_redirects=False
        )
        assert response.status_code == 302
        assert "/index" in response.headers["location"]
        # Verificar que se establece la cookie de sesión
        assert "user_session" in response.cookies

    def test_login_exitoso_con_correo(self, test_db, test_user):
        """Test: Login exitoso usando correo"""
        response = client.post(
            "/api/login",
            data={
                "username": test_user.correo,
                "password": "Password123"
            },
            follow_redirects=False
        )
        assert response.status_code == 302
        assert "/index" in response.headers["location"]
        assert "user_session" in response.cookies

    def test_login_usuario_inexistente(self, test_db):
        """Test: Fallo al iniciar sesión con usuario inexistente"""
        response = client.post(
            "/api/login",
            data={
                "username": "usuario_inexistente",
                "password": "Password123"
            }
        )
        assert response.status_code == 401
        assert "credenciales incorrectas" in response.text.lower()

    def test_login_contrasena_incorrecta(self, test_db, test_user):
        """Test: Fallo al iniciar sesión con contraseña incorrecta"""
        response = client.post(
            "/api/login",
            data={
                "username": test_user.cedula,
                "password": "ContraseñaIncorrecta123"
            }
        )
        assert response.status_code == 401
        assert "credenciales incorrectas" in response.text.lower()

    def test_login_usuario_inactivo(self, test_db, test_user):
        """Test: Fallo al iniciar sesión con usuario inactivo"""
        # Desactivar usuario
        test_user.activo = False
        test_db.commit()

        response = client.post(
            "/api/login",
            data={
                "username": test_user.cedula,
                "password": "Password123"
            }
        )
        assert response.status_code == 403
        assert "inactivo" in response.text.lower()


class TestCambioPassword:
    """Pruebas para el cambio de contraseña"""

    def test_cambio_password_exitoso_con_cedula(self, test_db, test_user):
        """Test: Cambio de contraseña exitoso usando cédula"""
        response = client.post(
            "/change_password",
            data={
                "identificador": test_user.cedula,
                "password_anterior": None,  # No necesaria con cédula
                "password_nueva": "NuevaPassword123",
                "password_nueva_confirmacion": "NuevaPassword123"
            },
            follow_redirects=False
        )
        assert response.status_code == 302
        assert "/login" in response.headers["location"]

    def test_cambio_password_exitoso_con_correo(self, test_db, test_user):
        """Test: Cambio de contraseña exitoso usando correo"""
        response = client.post(
            "/change_password",
            data={
                "identificador": test_user.correo,
                "password_anterior": "Password123",  # Necesaria con correo
                "password_nueva": "NuevaPassword456",
                "password_nueva_confirmacion": "NuevaPassword456"
            },
            follow_redirects=False
        )
        assert response.status_code == 302
        assert "/login" in response.headers["location"]

    def test_cambio_password_sin_anterior_con_correo(self, test_db, test_user):
        """Test: Fallo al cambiar contraseña sin proporcionar la anterior (usando correo)"""
        response = client.post(
            "/change_password",
            data={
                "identificador": test_user.correo,
                "password_anterior": None,
                "password_nueva": "NuevaPassword789",
                "password_nueva_confirmacion": "NuevaPassword789"
            }
        )
        assert response.status_code == 400
        assert "contraseña anterior" in response.text.lower()

    def test_cambio_password_anterior_incorrecta(self, test_db, test_user):
        """Test: Fallo con contraseña anterior incorrecta"""
        response = client.post(
            "/change_password",
            data={
                "identificador": test_user.correo,
                "password_anterior": "ContraseñaIncorrecta123",
                "password_nueva": "NuevaPassword789",
                "password_nueva_confirmacion": "NuevaPassword789"
            }
        )
        assert response.status_code == 401
        assert "contraseña anterior incorrecta" in response.text.lower()

    def test_cambio_password_confirmacion_no_coincide(self, test_db, test_user):
        """Test: Fallo cuando las contraseñas nuevas no coinciden"""
        response = client.post(
            "/change_password",
            data={
                "identificador": test_user.cedula,
                "password_anterior": None,
                "password_nueva": "NuevaPassword123",
                "password_nueva_confirmacion": "NuevaPasswordDiferente123"
            }
        )
        assert response.status_code in [400, 422]

    def test_cambio_password_usuario_inexistente(self, test_db):
        """Test: Fallo al cambiar contraseña de usuario inexistente"""
        response = client.post(
            "/change_password",
            data={
                "identificador": "9999999999",
                "password_anterior": None,
                "password_nueva": "NuevaPassword123",
                "password_nueva_confirmacion": "NuevaPassword123"
            }
        )
        assert response.status_code == 404
        assert "usuario no encontrado" in response.text.lower()


class TestLogout:
    """Pruebas para el cierre de sesión"""

    def test_logout_exitoso(self, test_db, test_user):
        """Test: Cierre de sesión exitoso"""
        # Primero hacer login
        login_response = client.post(
            "/api/login",
            data={
                "username": test_user.cedula,
                "password": "Password123"
            }
        )
        assert "user_session" in login_response.cookies

        # Ahora hacer logout
        logout_response = client.get("/api/logout", follow_redirects=False)
        assert logout_response.status_code == 302
        assert "/login" in logout_response.headers["location"]
        # Verificar que la cookie se eliminó
        assert logout_response.cookies.get("user_session", "") == ""


class TestAutorizacion:
    """Pruebas para verificar la protección de rutas"""

    def test_acceso_cars_sin_autenticacion(self, test_db):
        """Test: Acceso a /cars sin autenticación redirige a login"""
        response = client.get("/cars", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["location"]

    def test_acceso_cars_con_autenticacion(self, test_db, test_user):
        """Test: Acceso a /cars con autenticación exitoso"""
        # Simular cookie de sesión
        cookies = {"user_session": test_user.cedula}
        response = client.get("/cars", cookies=cookies)
        assert response.status_code == 200

    def test_acceso_index_sin_autenticacion(self, test_db):
        """Test: Acceso a /index sin autenticación (debe permitir)"""
        response = client.get("/index")
        assert response.status_code == 200


class TestHashingPassword:
    """Pruebas para el hashing de contraseñas"""

    def test_password_se_hashea_correctamente(self, test_db):
        """Test: La contraseña se hashea y no se guarda en texto plano"""
        response = client.post(
            "/register",
            data={
                "nombre": "Test Hash",
                "edad": 25,
                "correo": "hash@example.com",
                "cedula": "5555555555",
                "celular": "3005555555",
                "password": "TestPassword123"
            },
            follow_redirects=False
        )

        # Verificar que el usuario fue creado
        user = test_db.query(models_sql.UsuarioSQL).filter(
            models_sql.UsuarioSQL.cedula == "5555555555"
        ).first()

        assert user is not None
        # Verificar que la contraseña NO está en texto plano
        assert user.hashed_password != "TestPassword123"
        # Verificar que es un hash (debe tener cierta longitud)
        assert len(user.hashed_password) > 20

    def test_verificacion_password_funciona(self, test_db, test_user):
        """Test: La verificación de contraseña funciona correctamente"""
        from auth_utils import verify_password

        # Verificar contraseña correcta
        assert verify_password("Password123", test_user.hashed_password) is True

        # Verificar contraseña incorrecta
        assert verify_password("ContraseñaIncorrecta", test_user.hashed_password) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])