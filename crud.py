from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import models_sql as models
from modelos import AutoElectrico, CargaBase, EstacionBase

# --------------------- OPERACIONES AUTOS ---------------------

def get_autos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AutoElectricoSQL).offset(skip).limit(limit).all()

def get_auto(db: Session, auto_id: int):
    return db.query(models.AutoElectricoSQL).filter(models.AutoElectricoSQL.id == auto_id).first()

def create_auto(db: Session, auto: AutoElectrico):
    db_auto = models.AutoElectricoSQL(**auto.model_dump())
    db.add(db_auto)
    db.commit()
    db.refresh(db_auto)
    return db_auto

def update_auto(db: Session, auto_id: int, auto_data: Dict[str, Any]):
    db_auto = db.query(models.AutoElectricoSQL).filter(models.AutoElectricoSQL.id == auto_id).first()
    if db_auto:
        for key, value in auto_data.items():
            setattr(db_auto, key, value)
        db.commit()
        db.refresh(db_auto)
    return db_auto

def delete_auto(db: Session, auto_id: int):
    db_auto = db.query(models.AutoElectricoSQL).filter(models.AutoElectricoSQL.id == auto_id).first()
    if db_auto:
        db.delete(db_auto)
        db.commit()
    return db_auto

def filter_autos_by_marca(db: Session, marca: str):
    return db.query(models.AutoElectricoSQL).filter(models.AutoElectricoSQL.marca.ilike(f"%{marca}%")).all()

# --------------------- OPERACIONES CARGAS ---------------------

def get_cargas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CargaSQL).offset(skip).limit(limit).all()

def get_carga(db: Session, carga_id: int):
    return db.query(models.CargaSQL).filter(models.CargaSQL.id == carga_id).first()

def create_carga(db: Session, carga: CargaBase):
    db_carga = models.CargaSQL(**carga.model_dump())
    db.add(db_carga)
    db.commit()
    db.refresh(db_carga)
    return db_carga

def update_carga(db: Session, carga_id: int, carga_data: Dict[str, Any]):
    db_carga = db.query(models.CargaSQL).filter(models.CargaSQL.id == carga_id).first()
    if db_carga:
        for key, value in carga_data.items():
            setattr(db_carga, key, value)
        db.commit()
        db.refresh(db_carga)
    return db_carga

def delete_carga(db: Session, carga_id: int):
    db_carga = db.query(models.CargaSQL).filter(models.CargaSQL.id == carga_id).first()
    if db_carga:
        db.delete(db_carga)
        db.commit()
    return db_carga

def filter_cargas_by_dificultad(db: Session, nivel: str):
    return db.query(models.CargaSQL).filter(models.CargaSQL.dificultad_carga.ilike(f"%{nivel}%")).all()

def filter_cargas_by_modelo(db: Session, modelo: str):
    return db.query(models.CargaSQL).filter(models.CargaSQL.modelo.ilike(f"%{modelo}%")).all()

# --------------------- OPERACIONES ESTACIONES ---------------------

def get_estaciones(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.EstacionSQL).offset(skip).limit(limit).all()

def get_estacion(db: Session, estacion_id: int):
    return db.query(models.EstacionSQL).filter(models.EstacionSQL.id == estacion_id).first()

def create_estacion(db: Session, estacion: EstacionBase):
    db_estacion = models.EstacionSQL(**estacion.model_dump())
    db.add(db_estacion)
    db.commit()
    db.refresh(db_estacion)
    return db_estacion

def update_estacion(db: Session, estacion_id: int, estacion_data: Dict[str, Any]):
    db_estacion = db.query(models.EstacionSQL).filter(models.EstacionSQL.id == estacion_id).first()
    if db_estacion:
        for key, value in estacion_data.items():
            setattr(db_estacion, key, value)
        db.commit()
        db.refresh(db_estacion)
    return db_estacion

def delete_estacion(db: Session, estacion_id: int):
    db_estacion = db.query(models.EstacionSQL).filter(models.EstacionSQL.id == estacion_id).first()
    if db_estacion:
        db.delete(db_estacion)
        db.commit()
    return db_estacion

def filter_estaciones_by_operador(db: Session, operador: str):
    return db.query(models.EstacionSQL).filter(models.EstacionSQL.operador.ilike(f"%{operador}%")).all()

def filter_estaciones_by_tipo_conector(db: Session, tipo_conector: str):
    return db.query(models.EstacionSQL).filter(models.EstacionSQL.tipo_conector.ilike(f"%{tipo_conector}%")).all()