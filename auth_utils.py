from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import crud_usuarios as crud
from database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verifica si la contraseña plana coincide con el hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    truncated_password = password[:72]
    return pwd_context.hash(truncated_password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Lógica de decodificación de token (simplificada)
    # Por ahora, simularemos que el 'token' es la cédula o el correo
    # En un proyecto real, se usaría un JWT
    user = crud.get_user_by_cedula_or_correo(db, token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas o/y token expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user