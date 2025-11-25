from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # ⬅️ CLASE IMPORTADA
from sqlalchemy.orm import Session
# ... otras importaciones ...

logger = logging.getLogger("auth_utils")

# 🟢 SOLUCIÓN: Definición de oauth2_scheme
# La URL debe ser la del endpoint de login (como lo tienes en login.html)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# Configurar el contexto de contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ... el resto del archivo sigue igual ...

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

    truncated_password = password[:72]

    logger.debug(f"Hashing password (truncated length: {len(truncated_password)})")
    truncated_password = password[:72]
    return pwd_context.hash(truncated_password)

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