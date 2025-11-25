# crud.py - CORREGIDO PARA SQLALCHEMY 2.0 (VERSION FINAL)
from sqlalchemy import func, select, update, delete  # Añadidos select, update, delete
from sqlalchemy.orm import Session
from typing import List, Optional
import models_sql as models
# Se asume que AutoActualizado debe estar importado para update_auto
from modelos import AutoElectrico, CargaBase, EstacionBase, CargaActualizada, EstacionActualizada, AutoActualizado, \
    EstacionActualizada


# --------------------- OPERACIONES AUTOS ---------------------

def get_autos(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene una lista de autos eléctricos con paginación."""
    stmt = select(models.AutoElectricoSQL).offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_auto(db: Session, auto_id: int):
    """Obtiene un auto eléctrico por su ID."""
    stmt = select(models.AutoElectricoSQL).where(models.AutoElectricoSQL.id == auto_id)
    return db.scalar(stmt)  # db.scalar(stmt) es el equivalente moderno de .first() para resultados únicos


def get_auto_by_modelo(db: Session, modelo: str):
    """Busca autos eléctricos por una parte de su modelo (case-insensitive)."""
    # Se simplifica la cadena LIKE, f"%{modelo}%" es suficiente
    stmt = select(models.AutoElectricoSQL).where(models.AutoElectricoSQL.modelo.ilike(f"%{modelo}%"))
    return db.scalars(stmt).all()


def create_auto(db: Session, auto: AutoElectrico):
    """Crea un nuevo auto eléctrico. Verifica duplicados."""
    # Uso de select/scalar para la verificación
    stmt_check = select(models.AutoElectricoSQL).where(
        models.AutoElectricoSQL.modelo == auto.modelo,
        models.AutoElectricoSQL.anio == auto.anio
    )
    existing_auto = db.scalar(stmt_check)

    if existing_auto:
        raise ValueError(f"Ya existe un auto con el modelo '{auto.modelo}' y año '{auto.anio}'")

    db_auto = models.AutoElectricoSQL(**auto.model_dump())
    db.add(db_auto)
    db.commit()
    db.refresh(db_auto)
    return db_auto


def update_auto(db: Session, auto_id: int, auto: AutoActualizado):
    """Actualiza un auto eléctrico existente."""
    stmt_get = select(models.AutoElectricoSQL).where(models.AutoElectricoSQL.id == auto_id)
    db_auto = db.scalar(stmt_get)

    if not db_auto:
        return None

    update_data = auto.model_dump(exclude_unset=True)

    # Actualización directa del objeto ORM, la forma recomendada en sesiones
    for key, value in update_data.items():
        setattr(db_auto, key, value)

    db.commit()
    db.refresh(db_auto)
    return db_auto


def delete_auto(db: Session, auto_id: int):
    """Mueve un auto al historial y lo elimina de la tabla principal."""
    stmt_get = select(models.AutoElectricoSQL).where(models.AutoElectricoSQL.id == auto_id)
    db_auto = db.scalar(stmt_get)

    if not db_auto:
        return None

    # Mover al historial
    auto_data = db_auto.__dict__.copy()
    auto_data.pop('_sa_instance_state', None)
    auto_data.pop('id', None)  # Permitir que el ID del historial se autogenere

    db_auto_eliminado = models.AutoEliminadoSQL(**auto_data)
    db.add(db_auto_eliminado)

    # Eliminar con la sentencia delete
    stmt_delete = delete(models.AutoElectricoSQL).where(models.AutoElectricoSQL.id == auto_id)
    db.execute(stmt_delete)

    db.commit()
    return db_auto_eliminado


# --------------------- OPERACIONES CARGAS ---------------------

def get_cargas(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene una lista de registros de dificultad de carga con paginación."""
    stmt = select(models.CargaSQL).offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_carga(db: Session, carga_id: int):
    """Obtiene un registro de carga por su ID."""
    stmt = select(models.CargaSQL).where(models.CargaSQL.id == carga_id)
    return db.scalar(stmt)


def get_carga_by_modelo(db: Session, modelo: str):
    """Busca registros de carga por una parte de su modelo de auto (case-insensitive)."""
    stmt = select(models.CargaSQL).where(models.CargaSQL.modelo_auto.ilike(f"%{modelo}%"))
    return db.scalars(stmt).all()


def create_carga(db: Session, carga: CargaBase):
    """Crea un nuevo registro de dificultad de carga."""
    db_carga = models.CargaSQL(**carga.model_dump())
    db.add(db_carga)
    db.commit()
    db.refresh(db_carga)
    return db_carga


def update_carga(db: Session, carga_id: int, carga: CargaActualizada):
    """Actualiza un registro de dificultad de carga existente."""
    stmt_get = select(models.CargaSQL).where(models.CargaSQL.id == carga_id)
    db_carga = db.scalar(stmt_get)

    if not db_carga:
        return None

    update_data = carga.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_carga, key, value)

    db.commit()
    db.refresh(db_carga)
    return db_carga


def delete_carga(db: Session, carga_id: int):
    """Mueve un registro de carga al historial y lo elimina de la tabla principal."""
    stmt_get = select(models.CargaSQL).where(models.CargaSQL.id == carga_id)
    db_carga = db.scalar(stmt_get)

    if not db_carga:
        return None

    # Mover al historial
    carga_data = db_carga.__dict__.copy()
    carga_data.pop('_sa_instance_state', None)
    carga_data.pop('id', None)

    db_carga_eliminada = models.CargaEliminadaSQL(**carga_data)
    db.add(db_carga_eliminada)

    # Eliminar con la sentencia delete
    stmt_delete = delete(models.CargaSQL).where(models.CargaSQL.id == carga_id)
    db.execute(stmt_delete)

    db.commit()
    return db_carga_eliminada


# --------------------- OPERACIONES ESTACIONES ---------------------

def get_estaciones(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene una lista de estaciones de carga con paginación."""
    stmt = select(models.EstacionSQL).offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_estacion(db: Session, estacion_id: int):
    """Obtiene una estación de carga por su ID."""
    stmt = select(models.EstacionSQL).where(models.EstacionSQL.id == estacion_id)
    return db.scalar(stmt)


def get_estacion_by_nombre(db: Session, nombre: str):
    """Busca estaciones de carga por una parte de su nombre (case-insensitive)."""
    stmt = select(models.EstacionSQL).where(models.EstacionSQL.nombre.ilike(f"%{nombre}%"))
    return db.scalars(stmt).all()


def create_estacion(db: Session, estacion: EstacionBase):
    """Crea una nueva estación de carga."""
    db_estacion = models.EstacionSQL(**estacion.model_dump())
    db.add(db_estacion)
    db.commit()
    db.refresh(db_estacion)
    return db_estacion


def update_estacion(db: Session, estacion_id: int, estacion: EstacionActualizada):
    """Actualiza una estación de carga existente."""
    stmt_get = select(models.EstacionSQL).where(models.EstacionSQL.id == estacion_id)
    db_estacion = db.scalar(stmt_get)

    if not db_estacion:
        return None

    update_data = estacion.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_estacion, key, value)

    db.commit()
    db.refresh(db_estacion)
    return db_estacion


def delete_estacion(db: Session, estacion_id: int):
    """Mueve una estación de carga al historial y la elimina de la tabla principal."""
    stmt_get = select(models.EstacionSQL).where(models.EstacionSQL.id == estacion_id)
    db_estacion = db.scalar(stmt_get)

    if not db_estacion:
        return None

    # Mover al historial
    estacion_data = db_estacion.__dict__.copy()
    estacion_data.pop('_sa_instance_state', None)
    estacion_data.pop('id', None)

    db_estacion_eliminada = models.EstacionEliminadaSQL(**estacion_data)
    db.add(db_estacion_eliminada)

    # Eliminar con la sentencia delete
    stmt_delete = delete(models.EstacionSQL).where(models.EstacionSQL.id == estacion_id)
    db.execute(stmt_delete)

    db.commit()
    return db_estacion_eliminada


# --------------------- OPERACIONES DE HISTORIAL (ELIMINADOS) ---------------------

# Se asume que estas funciones también requieren la conversión a select/scalars/scalar

def get_autos_eliminados(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene registros de autos eliminados con paginación."""
    stmt = select(models.AutoEliminadoSQL).offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_auto_eliminado(db: Session, auto_id: int):
    """Obtiene un auto eliminado por su ID."""
    stmt = select(models.AutoEliminadoSQL).where(models.AutoEliminadoSQL.id == auto_id)
    return db.scalar(stmt)


def get_cargas_eliminadas(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene registros de carga eliminados con paginación."""
    stmt = select(models.CargaEliminadaSQL).offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_carga_eliminada(db: Session, carga_id: int):
    """Obtiene un registro de carga eliminado por su ID."""
    stmt = select(models.CargaEliminadaSQL).where(models.CargaEliminadaSQL.id == carga_id)
    return db.scalar(stmt)


def get_estaciones_eliminadas(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene registros de estaciones eliminadas con paginación."""
    stmt = select(models.EstacionEliminadaSQL).offset(skip).limit(limit)
    return db.scalars(stmt).all()


def get_estacion_eliminada(db: Session, estacion_id: int):
    """Obtiene una estación eliminada por su ID."""
    stmt = select(models.EstacionEliminadaSQL).where(models.EstacionEliminadaSQL.id == estacion_id)
    return db.scalar(stmt)


# --------------------- OPERACIONES DE ESTADÍSTICAS (CORREGIDAS) ---------------------

def get_autos_count(db: Session) -> int:
    """Obtiene el número total de autos eléctricos."""
    # CORRECCIÓN: Usar db.scalar(select(func.count(...))) para estilo 2.0
    stmt = select(func.count(models.AutoElectricoSQL.id))
    result = db.scalar(stmt)
    return result if result else 0


def get_average_autonomia(db: Session) -> float:
    """Obtiene el promedio de autonomía de todos los autos eléctricos."""
    # CORRECCIÓN: Usar db.scalar(select(func.avg(...))) para estilo 2.0
    stmt = select(func.avg(models.AutoElectricoSQL.autonomia_km))
    result = db.scalar(stmt)
    return round(result, 2) if result else 0.0


def get_cargas_count(db: Session) -> int:
    """Obtiene el número total de registros de carga."""
    # CORRECCIÓN: Usar db.scalar(select(func.count(...))) para estilo 2.0
    stmt = select(func.count(models.CargaSQL.id))
    result = db.scalar(stmt)
    return result if result else 0


def get_estaciones_count(db: Session) -> int:
    """Obtiene el número total de estaciones de carga."""
    # CORRECCIÓN: Usar db.scalar(select(func.count(...))) para estilo 2.0
    stmt = select(func.count(models.EstacionSQL.id))
    result = db.scalar(stmt)
    return result if result else 0


# Se asume que esta función se usa en main.py y se corrige
def get_cars_by_brand_stats(db: Session) -> List[dict]:
    """Obtiene el conteo de autos por marca."""
    # CORRECCIÓN: Usar select y db.execute/fetchall
    stmt = select(
        models.AutoElectricoSQL.marca,
        func.count(models.AutoElectricoSQL.id)
    ).group_by(models.AutoElectricoSQL.marca)

    # db.execute(stmt).all() devuelve tuplas (marca, count)
    return [{"marca": brand, "count": count} for brand, count in db.execute(stmt).all()]


# Se asume que esta función se usa en main.py y se corrige
def get_charge_difficulty_distribution(db: Session) -> List[dict]:
    """Obtiene la distribución de dificultad de carga."""
    # CORRECCIÓN: Usar select y db.execute/fetchall
    stmt = select(
        models.CargaSQL.dificultad_carga,
        func.count(models.CargaSQL.id)
    ).group_by(models.CargaSQL.dificultad_carga)

    # db.execute(stmt).all() devuelve tuplas (dificultad, count)
    return [{"dificultad": diff.capitalize(), "count": count} for diff, count in db.execute(stmt).all()]


# Se asume que esta función se usa en main.py y se corrige
def get_station_power_by_connector_type_stats(db: Session) -> List[dict]:
    """Obtiene la potencia promedio de estaciones por tipo de conector."""
    # CORRECCIÓN: Usar select y db.execute/fetchall
    stmt = select(
        models.EstacionSQL.tipo_conector,
        func.avg(models.EstacionSQL.potencia_kw)
    ).group_by(models.EstacionSQL.tipo_conector)

    # db.execute(stmt).all() devuelve tuplas (tipo_conector, avg_potencia_kw)
    return [
        {"tipo_conector": ct, "avg_potencia_kw": round(ap, 2) if ap else 0}
        for ct, ap in db.execute(stmt).all()
    ]