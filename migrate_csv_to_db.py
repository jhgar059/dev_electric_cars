#!/usr/bin/env python

import csv
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, inspect
from sqlalchemy.orm import sessionmaker
# Importar explícitamente los modelos SQL para que Base.metadata los reconozca
from models_sql import (
    AutoElectricoSQL, CargaSQL, EstacionSQL,
    AutoEliminadoSQL, CargaEliminadaSQL, EstacionEliminadaSQL
)
from database import DATABASE_URL, Base, engine # Importar el engine y Base de database.py para consistencia

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
        "url_imagen": fila.get("url_imagen") # Usar .get() para evitar KeyError si el campo no existe
    }

# Función para convertir tipos de datos para Carga
def conversion_tipo_carga(fila: dict) -> dict:
    return {
        "id": int(fila["id"]),
        "modelo": fila["modelo"],
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

def migrar_csv_a_db(filepath: str, sql_model: type, conversion_func):
    """
    Lee un archivo CSV y migra sus datos a la tabla de la base de datos
    correspondiente, actualizando registros existentes o insertando nuevos.
    """
    if not os.path.exists(filepath):
        logger.info(f"Archivo CSV no encontrado: {filepath}. Saltando migración.")
        return

    logger.info(f"Iniciando migración desde {filepath} a la tabla '{sql_model.__tablename__}'...")
    datos_a_insertar = []
    try:
        with open(filepath, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    processed_row = conversion_func(row)
                    datos_a_insertar.append(processed_row)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Saltando fila debido a un error de formato en {filepath}: {row}. Error: {e}")
                    continue

        db = SessionLocal()
        try:
            for data in datos_a_insertar:
                # Intenta encontrar el registro por ID para actualizarlo si existe
                db_obj = db.query(sql_model).filter(sql_model.id == data['id']).first()
                if db_obj:
                    # Actualizar campos existentes
                    for key, value in data.items():
                        setattr(db_obj, key, value)
                    logger.debug(f"Actualizando registro ID {data['id']} en {sql_model.__tablename__}")
                else:
                    # Insertar nuevo registro
                    new_obj = sql_model(**data)
                    db.add(new_obj)
                    logger.debug(f"Insertando nuevo ID {data['id']} en {sql_model.__tablename__}")
            db.commit()
            logger.info(f"✅ Migración completada para {filepath}. {len(datos_a_insertar)} registros procesados.")

        except Exception as e:
            db.rollback() # Revertir si hay algún error
            logger.error(f"❌ Error durante la migración de {filepath} a la base de datos: {e}", exc_info=True)
        finally:
            db.close()

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
    # Nota: Asegúrate de que este CSV exista si lo usas
    migrar_csv_a_db("eliminados/estaciones_eliminadas.csv", EstacionEliminadaSQL, conversion_tipo_estacion)

if __name__ == "__main__":
    main()