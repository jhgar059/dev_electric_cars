from passlib.context import CryptContext
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

# Configurar el contexto de contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si la contraseña plana coincide con el hash.
    """
    try:
        # Truncar la contraseña a 72 bytes antes de verificar (corrección previa)
        truncated_password = plain_password[:72]
        result = pwd_context.verify(truncated_password, hashed_password)
        logger.debug(f"Verificación de contraseña: {result}")
        return result
    except Exception as e:
        logger.error(f"Error al verificar contraseña: {e}", exc_info=True)
        return False


def get_password_hash(password: str) -> str:
    """
    Genera un hash bcrypt de la contraseña.
    """
    # Truncar la contraseña a 72 bytes antes de hashear (corrección previa)
    truncated_password = password[:72]
    return pwd_context.hash(truncated_password)


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