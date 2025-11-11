from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import crud_usuarios as crud
from database import get_db


# Contexto de passlib: esquema bcrypt y autoconservación de hashes antiguos
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    """Verifica si la contraseña plana coincide con el hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Genera el hash de una contraseña, truncando a 72 bytes si es necesario
    para cumplir con el límite de bcrypt."""
    # CORRECCIÓN: Truncar la contraseña a 72 caracteres antes de hashear
    truncated_password = password[:72]
    return pwd_context.hash(truncated_password)


# Esquema OAuth2 para inyección de dependencia y extracción de token
# (Se eliminó el punto final en 'api/login')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Dependencia que obtiene el usuario a partir del token (cédula o correo)."""
    user = crud.get_user_by_cedula_or_correo(db, token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            # Se corrigió el detalle del mensaje para mejor claridad en español
            detail="Credenciales inválidas y/o token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user