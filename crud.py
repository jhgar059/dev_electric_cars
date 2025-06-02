# crud.py
from sqlalchemy import Table, Column, Integer, String, Float, Boolean, MetaData, func # Importa func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import models_sql as models
from modelos import AutoElectrico, CargaBase, EstacionBase, CargaActualizada, EstacionActualizada

# --------------------- OPERACIONES AUTOS ---------------------

def get_autos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AutoElectricoSQL).offset(skip).limit(limit).all()

def get_auto(db: Session, auto_id: int):
    return db.query(models.AutoElectricoSQL).filter(models.AutoElectricoSQL.id == auto_id).first()

def get_auto_by_modelo(db: Session, modelo: str):
    return db.query(models.AutoElectricoSQL).filter(models.AutoElectricoSQL.modelo.ilike(f"%{modelo}%")).all()

def create_auto(db: Session, auto: AutoElectrico):
    # Opcional: Verificar si ya existe un auto con el mismo modelo y año para evitar duplicados
    existing_auto = db.query(models.AutoElectricoSQL).filter(
        models.AutoElectricoSQL.modelo == auto.modelo,
        models.AutoElectricoSQL.anio == auto.anio
    ).first()
    if existing_auto:
        return None # O lanzar una HTTPException en main.py

    db_auto = models.AutoElectricoSQL(**auto.model_dump())
    db.add(db_auto)
    db.commit()
    db.refresh(db_auto)
    return db_auto

def update_auto(db: Session, auto_id: int, auto: AutoElectrico):
    db_auto = db.query(models.AutoElectricoSQL).filter(models.AutoElectricoSQL.id == auto_id).first()
    if db_auto:
        for key, value in auto.model_dump(exclude_unset=True).items():
            setattr(db_auto, key, value)
        db.commit()
        db.refresh(db_auto)
        return db_auto
    return None

def delete_auto(db: Session, auto_id: int):
    db_auto = db.query(models.AutoElectricoSQL).filter(models.AutoElectricoSQL.id == auto_id).first()
    if db_auto:
        # Mover a la tabla de eliminados
        db_eliminado = models.AutoEliminadoSQL(**{
            "id": db_auto.id, # Conservar el ID original si se quiere
            "marca": db_auto.marca,
            "modelo": db_auto.modelo,
            "anio": db_auto.anio,
            "capacidad_bateria_kwh": db_auto.capacidad_bateria_kwh,
            "autonomia_km": db_auto.autonomia_km,
            "disponible": db_auto.disponible,
            "url_imagen": db_auto.url_imagen
        })
        db.add(db_eliminado)
        db.delete(db_auto)
        db.commit()
        return db_auto
    return None

def get_average_autonomy(db: Session) -> Optional[float]:
    """Calcula la autonomía promedio de todos los autos eléctricos."""
    result = db.query(func.avg(models.AutoElectricoSQL.autonomia_km)).scalar()
    return result if result is not None else 0.0


# --------------------- OPERACIONES CARGAS ---------------------

def get_cargas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CargaSQL).offset(skip).limit(limit).all()

def get_carga(db: Session, carga_id: int):
    return db.query(models.CargaSQL).filter(models.CargaSQL.id == carga_id).first()

def create_carga(db: Session, carga: CargaBase):
    # Opcional: Verificar si ya existe un registro de carga con el mismo modelo y tipo de autonomía
    existing_carga = db.query(models.CargaSQL).filter(
        models.CargaSQL.modelo == carga.modelo,
        models.CargaSQL.tipo_autonomia == carga.tipo_autonomia
    ).first()
    if existing_carga:
        return None # O lanzar una HTTPException

    db_carga = models.CargaSQL(**carga.model_dump())
    db.add(db_carga)
    db.commit()
    db.refresh(db_carga)
    return db_carga

def update_carga(db: Session, carga_id: int, carga: CargaActualizada):
    db_carga = db.query(models.CargaSQL).filter(models.CargaSQL.id == carga_id).first()
    if db_carga:
        for key, value in carga.model_dump(exclude_unset=True).items():
            setattr(db_carga, key, value)
        db.commit()
        db.refresh(db_carga)
        return db_carga
    return None

def delete_carga(db: Session, carga_id: int):
    db_carga = db.query(models.CargaSQL).filter(models.CargaSQL.id == carga_id).first()
    if db_carga:
        # Mover a la tabla de eliminados
        db_eliminado = models.CargaEliminadaSQL(**{
            "id": db_carga.id, # Conservar el ID original
            "modelo": db_carga.modelo,
            "tipo_autonomia": db_carga.tipo_autonomia,
            "autonomia_km": db_carga.autonomia_km,
            "consumo_kwh_100km": db_carga.consumo_kwh_100km,
            "tiempo_carga_horas": db_carga.tiempo_carga_horas,
            "dificultad_carga": db_carga.dificultad_carga,
            "requiere_instalacion_domestica": db_carga.requiere_instalacion_domestica,
            "url_imagen": db_carga.url_imagen
        })
        db.add(db_eliminado)
        db.delete(db_carga)
        db.commit()
        return db_carga
    return None

# --------------------- OPERACIONES ESTACIONES ---------------------

def get_estaciones(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.EstacionSQL).offset(skip).limit(limit).all()

def get_estacion(db: Session, estacion_id: int):
    return db.query(models.EstacionSQL).filter(models.EstacionSQL.id == estacion_id).first()

def create_estacion(db: Session, estacion: EstacionBase):
    # Opcional: Verificar si ya existe una estación con el mismo nombre y ubicación
    existing_estacion = db.query(models.EstacionSQL).filter(
        models.EstacionSQL.nombre == estacion.nombre,
        models.EstacionSQL.ubicacion == estacion.ubicacion
    ).first()
    if existing_estacion:
        return None # O lanzar una HTTPException

    db_estacion = models.EstacionSQL(**estacion.model_dump())
    db.add(db_estacion)
    db.commit()
    db.refresh(db_estacion)
    return db_estacion

def update_estacion(db: Session, estacion_id: int, estacion: EstacionActualizada):
    db_estacion = db.query(models.EstacionSQL).filter(models.EstacionSQL.id == estacion_id).first()
    if db_estacion:
        for key, value in estacion.model_dump(exclude_unset=True).items():
            setattr(db_estacion, key, value)
        db.commit()
        db.refresh(db_estacion)
        return db_estacion
    return None

def delete_estacion(db: Session, estacion_id: int):
    db_estacion = db.query(models.EstacionSQL).filter(models.EstacionSQL.id == estacion_id).first()
    if db_estacion:
        # Mover a la tabla de eliminados
        db_eliminado = models.EstacionEliminadaSQL(**{
            "id": db_estacion.id, # Conservar el ID original
            "nombre": db_estacion.nombre,
            "ubicacion": db_estacion.ubicacion,
            "tipo_conector": db_estacion.tipo_conector,
            "potencia_kw": db_estacion.potencia_kw,
            "num_conectores": db_estacion.num_conectores,
            "acceso_publico": db_estacion.acceso_publico,
            "horario_apertura": db_estacion.horario_apertura,
            "coste_por_kwh": db_estacion.coste_por_kwh,
            "operador": db_estacion.operador,
            "url_imagen": db_estacion.url_imagen
        })
        db.add(db_eliminado)
        db.delete(db_estacion)
        db.commit()
        return db_estacion
    return None

# --------------------- OPERACIONES PARA OBTENER ELEMENTOS ELIMINADOS ---------------------

def get_autos_eliminados(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AutoEliminadoSQL).offset(skip).limit(limit).all()

def get_auto_eliminado(db: Session, auto_id: int):
    return db.query(models.AutoEliminadoSQL).filter(models.AutoEliminadoSQL.id == auto_id).first()

def get_cargas_eliminadas(db: Session, skip: int = 0, limit: int = 100):
    # Asegúrate de que este query sea correcto para tu modelo CargaEliminadaSQL
    return db.query(models.CargaEliminadaSQL).offset(skip).limit(limit).all()

def get_carga_eliminada(db: Session, carga_id: int):
    return db.query(models.CargaEliminadaSQL).filter(models.CargaEliminadaSQL.id == carga_id).first()

def get_estaciones_eliminadas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.EstacionEliminadaSQL).offset(skip).limit(limit).all()

def get_estacion_eliminada(db: Session, estacion_id: int):
    return db.query(models.EstacionEliminadaSQL).filter(models.EstacionEliminadaSQL.id == estacion_id).first()