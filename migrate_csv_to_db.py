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
        "disponible": fila["disponible"].lower() == 'true',
        "url_imagen": fila.get("url_imagen") if fila.get("url_imagen") else None
    }


# Función para convertir tipos de datos para CargaBase
def conversion_tipo_carga(fila: dict) -> dict:
    return {
        "id": int(fila["id"]),
        "modelo": fila["modelo"],
        "tipo_autonomia": fila["tipo_autonomia"],
        "autonomia_km": float(fila["autonomia_km"]),
        "consumo_kwh_100km": float(fila["consumo_kwh_100km"]),
        "tiempo_carga_horas": float(fila["tiempo_carga_horas"]),
        "dificultad_carga": fila["dificultad_carga"],
        "requiere_instalacion_domestica": fila["requiere_instalacion_domestica"].lower() == 'true',
        "url_imagen": fila.get("url_imagen") if fila.get("url_imagen") else None
    }


# Función para convertir tipos de datos para EstacionBase
def conversion_tipo_estacion(fila: dict) -> dict:
    return {
        "id": int(fila["id"]),
        "nombre": fila["nombre"],
        "ubicacion": fila["ubicacion"],
        "tipo_conector": fila["tipo_conector"],
        "potencia_kw": float(fila["potencia_kw"]),
        "num_conectores": int(fila["num_conectores"]),
        "acceso_publico": fila["acceso_publico"].lower() == 'true',
        "horario_apertura": fila["horario_apertura"],
        "coste_por_kwh": float(fila["coste_por_kwh"]),
        "operador": fila["operador"],
        "url_imagen": fila.get("url_imagen") if fila.get("url_imagen") else None
    }


def migrar_csv_a_db(filepath: str, modelo_sql, conversion_func):
    """
    Lee un archivo CSV y migra sus datos a la tabla correspondiente en la base de datos.
    Ignora registros si ya existen con el mismo ID.
    """
    if not os.path.exists(filepath):
        logger.warning(f"⚠️ Archivo CSV no encontrado en: {filepath}. Saltando migración.")
        return

    logger.info(f"Iniciando migración desde {filepath} a la tabla {modelo_sql.__tablename__}...")

    try:
        with open(filepath, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            db = SessionLocal()  # Abre una sesión para este archivo

            try:
                for fila in reader:
                    try:
                        datos_convertidos = conversion_func(fila)

                        # Verificar si el registro ya existe usando el ID
                        registro_id = datos_convertidos.get('id')
                        if registro_id is not None:
                            # Intenta obtener el registro existente
                            existente = db.query(modelo_sql).filter(modelo_sql.id == registro_id).first()
                            if existente:
                                logger.info(
                                    f"Registro con ID {registro_id} ya existe en {modelo_sql.__tablename__}. Saltando inserción.")
                                continue  # Saltar al siguiente registro en el CSV

                        # Si no existe, crea e inserta el nuevo registro
                        instancia_modelo = modelo_sql(**datos_convertidos)
                        db.add(instancia_modelo)
                        db.commit()
                        # logger.info(f"✅ Registro {instancia_modelo.id} de {filepath} insertado en {modelo_sql.__tablename__}.")
                    except IntegrityError as ie:
                        db.rollback()  # Hacer rollback de la operación actual
                        if "unique constraint" in str(ie).lower():
                            logger.warning(
                                f"⚠️ Registro con ID {datos_convertidos.get('id', 'N/A')} ya existe en {modelo_sql.__tablename__} (UniqueViolation). Saltando.")
                        else:
                            logger.error(f"❌ Error de integridad al insertar registro de {filepath}: {ie}",
                                         exc_info=True)
                    except Exception as e:
                        db.rollback()  # Asegúrate de hacer rollback en cualquier error de fila
                        logger.error(f"❌ Error al procesar fila de {filepath}: {e}", exc_info=True)

                logger.info(f"🎉 Migración de {filepath} a {modelo_sql.__tablename__} completada (duplicados omitidos).")

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
    main()