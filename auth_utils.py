from werkzeug.security import generate_password_hash, check_password_hash
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import crud_usuarios as crud
from database import get_db
import logging
import models_sql

logger = logging.getLogger("auth_utils")

# 🟢 SOLUCIÓN 1 (YA APLICADA): Definición de oauth2_scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si la contraseña plana coincide con el hash usando Werkzeug.

    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash de la contraseña almacenado en la BD

    Returns:
        bool: True si coinciden, False en caso contrario
    """
    try:
        # Werkzeug gestiona la longitud de forma interna.
        # Ya no es necesario el trucado a 72 bytes.
        result = check_password_hash(hashed_password, plain_password)
        logger.debug(f"Verificación de contraseña con Werkzeug: {result}")
        return result
    except Exception as e:
        logger.error(f"Error al verificar contraseña con Werkzeug: {e}", exc_info=True)
        return False


def get_password_hash(password: str) -> str:
    """
    Genera un hash seguro de la contraseña usando Werkzeug (por defecto, utiliza PBKDF2).

    Args:
        password: Contraseña en texto plano

    Returns:
        str: Hash de la contraseña
    """
    # 🔑 Werkzeug es seguro por defecto (usa sha256 o sha512 en la configuración de hashing)
    hashed_password = generate_password_hash(password)
    logger.debug("Hash de contraseña generado con Werkzeug")
    return hashed_password


# 🟢 SOLUCIÓN 2 (NUEVA): Definición de la función de dependencia
def get_current_user_simplified(token: str = Depends(oauth2_scheme),
                                db: Session = Depends(get_db)) -> models_sql.UsuarioSQL:
    """
    Función de dependencia para obtener el usuario actual a partir del token.
    En este caso simplificado, el token (el valor que viene en el header) es la cédula.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # El token se usa para buscar el usuario por cédula o correo
        user = crud.get_user_by_cedula_or_correo(db, token)

        if user is None:
            logger.warning(f"Token inválido o usuario no encontrado: {token}")
            raise credentials_exception

        if not user.activo:
            logger.warning(f"Usuario inactivo intentó acceder: {token}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo",
            )

        logger.debug(f"Usuario autenticado: {user.cedula}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener usuario actual: {e}", exc_info=True)
        raise credentials_exception