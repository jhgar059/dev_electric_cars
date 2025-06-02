# db_init.py
# !/usr/bin/env python3

import os
import sys
import logging
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
# Importa explícitamente todas las clases de modelos que están definidas en models_sql.py
# Esto asegura que Base.metadata "vea" todas las tablas.
from models_sql import (
    AutoElectricoSQL, AutoEliminadoSQL,
    CargaSQL, CargaEliminadaSQL,
    EstacionSQL, EstacionEliminadaSQL
)
# Los modelos Pydantic no son necesarios para crear tablas, pero los mantengo si tuvieras otros usos.
from modelos import AutoElectrico, CargaBase, EstacionBase

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("db_init")


def verificar_conexion():
    """Verifica la conexión a la base de datos"""
    try:
        conn = engine.connect()
        conn.close()
        logger.info("✅ Conexión a base de datos exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Error de conexión a la base de datos: {e}")
        return False


def crear_tablas():
    """Crea las tablas en la base de datos si no existen, incluyendo las de 'eliminados'."""
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        # Define la lista de todas las tablas que deberían existir
        required_tables = [
            AutoElectricoSQL.__tablename__,
            AutoEliminadoSQL.__tablename__,
            CargaSQL.__tablename__,
            CargaEliminadaSQL.__tablename__,
            EstacionSQL.__tablename__,
            EstacionEliminadaSQL.__tablename__
        ]

        # Comprueba si TODAS las tablas requeridas ya existen
        if all(table_name in existing_tables for table_name in required_tables):
            logger.info("ℹ️ Todas las tablas de la base de datos ya existen. No se recrearán.")
            return True
        else:
            logger.info("Creando tablas de la base de datos...")
            # Aquí es donde Base.metadata.create_all() usa las clases importadas para crear las tablas
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Tablas creadas exitosamente.")
            return True
    except Exception as e:
        logger.error(f"❌ Error al crear tablas: {e}", exc_info=True)  # Añadir exc_info para ver el traceback completo
        return False


def insertar_datos_de_prueba(db: Session):
    """Inserta algunos datos de prueba si las tablas están vacías."""
    if db.query(AutoElectricoSQL).count() == 0:
        logger.info("Insertando datos de prueba en la tabla 'autos_electricos'...")
        db.add(AutoElectricoSQL(marca="BMW", modelo="iX", anio=2023, capacidad_bateria_kwh=105.2, autonomia_km=630.0,
                                disponible=True, url_imagen="https://example.com/bmw_ix.jpg"))
        db.add(AutoElectricoSQL(marca="Audi", modelo="e-tron GT", anio=2022, capacidad_bateria_kwh=93.4,
                                autonomia_km=488.0, disponible=True, url_imagen="https://example.com/audi_etron.jpg"))
        db.commit()
        logger.info("Datos de prueba para autos insertados.")
    else:
        logger.info("La tabla 'autos_electricos' ya contiene datos. No se insertarán datos de prueba.")

    if db.query(CargaSQL).count() == 0:
        logger.info("Insertando datos de prueba en la tabla 'dificultad_carga'...")
        db.add(CargaSQL(modelo="BMW i3", tipo_autonomia="urbana", autonomia_km=250.0, consumo_kwh_100km=13.5,
                        tiempo_carga_horas=6.0, dificultad_carga="baja", requiere_instalacion_domestica=False,
                        url_imagen="https://example.com/bmw_i3_charge.jpg"))
        db.add(
            CargaSQL(modelo="Mercedes-Benz EQS", tipo_autonomia="autopista", autonomia_km=600.0, consumo_kwh_100km=20.0,
                     tiempo_carga_horas=1.0, dificultad_carga="alta", requiere_instalacion_domestica=True,
                     url_imagen="https://example.com/eqs_charge.jpg"))
        db.commit()
        logger.info("Datos de prueba para cargas insertados.")
    else:
        logger.info("La tabla 'dificultad_carga' ya contiene datos. No se insertarán datos de prueba.")

    if db.query(EstacionSQL).count() == 0:
        logger.info("Insertando datos de prueba en la tabla 'estaciones_carga'...")
        db.add(EstacionSQL(nombre="ChargePoint City", ubicacion="Centro Histórico", tipo_conector="Tipo 2",
                           potencia_kw=22.0, num_conectores=8, acceso_publico=True, horario_apertura="24/7",
                           coste_por_kwh=0.25, operador="ChargePoint",
                           url_imagen="https://example.com/chargepoint.jpg"))
        db.add(EstacionSQL(nombre="Ionity Highway", ubicacion="Autopista Sur KM 50", tipo_conector="CCS",
                           potencia_kw=350.0, num_conectores=4, acceso_publico=True, horario_apertura="24/7",
                           coste_por_kwh=0.45, operador="Ionity", url_imagen="https://example.com/ionity.jpg"))
        db.commit()
        logger.info("Datos de prueba para estaciones insertados.")
    else:
        logger.info("La tabla 'estaciones_carga' ya contiene datos. No se insertarán datos de prueba.")


def listar_datos(db: Session):
    """Lista algunos datos para verificar que se han cargado."""
    logger.info("\n--- Datos actuales en la base de datos ---")
    autos = db.query(AutoElectricoSQL).limit(5).all()
    if autos:
        logger.info("Autos Eléctricos:")
        for auto in autos:
            logger.info(f"  ID: {auto.id}, Marca: {auto.marca}, Modelo: {auto.modelo}, Año: {auto.anio}")
    else:
        logger.info("No hay autos eléctricos en la base de datos.")

    cargas = db.query(CargaSQL).limit(5).all()
    if cargas:
        logger.info("Registros de Dificultad de Carga:")
        for carga in cargas:
            logger.info(f"  ID: {carga.id}, Modelo: {carga.modelo}, Dificultad: {carga.dificultad_carga}")
    else:
        logger.info("No hay registros de dificultad de carga en la base de datos.")

    estaciones = db.query(EstacionSQL).limit(5).all()
    if estaciones:
        logger.info("Estaciones de Carga:")
        for estacion in estaciones:
            logger.info(f"  ID: {estacion.id}, Nombre: {estacion.nombre}, Ubicación: {estacion.ubicacion}")
    else:
        logger.info("No hay estaciones de carga en la base de datos.")

    # Listar también los eliminados (opcional)
    autos_elim = db.query(AutoEliminadoSQL).limit(5).all()
    if autos_elim:
        logger.info("Autos Eliminados (ejemplos):")
        for auto_e in autos_elim:
            logger.info(f"  ID: {auto_e.id}, Marca: {auto_e.marca}, Modelo: {auto_e.modelo} (Eliminado)")

    cargas_elim = db.query(CargaEliminadaSQL).limit(5).all()
    if cargas_elim:
        logger.info("Cargas Eliminadas (ejemplos):")
        for carga_e in cargas_elim:
            logger.info(f"  ID: {carga_e.id}, Modelo: {carga_e.modelo} (Eliminado)")

    estaciones_elim = db.query(EstacionEliminadaSQL).limit(5).all()
    if estaciones_elim:
        logger.info("Estaciones Eliminadas (ejemplos):")
        for estacion_e in estaciones_elim:
            logger.info(f"  ID: {estacion_e.id}, Nombre: {estacion_e.nombre} (Eliminada)")


if __name__ == "__main__":
    logger.info("Iniciando proceso de inicialización de base de datos...")

    # Verificar conexión
    if not verificar_conexion():
        logger.error("❌ No se pudo establecer conexión con la base de datos. Abortando.")
        sys.exit(1)  # Salir con un código de error

    # Crear tablas (solo si no existen)
    if not crear_tablas():
        logger.error("❌ Error al crear tablas. Abortando.")
        sys.exit(1)  # Salir con un código de error

    # Insertar datos de prueba (solo si las tablas están vacías)
    db = SessionLocal()
    try:
        insertar_datos_de_prueba(db)
    finally:
        db.close()

    # Migrar datos CSV (se ejecuta SIEMPRE para asegurar que los CSV se carguen)
    # Esto es independiente de los datos de prueba y debería correr en cada despliegue si los CSV son la fuente de verdad.
    logger.info("Migrando datos CSV existentes (si los hay)...")
    try:
        # Importar migrate_csv_to_db aquí para evitar circular imports en el nivel superior
        # Esto es un truco para cuando el migrador también usa Base.metadata.create_all
        import migrate_csv_to_db

        migrate_csv_to_db.main()  # Ejecutar la función main del migrador
    except Exception as e:
        logger.error(f"❌ Error al ejecutar el script de migración CSV: {e}", exc_info=True)

    # Listar datos para verificación
    db_after_migration = SessionLocal()
    try:
        listar_datos(db_after_migration)
    finally:
        db_after_migration.close()

    logger.info("✅ Inicialización de base de datos finalizada.")