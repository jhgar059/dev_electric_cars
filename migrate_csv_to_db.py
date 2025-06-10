#!/usr/bin/env python

import csv
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError  # Importa IntegrityError

# Importar explícitamente los modelos SQL para que Base.metadata los reconozca
from models_sql import (
    AutoElectricoSQL, CargaSQL, EstacionSQL,
    AutoEliminadoSQL, CargaEliminadaSQL, EstacionEliminadaSQL
)
from database import DATABASE_URL, Base, engine  # Importar el engine y Base de database.py para consistencia

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - \"%(levelname)s\" - %(message)s"
)
logger = logging.getLogger("migrador")

# Crear una sesión local para las operaciones de migración
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger.info(f"Conectando a la base de datos para migración...")

# Definir la metadata de la base de datos
metadata = MetaData()


# Función para convertir tipos de datos para AutoElectrico
def conversion_tipo_auto(fila: dict) -> dict:
    return {
        "id": int(fila["id"]),
        "marca": fila["marca"],
        "modelo": fila["modelo"],
        "anio": int(fila["anio"]),
        "capacidad_bateria_kwh": float(fila["capacidad_bateria_kwh"]),
        "autonomia_km": float(fila["autonomia_km"]),
        "disponible": fila["disponible"].lower() == "true",
        "url_imagen": fila.get("url_imagen")  # Usar .get para que no falle si la columna no existe
    }


# Función para convertir tipos de datos para Carga
def conversion_tipo_carga(fila: dict) -> dict:
    return {
        "id": int(fila["id"]),
        "modelo_auto": fila["modelo_auto"],
        "tipo_autonomia": fila["tipo_autonomia"],
        "autonomia_km": float(fila["autonomia_km"]),
        "consumo_kwh_100km": float(fila["consumo_kwh_100km"]),
        "tiempo_carga_horas": float(fila["tiempo_carga_horas"]),
        "dificultad_carga": fila["dificultad_carga"],
        "requiere_instalacion_domestica": fila["requiere_instalacion_domestica"].lower() == "true",
        "url_imagen": fila.get("url_imagen")
    }


# Función para convertir tipos de datos para Estacion
def conversion_tipo_estacion(fila: dict) -> dict:
    return {
        "id": int(fila["id"]),
        "nombre": fila["nombre"],
        "ubicacion": fila["ubicacion"],
        "tipo_conector": fila["tipo_conector"],
        "potencia_kw": float(fila["potencia_kw"]),
        "num_conectores": int(fila["num_conectores"]),
        "acceso_publico": fila["acceso_publico"].lower() == "true",
        "horario_apertura": fila["horario_apertura"],
        "coste_por_kwh": float(fila["coste_por_kwh"]),
        "operador": fila["operador"],
        "url_imagen": fila.get("url_imagen")
    }


def migrar_csv_a_db(filepath: str, sql_model: Base, conversion_func):
    """
    Migra datos desde un archivo CSV a una tabla de la base de datos.
    :param filepath: La ruta al archivo CSV.
    :param sql_model: El modelo SQLAlchemy (ej. AutoElectricoSQL) al que se migrarán los datos.
    :param conversion_func: Una función que convierte cada fila del CSV (diccionario)
                            al formato esperado por el modelo SQL.
    """
    if not os.path.exists(filepath):
        logger.info(f"ℹ️ Archivo CSV no encontrado: {filepath}. Saltando migración para este archivo.")
        return

    logger.info(f"🔄 Iniciando migración de {filepath} a la tabla {sql_model.__tablename__}...")
    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            datos = [conversion_func(fila) for fila in reader]

            db = SessionLocal()
            try:
                inspector = inspect(engine)
                table_name = sql_model.__tablename__

                # Obtener los IDs existentes en la tabla para evitar duplicados
                existing_ids = set()
                if inspector.has_table(table_name):
                    existing_ids = set(db.query(sql_model.id).all())

                nuevos_registros = 0
                registros_actualizados = 0

                for dato in datos:
                    instance_id = dato.get("id")
                    if instance_id and (instance_id,) in existing_ids:  # Tuple comparison for set
                        # Si el registro ya existe, actualiza
                        db_instance = db.query(sql_model).filter(sql_model.id == instance_id).first()
                        if db_instance:
                            for key, value in dato.items():
                                setattr(db_instance, key, value)
                            registros_actualizados += 1
                        else:
                            logger.warning(
                                f"Advertencia: El ID {instance_id} existe en el conjunto de IDs, pero no se encontró la instancia para actualizar. Esto no debería pasar.")
                    else:
                        # Si no existe, crea uno nuevo
                        db_instance = sql_model(**dato)
                        db.add(db_instance)
                        nuevos_registros += 1

                db.commit()
                logger.info(
                    f"✅ Migración de {filepath} completada. {nuevos_registros} nuevos registros, {registros_actualizados} registros actualizados.")

            except IntegrityError as e:
                db.rollback()
                logger.error(
                    f"❌ Error de integridad al migrar {filepath}. Posible duplicado de ID o dato inválido. Detalles: {e}",
                    exc_info=True)
                logger.error(
                    f"Revise el CSV: {filepath} para datos duplicados en la columna 'id' o datos inconsistentes.")
            except Exception as e:
                db.rollback()  # Revertir si hay algún error
                logger.error(f"❌ Error durante la migración de {filepath} a la base de datos: {e}", exc_info=True)
            finally:
                db.close()  # Asegúrate de cerrar la sesión

    except Exception as e:
        logger.error(f"❌ Error al leer el archivo CSV {filepath}: {e}")


def main():
    """Función principal para ejecutar la migración"""
    # Asegurarse de que los directorios 'datos' y 'eliminados' existan
    os.makedirs('datos', exist_ok=True)
    os.makedirs('eliminados', exist_ok=True)

    # Migrar datos de autos (principales y eliminados)
    migrar_csv_a_db("datos/autos_electricos.csv", AutoElectricoSQL, conversion_tipo_auto)
    migrar_csv_a_db("eliminados/autos_eliminados.csv", AutoEliminadoSQL, conversion_tipo_auto)

    # Migrar datos de cargas (principales y eliminados)
    migrar_csv_a_db("datos/dificultad_carga.csv", CargaSQL, conversion_tipo_carga)
    # Nota: Asegúrate de que este CSV exista si lo usas
    migrar_csv_a_db("eliminados/dificultad_carga_eliminados.csv", CargaEliminadaSQL, conversion_tipo_carga)

    # Migrar datos de estaciones (principales y eliminados)
    migrar_csv_a_db("datos/estaciones_carga.csv", EstacionSQL, conversion_tipo_estacion)
    migrar_csv_a_db("eliminados/estaciones_eliminadas.csv", EstacionEliminadaSQL, conversion_tipo_estacion)


if __name__ == "__main__":
    logger.info("Iniciando script de migración CSV a DB...")
    main()
    logger.info("Migración CSV a DB completada.")