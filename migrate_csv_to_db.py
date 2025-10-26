#!/usr/bin/env python

import os
import logging
import sys
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, text, inspect
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - \"%(levelname)s\" - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("migrador")

# Importar explícitamente el motor, base y modelos
try:
    from database import engine, SessionLocal, Base
    from models_sql import (
        AutoElectricoSQL, CargaSQL, EstacionSQL,
        AutoEliminadoSQL, CargaEliminadaSQL, EstacionEliminadaSQL
    )
except ImportError as e:
    logger.error(f"❌ Error al importar dependencias de DB/Modelos: {e}")
    sys.exit(1)


# ------------------ FUNCIONES DE CONVERSIÓN (Correctas) ------------------

def conversion_tipo_auto(fila: pd.Series) -> AutoElectricoSQL:
    return AutoElectricoSQL(
        id=int(fila["id"]),
        marca=fila["marca"],
        modelo=fila["modelo"],
        anio=int(fila["anio"]),
        capacidad_bateria_kwh=float(fila["capacidad_bateria_kwh"]),
        autonomia_km=float(fila["autonomia_km"]),
        disponible=str(fila["disponible"]).lower() == "true",
        url_imagen=fila.get("url_imagen")
    )


def conversion_tipo_carga(fila: pd.Series) -> CargaSQL:
    return CargaSQL(
        id=int(fila["id"]),
        modelo_auto=fila["modelo_auto"],
        tipo_autonomia=fila["tipo_autonomia"],
        autonomia_km=float(fila["autonomia_km"]),
        consumo_kwh_100km=float(fila["consumo_kwh_100km"]),
        tiempo_carga_horas=float(fila["tiempo_carga_horas"]),
        dificultad_carga=fila["dificultad_carga"],
        requiere_instalacion_domestica=str(fila["requiere_instalacion_domestica"]).lower() == "true",
        url_imagen=fila.get("url_imagen")
    )


def conversion_tipo_estacion(fila: pd.Series) -> EstacionSQL:
    return EstacionSQL(
        id=int(fila["id"]),
        nombre=fila["nombre"],
        ubicacion=fila["ubicacion"],
        tipo_conector=fila["tipo_conector"],
        potencia_kw=float(fila["potencia_kw"]),
        num_conectores=int(fila["num_conectores"]),
        acceso_publico=str(fila["acceso_publico"]).lower() == "true",
        horario_apertura=fila["horario_apertura"],
        coste_por_kwh=float(fila["coste_por_kwh"]),
        operador=fila["operador"],
        url_imagen=fila.get("url_imagen")
    )


# ------------------ FUNCIONES DE DB (Limpieza y Secuencia) ------------------

def limpiar_tabla(db: Session, model_class, table_name: str):
    """Limpia la tabla usando TRUNCATE (PostgreSQL) para resetear el estado y evitar errores de ID."""
    try:
        # TRUNCATE es rápido y en PostgreSQL (Render) reinicia la secuencia automáticamente.
        # CASCADE se usa si hay dependencias de foreign keys.
        db.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;"))
        db.commit()
        logger.info(f"🗑️ Tabla '{table_name}' limpiada (TRUNCATE).")
    except Exception as e:
        logger.error(f"❌ Error al limpiar la tabla '{table_name}': {e}", exc_info=True)
        db.rollback()


def reset_sequence_ids(db: Session, model_class, table_name):
    """Función de respaldo para resetear la secuencia de ID si TRUNCATE falla o no se usa CASCADE."""
    try:
        max_id = db.query(func.max(model_class.id)).scalar()
        if max_id is not None:
            sequence_name = f"{table_name}_id_seq"
            # setval(sequence_name, valor, is_called)
            # is_called=True significa que el próximo valor será max_id + 1
            db.execute(text(f"SELECT setval('{sequence_name}', {max_id}, true);"))
            db.commit()
            logger.info(f"✅ Secuencia de ID para {table_name} reseteada a {max_id + 1}.")
    except Exception as e:
        logger.warning(
            f"⚠️ No se pudo resetear la secuencia de ID para {table_name} (Esto es normal si TRUNCATE RESTART IDENTITY funcionó): {e}")
        db.rollback()


# ------------------ FUNCIÓN DE MIGRACIÓN CON CHUNKING (Optimizado para Memoria) ------------------

def migrar_csv_a_db(filepath: str, ModelSQL, conversion_func):
    """
    Migra datos de un CSV a la base de datos en lotes (chunks) para ahorrar memoria.
    Esta función asume que la tabla ya ha sido limpiada (TRUNCATE) previamente.
    """
    if not os.path.exists(filepath):
        logger.warning(f"⚠️ Archivo no encontrado: {filepath}. Saltando.")
        return

    logger.info(f"🔄 Iniciando migración por CHUNKS para {filepath} a la tabla {ModelSQL.__tablename__}...")

    try:
        # CLAVE: usar chunksize para procesar el archivo en pequeños bloques
        chunksize = 1000
        total_inserted = 0

        # Leer el CSV en iterador de chunks
        for i, chunk in enumerate(pd.read_csv(filepath, chunksize=chunksize, encoding='utf-8', sep=',')):
            db = SessionLocal()  # Abre una nueva sesión para cada lote
            try:
                # 1. Convertir el chunk de Pandas a objetos de SQLAlchemy
                # Usar list comprehension es más eficiente que iterrows() para esta conversión.
                data_to_insert = [ModelSQL(**conversion_func(row)) for index, row in chunk.iterrows()]

                # 2. Inserción masiva del lote (más rápido que db.add() uno por uno)
                db.bulk_save_objects(data_to_insert)
                db.commit()
                total_inserted += len(data_to_insert)

            except Exception as e:
                db.rollback()
                logger.error(f"❌ Error crítico en LOTE {i + 1} de {filepath}. Revisar tipos de datos: {e}",
                             exc_info=True)
                # Si el error es crítico, paramos la migración
                raise
            finally:
                db.close()  # Cierra la sesión

        logger.info(f"✅ Migración de {filepath} completa. Total de registros insertados: {total_inserted}.")

    except Exception as e:
        logger.error(f"❌ Error fatal al leer o procesar {filepath}: {e}", exc_info=True)


# ------------------ FUNCIÓN PRINCIPAL (Lógica de Despliegue) ------------------

def main():
    """Función principal para ejecutar la migración: Limpiar, Migrar, Resetear."""
    # Asegurarse de que los directorios existan
    os.makedirs('datos', exist_ok=True)
    os.makedirs('eliminados', exist_ok=True)

    db = SessionLocal()
    try:
        # 1. LIMPIEZA CRÍTICA: TRUNCATE las tablas principales para una migración limpia
        logger.info("--- INICIANDO LIMPIEZA DE TABLAS PRINCIPALES (TRUNCATE) ---")
        limpiar_tabla(db, AutoElectricoSQL, "autos_electricos")
        limpiar_tabla(db, CargaSQL, "cargas")
        limpiar_tabla(db, EstacionSQL, "estaciones_carga")
        logger.info("--- LIMPIEZA COMPLETADA ---")

    except Exception as e:
        logger.error(f"❌ Error al preparar la base de datos para migración: {e}", exc_info=True)
        sys.exit(1)  # Detener si la limpieza falla
    finally:
        db.close()

    # 2. MIGRACIÓN DE DATOS (Las tablas eliminadas no se limpian, solo se insertan si es un primer deploy)
    try:
        logger.info("--- INICIANDO MIGRACIÓN DE DATOS PRINCIPALES ---")
        migrar_csv_a_db("datos/autos_electricos.csv", AutoElectricoSQL, conversion_tipo_auto)
        migrar_csv_a_db("datos/dificultad_carga.csv", CargaSQL, conversion_tipo_carga)
        migrar_csv_a_db("datos/estaciones_carga.csv", EstacionSQL, conversion_tipo_estacion)

        # Migrar tablas de eliminación (simplemente se insertan, no se hace TRUNCATE/limpieza)
        logger.info("--- INICIANDO MIGRACIÓN DE DATOS ELIMINADOS (Historial) ---")
        migrar_csv_a_db("eliminados/autos_eliminados.csv", AutoEliminadoSQL, conversion_tipo_auto)
        migrar_csv_a_db("eliminados/dificultad_carga_eliminados.csv", CargaEliminadaSQL, conversion_tipo_carga)
        migrar_csv_a_db("eliminados/estaciones_eliminadas.csv", EstacionEliminadaSQL, conversion_tipo_estacion)

    except Exception as e:
        logger.error(f"❌ FALLA CRÍTICA EN MIGRACIÓN. El servicio probablemente morirá con 500: {e}", exc_info=True)
        # No salimos aquí porque la aplicación puede intentar arrancar incluso con datos parciales

    logger.info("✨ Migración de CSV a DB completada.")


if __name__ == "__main__":
    main()