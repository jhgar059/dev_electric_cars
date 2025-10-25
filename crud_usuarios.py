from sqlalchemy.orm import Session
from sqlalchemy import or_
import models_sql as models
from modelos import UsuarioRegistro
from auth_utils import get_password_hash


def get_user_by_cedula_or_correo(db: Session, identificador: str):
    """Busca un usuario por cédula o correo."""
    return db.query(models.UsuarioSQL).filter(
        or_(
            models.UsuarioSQL.cedula == identificador,
            models.UsuarioSQL.correo == identificador
        )
    ).first()


def get_user_by_cedula(db: Session, cedula: str):
    return db.query(models.UsuarioSQL).filter(models.UsuarioSQL.cedula == cedula).first()


def get_user_by_correo(db: Session, correo: str):
    return db.query(models.UsuarioSQL).filter(models.UsuarioSQL.correo == correo).first()


def create_user(db: Session, user: UsuarioRegistro):
    """Crea un nuevo usuario y hashea la contraseña."""
    # Hashear la contraseña
    hashed_password = get_password_hash(user.password)

    # Crear la instancia del modelo SQL
    db_user = models.UsuarioSQL(
        nombre=user.nombre,
        edad=user.edad,
        correo=user.correo,
        cedula=user.cedula,
        celular=user.celular,
        hashed_password=hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_password(db: Session, user_id: int, new_password: str):
    """Actualiza la contraseña de un usuario (borra la antigua y pone la nueva)."""
    db_user = db.query(models.UsuarioSQL).filter(models.UsuarioSQL.id == user_id).first()
    if db_user:
        db_user.hashed_password = get_password_hash(new_password)
        db.commit()
        db.refresh(db_user)
        return db_user
    return None