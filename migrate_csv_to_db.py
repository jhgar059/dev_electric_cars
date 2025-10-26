#!/usr/bin/env python

import os
import logging
import sys
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, text, inspect
from dotenv import load_dotenv
from typing import Callable, Type

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - \"%(levelname)s\" - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("migrador")

# Importar dependencias esenciales
try:
    from database import engine, SessionLocal, Base
    from models_sql import (
        AutoElectricoSQL, CargaSQL, EstacionSQL,
        AutoEliminadoSQL, CargaEliminadaSQL, EstacionEliminadaSQL
    )
except ImportError as e:
    logger.error(f"❌ Error al importar dependencias de DB/Modelos: {e}")
    sys.exit(1)


# ------------------ FUNCIONES DE CONVERSIÓN (Usan pd.Series y retornan dict) ------------------

def conversion_tipo_auto(fila: pd.Series) -> dict:
    return {
        "id": int(fila["id"]),
        "marca": fila["marca"],
        "modelo": fila["modelo"],
        "anio": int(fila["anio"]),
        "capacidad_bateria_kwh": float(fila["capacidad_bateria_kwh"]),
        "autonomia_km": float(fila["autonomia_km"]),
        "disponible": str(fila["disponible"]).lower() == "true",
        "url_imagen": fila.get("url_imagen")
    }


def conversion_tipo_carga(fila: pd.Series) -> dict:
    return {
        "id": int(fila["id"]),
        "modelo_auto": fila["modelo_auto"],
        "tipo_autonomia": fila["tipo_autonomia"],
        "autonomia_km": float(fila["autonomia_km"]),
        "consumo_kwh_100km": float(fila["consumo_kwh_100km"]),
        "tiempo_carga_horas": float(fila["tiempo_carga_horas"]),
        "dificultad_carga": fila["dificultad_carga"],
        "requiere_instalacion_domestica": str(fila["requiere_instalacion_domestica"]).lower() == "true",
        "url_imagen": fila.get("url_imagen")
    }


def conversion_tipo_estacion(fila: pd.Series) -> dict:
    return {
        "id": int(fila["id"]),
        "nombre": fila["nombre"],
        "ubicacion": fila["ubicacion"],
        "tipo_conector": fila["tipo_conector"],
        "potencia_kw": float(fila["potencia_kw"]),
        "num_conectores": int(fila["num_conectores"]),
        "acceso_publico": str(fila["acceso_publico"]).lower() == "true",
        "horario_apertura": fila["horario_apertura"],
        "coste_por_kwh": float(fila["coste_por_kwh"]),
        "operador": fila["operador"],
        "url_imagen": fila.get("url_imagen")
    }


# ------------------ FUNCIÓN DE DB (Limpieza) ------------------

def limpiar_tabla(db: Session, table_name: str):
    """Limpia la tabla usando TRUNCATE RESTART IDENTITY CASCADE."""
    try:
        # TRUNCATE es rápido y en PostgreSQL (Render) reinicia la secuencia.
        db.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;"))
        db.commit()
        logger.info(f"🗑️ Tabla '{table_name}' limpiada (TRUNCATE RESTART IDENTITY).")
    except Exception as e:
        logger.error(f"❌ Error al limpiar la tabla '{table_name}': {e}", exc_info=True)
        db.rollback()


# ------------------ FUNCIÓN DE MIGRACIÓN CON CHUNKING ------------------

def migrar_csv_a_db(filepath: str, ModelSQL: Type[Base], conversion_func: Callable):
    """
    Migra datos de un CSV a la base de datos en lotes (chunks) para ahorrar memoria.
    """
    if not os.path.exists(filepath):
        logger.warning(f"⚠️ Archivo no encontrado: {filepath}. Saltando.")
        return

    logger.info(f"🔄 Iniciando migración por CHUNKS para {filepath} a la tabla {ModelSQL.__tablename__}...")

    try:
        chunksize = 1000  # Lotes de 1000 filas
        total_inserted = 0

        # Leer el CSV en iterador de chunks
        for i, chunk in enumerate(pd.read_csv(filepath, chunksize=chunksize, encoding='utf-8', sep=',')):
            db = SessionLocal()  # Abre una nueva sesión para cada lote
            try:
                # 1. Convertir el chunk de Pandas a diccionarios y luego a objetos de SQLAlchemy
                data_dicts = [conversion_func(row) for index, row in chunk.iterrows()]
                data_to_insert = [ModelSQL(**d) for d in data_dicts]

                # 2. Inserción masiva del lote
                db.bulk_save_objects(data_to_insert)
                db.commit()
                total_inserted += len(data_to_insert)

            except Exception as e:
                db.rollback()
                logger.error(f"❌ Error en LOTE {i + 1} de {filepath}. Revisar tipos de datos: {e}", exc_info=True)
                raise  # Re-lanzar para detener la migración fatal
            finally:
                db.close()

        logger.info(f"✅ Migración de {filepath} completa. Total de registros insertados: {total_inserted}.")

    except Exception as e:
        logger.error(f"❌ Error fatal al leer o procesar {filepath}: {e}", exc_info=True)


# ------------------ FUNCIÓN PRINCIPAL (Lógica de Despliegue) ------------------

def main():
    """Función principal para ejecutar la migración: Limpiar, Migrar."""
    os.makedirs('datos', exist_ok=True)
    os.makedirs('eliminados', exist_ok=True)

    db = SessionLocal()
    try:
        # 1. LIMPIEZA CRÍTICA (Elimina los datos existentes para empezar limpio)
        logger.info("--- INICIANDO LIMPIEZA DE TABLAS PRINCIPALES (TRUNCATE) ---")
        limpiar_tabla(db, "autos_electricos")
        limpiar_tabla(db, "cargas")
        limpiar_tabla(db, "estaciones_carga")
        # No limpiamos las tablas de historial ('eliminados')
        logger.info("--- LIMPIEZA COMPLETADA ---")
    except Exception as e:
        logger.error(f"❌ Error al preparar la base de datos: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()

    # 2. MIGRACIÓN DE DATOS
    try:
        logger.info("--- INICIANDO MIGRACIÓN DE DATOS PRINCIPALES ---")
        migrar_csv_a_db("datos/autos_electricos.csv", AutoElectricoSQL, conversion_tipo_auto)
        migrar_csv_a_db("datos/dificultad_carga.csv", CargaSQL, conversion_tipo_carga)
        migrar_csv_a_db("datos/estaciones_carga.csv", EstacionSQL, conversion_tipo_estacion)

        # Migrar tablas de historial
        logger.info("--- INICIANDO MIGRACIÓN DE DATOS ELIMINADOS (Historial) ---")
        migrar_csv_a_db("eliminados/autos_eliminados.csv", AutoEliminadoSQL, conversion_tipo_auto)
        migrar_csv_a_db("eliminados/dificultad_carga_eliminados.csv", CargaEliminadaSQL, conversion_tipo_carga)
        migrar_csv_a_db("eliminados/estaciones_eliminadas.csv", EstacionEliminadaSQL, conversion_tipo_estacion)

    except Exception as e:
        # Si la migración falla, el log mostrará la razón, pero el build continuará.
        logger.error(f"❌ FALLA CRÍTICA EN MIGRACIÓN: {e}", exc_info=True)

    logger.info("✨ Migración de CSV a DB completada.")


if __name__ == "__main__":
    main()