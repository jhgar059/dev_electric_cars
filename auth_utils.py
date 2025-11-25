from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import crud_usuarios as crud
from database import get_db
import logging

logger = logging.getLogger("auth_utils")

# Configurar el contexto de contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si la contraseña plana coincide con el hash.

    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash de la contraseña almacenado en la BD

    Returns:
        bool: True si coinciden, False en caso contrario
    """
    try:
        # Truncar la contraseña a 72 bytes antes de verificar
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

    Args:
        password: Contraseña en texto plano

    Returns:
        str: Hash de la contraseña

    Note:
        Bcrypt tiene un límite de 72 bytes, por lo que truncamos la contraseña
    """
    try:
        # Truncar la contraseña a 72 bytes antes de hashear
        truncated_password = password[:72]
        hashed = pwd_context.hash(truncated_password)
        logger.debug("Contraseña hasheada exitosamente")
        return hashed
    except Exception as e:
        logger.error(f"Error al hashear contraseña: {e}", exc_info=True)
        raise


# OAuth2 scheme para el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Obtiene el usuario actual a partir del token.

    Args:
        token: Token de autenticación (en este caso simplificado, es la cédula)
        db: Sesión de base de datos

    Returns:
        UsuarioSQL: Usuario autenticado

    Raises:
        HTTPException: Si el token es inválido o el usuario no existe

    Note:
        Esta es una implementación simplificada. En producción, usar JWT.
    """
    try:
        # En esta implementación simplificada, el token es la cédula del usuario
        user = crud.get_user_by_cedula_or_correo(db, token)

        if user is None:
            logger.warning(f"Token inválido o usuario no encontrado: {token}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas o token expirado.",
                headers={"WWW-Authenticate": "Bearer"},
            )

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error al validar credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )