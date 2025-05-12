#!/usr/bin/env python

import csv
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, inspect

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("migrador")

# Cargar variables de entorno
load_dotenv()

# Obtener la URL de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/electricos_db")

# Configuración para SQLAlchemy cuando el DATABASE_URL comienza con "postgres://" (necesario para Render)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

logger.info(f"Conectando a la base de datos...")

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Definir tablas adicionales para los elementos eliminados
deleted_auto = Table(
    "autos_eliminados",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("marca", String(30), nullable=False),
    Column("modelo", String(30), nullable=False),
    Column("anio", Integer, nullable=False),
    Column("capacidad_bateria_kwh", Float, nullable=False),
    Column("autonomia_km", Float, nullable=False),
    Column("disponible", Boolean, default=True)
)

deleted_carga = Table(
    "dificultad_carga_eliminados",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("modelo", String(50), nullable=False),
    Column("tipo_autonomia", String(10), nullable=False),
    Column("autonomia_km", Float, nullable=False),
    Column("consumo_kwh_100km", Float, nullable=False),
    Column("tiempo_carga_horas", Float, nullable=False),
    Column("dificultad_carga", String(5), nullable=False),
    Column("requiere_instalacion_domestica", Boolean, default=False)
)

deleted_estacion = Table(
    "estaciones_eliminadas",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", String(50), nullable=False),
    Column("ubicacion", String(100), nullable=False),
    Column("tipo_conector", String(10), nullable=False),
    Column("potencia_kw", Float, nullable=False),
    Column("num_conectores", Integer, nullable=False),
    Column("acceso_publico", Boolean, default=True),
    Column("horario_apertura", String(50), nullable=False),
    Column("coste_por_kwh", Float, nullable=False),
    Column("operador", String(50), nullable=False)
)

# Crear las tablas si no existen
logger.info("Creando tablas para elementos eliminados si no existen...")
metadata.create_all(engine)


def convertir_bool(valor):
    """Convierte una cadena de texto a booleano"""
    if isinstance(valor, str):
        return valor.lower() == "true"
    return valor


def migrar_csv_a_db(archivo_csv, tabla, conversion_tipos):
    """Migra los datos de un archivo CSV a una tabla en la base de datos"""
    try:
        logger.info(f"Migrando datos de {archivo_csv} a tabla {tabla.name}...")
        with open(archivo_csv, 'r', newline='') as f:
            reader = csv.DictReader(f)
            with engine.connect() as conn:
                for row in reader:
                    # Convertir tipos según la función proporcionada
                    datos = conversion_tipos(row)
                    # Verificar si ya existe un registro con el mismo ID
                    stmt = tabla.select().where(tabla.c.id == datos["id"])
                    result = conn.execute(stmt).fetchone()
                    if not result:
                        # Si no existe, insertar
                        conn.execute(tabla.insert().values(**datos))
        logger.info(f"Migración de {archivo_csv} completada con éxito")
        return True
    except Exception as e:
        logger.error(f"Error al migrar {archivo_csv}: {str(e)}")
        return False


def conversion_tipo_auto(row):
    """Convierte los tipos de datos para la tabla de autos"""
    return {
        "id": int(row["id"]),
        "marca": row["marca"],
        "modelo": row["modelo"],
        "anio": int(row["anio"]),
        "capacidad_bateria_kwh": float(row["capacidad_bateria_kwh"]),
        "autonomia_km": float(row["autonomia_km"]),
        "disponible": convertir_bool(row["disponible"])
    }


def conversion_tipo_carga(row):
    """Convierte los tipos de datos para la tabla de cargas"""
    return {
        "id": int(row["id"]),
        "modelo": row["modelo"],
        "tipo_autonomia": row["tipo_autonomia"],
        "autonomia_km": float(row["autonomia_km"]),
        "consumo_kwh_100km": float(row["consumo_kwh_100km"]),
        "tiempo_carga_horas": float(row["tiempo_carga_horas"]),
        "dificultad_carga": row["dificultad_carga"],
        "requiere_instalacion_domestica": convertir_bool(row["requiere_instalacion_domestica"])
    }


def conversion_tipo_estacion(row):
    """Convierte los tipos de datos para la tabla de estaciones"""
    return {
        "id": int(row["id"]),
        "nombre": row["nombre"],
        "ubicacion": row["ubicacion"],
        "tipo_conector": row["tipo_conector"],
        "potencia_kw": float(row["potencia_kw"]),
        "num_conectores": int(row["num_conectores"]),
        "acceso_publico": convertir_bool(row["acceso_publico"]),
        "horario_apertura": row["horario_apertura"],
        "coste_por_kwh": float(row["coste_por_kwh"]),
        "operador": row["operador"]
    }


def main():
    """Función principal para ejecutar la migración"""
    # Obtener referencia a las tablas existentes
    inspector = inspect(engine)
    existentes = inspector.get_table_names()

    logger.info(f"Tablas existentes en la base de datos: {existentes}")

    # Tablas principales (deben ya existir según tu código)
    auto_table = Table("autos_electricos", metadata, autoload_with=engine)
    carga_table = Table("dificultad_carga", metadata, autoload_with=engine)
    estacion_table = Table("estaciones_carga", metadata, autoload_with=engine)

    # Migrar datos de autos
    migrar_csv_a_db("datos/autos_electricos.csv", auto_table, conversion_tipo_auto)
    migrar_csv_a_db("eliminados/autos_eliminados.csv", deleted_auto, conversion_tipo_auto)

    # Migrar datos de cargas
    migrar_csv_a_db("datos/dificultad_carga.csv", carga_table, conversion_tipo_carga)
    migrar_csv_a_db("eliminados/dificultad_carga_eliminados.csv", deleted_carga, conversion_tipo_carga)

    # Migrar datos de estaciones
    migrar_csv_a_db("datos/estaciones_carga.csv", estacion_table, conversion_tipo_estacion)
    migrar_csv_a_db("eliminados/estaciones_eliminadas.csv", deleted_estacion, conversion_tipo_estacion)

    logger.info("Proceso de migración completado exitosamente")


if __name__ == "__main__":
    main()