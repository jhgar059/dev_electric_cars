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
    """Crea las tablas en la base de datos si no existen."""
    logger.info("Intentando crear tablas en la base de datos...")
    try:
        # Base.metadata.create_all creará todas las tablas definidas en los modelos
        # que heredan de Base. Asegúrate de que todos tus modelos SQL estén importados
        # en este archivo o en un archivo que sea importado por este.
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas o ya existentes.")
        return True
    except Exception as e:
        logger.error(f"❌ Error al crear tablas: {e}", exc_info=True)
        return False


def is_db_empty(db: Session) -> bool:
    """Verifica si alguna de las tablas principales está vacía."""
    inspector = inspect(engine)
    # Comprobar si las tablas existen y si tienen datos
    if not inspector.has_table("autos_electricos") or db.query(AutoElectricoSQL).count() == 0:
        return True
    if not inspector.has_table("cargas") or db.query(CargaSQL).count() == 0:
        return True
    if not inspector.has_table("estaciones_carga") or db.query(EstacionSQL).count() == 0:
        return True
    return False


def insertar_datos_de_prueba(db: Session):
    """Inserta datos de prueba si la base de datos está vacía."""
    if is_db_empty(db):
        logger.info("Base de datos vacía. Insertando datos de prueba...")

        # Datos de prueba para AutoElectrico
        autos_data = [
            AutoElectrico(
                marca="Tesla",
                modelo="Model 3",
                anio=2023,
                capacidad_bateria_kwh=75.0,
                autonomia_km=500.0,
                disponible=True,
                url_imagen="/static/images/tesla_model_3.jpg"
            ),
            AutoElectrico(
                marca="Hyundai",
                modelo="Kona Electric",
                anio=2022,
                capacidad_bateria_kwh=64.0,
                autonomia_km=484.0,
                disponible=True,
                url_imagen="/static/images/hyundai_kona.jpg"
            ),
            AutoElectrico(
                marca="Nissan",
                modelo="Leaf",
                anio=2021,
                capacidad_bateria_kwh=40.0,
                autonomia_km=270.0,
                disponible=False,
                url_imagen="/static/images/nissan_leaf.jpg"
            )
        ]

        # Datos de prueba para Carga (usando CargaBase para la entrada inicial)
        cargas_data = [
            CargaBase(
                modelo_auto="Tesla Model 3",
                tipo_autonomia="EPA",
                autonomia_km=500.0,
                consumo_kwh_100km=15.0,
                tiempo_carga_horas=8.0,
                dificultad_carga="baja",
                requiere_instalacion_domestica=False,
                url_imagen="/static/images/carga_tesla.jpg"
            ),
            CargaBase(
                modelo_auto="Hyundai Kona Electric",
                tipo_autonomia="WLTP",
                autonomia_km=484.0,
                consumo_kwh_100km=14.7,
                tiempo_carga_horas=7.0,
                dificultad_carga="media",
                requiere_instalacion_domestica=True,
                url_imagen="/static/images/carga_kona.jpg"
            ),
            CargaBase(
                modelo_auto="Nissan Leaf",
                tipo_autonomia="EPA",
                autonomia_km=270.0,
                consumo_kwh_100km=17.0,
                tiempo_carga_horas=6.0,
                dificultad_carga="baja",
                requiere_instalacion_domestica=False,
                url_imagen="/static/images/carga_leaf.jpg"
            )
        ]

        # Datos de prueba para Estacion (usando EstacionBase para la entrada inicial)
        estaciones_data = [
            EstacionBase(
                nombre="Supercharger Bogotá",
                ubicacion="Calle 100 # 19-51, Bogotá",
                tipo_conector="Tesla",
                potencia_kw=250.0,
                num_conectores=12,
                acceso_publico=True,
                horario_apertura="24/7",
                coste_por_kwh=0.25,
                operador="Tesla",
                url_imagen="/static/images/estacion_tesla.jpg"
            ),
            EstacionBase(
                nombre="Celsia Conectado Medellín",
                ubicacion="Carrera 43A # 11-50, Medellín",
                tipo_conector="CCS",
                potencia_kw=50.0,
                num_conectores=4,
                acceso_publico=True,
                horario_apertura="L-D 8:00-20:00",
                coste_por_kwh=0.20,
                operador="Celsia",
                url_imagen="/static/images/estacion_celsia.jpg"
            ),
            EstacionBase(
                nombre="EPM Punto de Carga Cali",
                ubicacion="Avenida 3N # 47-20, Cali",
                tipo_conector="Tipo 2",
                potencia_kw=22.0,
                num_conectores=2,
                acceso_publico=False,
                horario_apertura="L-V 9:00-17:00",
                coste_por_kwh=0.18,
                operador="EPM",
                url_imagen="/static/images/estacion_epm.jpg"
            )
        ]

        try:
            for auto in autos_data:
                db_auto = AutoElectricoSQL(**auto.model_dump())
                db.add(db_auto)
            for carga in cargas_data:
                db_carga = CargaSQL(**carga.model_dump())
                db.add(db_carga)
            for estacion in estaciones_data:
                db_estacion = EstacionSQL(**estacion.model_dump())
                db.add(db_estacion)

            db.commit()
            logger.info("✅ Datos de prueba insertados exitosamente.")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error al insertar datos de prueba: {e}", exc_info=True)
    else:
        logger.info("Base de datos no está vacía. Saltando inserción de datos de prueba.")


def listar_datos_para_verificacion(db: Session):
    """Lista algunos datos de cada tabla para verificar su contenido."""
    logger.info("\n--- Verificación de datos en la base de datos ---")

    autos = db.query(AutoElectricoSQL).limit(5).all()
    logger.info(f"Autos Eléctricos ({len(autos)} encontrados, mostrando los primeros 5):")
    for auto in autos:
        logger.info(f"  ID: {auto.id}, Marca: {auto.marca}, Modelo: {auto.modelo}, Año: {auto.anio}")

    cargas = db.query(CargaSQL).limit(5).all()
    logger.info(f"Registros de Carga ({len(cargas)} encontrados, mostrando los primeros 5):")
    for carga in cargas:
        logger.info(f"  ID: {carga.id}, Modelo Auto: {carga.modelo_auto}, Dificultad: {carga.dificultad_carga}")

    estaciones = db.query(EstacionSQL).limit(5).all()
    logger.info(f"Estaciones de Carga ({len(estaciones)} encontrados, mostrando los primeros 5):")
    for estacion in estaciones:
        logger.info(f"  ID: {estacion.id}, Nombre: {estacion.nombre}, Ubicación: {estacion.ubicacion}")

    autos_eliminados = db.query(AutoEliminadoSQL).limit(5).all()
    logger.info(f"Autos Eliminados ({len(autos_eliminados)} encontrados, mostrando los primeros 5):")
    for auto_el in autos_eliminados:
        logger.info(f"  ID: {auto_el.id}, Marca: {auto_el.marca}, Modelo: {auto_el.modelo}")

    cargas_eliminadas = db.query(CargaEliminadaSQL).limit(5).all()
    logger.info(f"Cargas Eliminadas ({len(cargas_eliminadas)} encontrados, mostrando los primeros 5):")
    for carga_el in cargas_eliminadas:
        logger.info(f"  ID: {carga_el.id}, Modelo Auto: {carga_el.modelo_auto}")

    estaciones_eliminadas = db.query(EstacionEliminadaSQL).limit(5).all()
    logger.info(f"Estaciones Eliminadas ({len(estaciones_eliminadas)} encontrados, mostrando los primeros 5):")
    for estacion_el in estaciones_eliminadas:
        logger.info(f"  ID: {estacion_el.id}, Nombre: {estacion_el.nombre}")

    logger.info("--- Fin de la verificación de datos ---")


if __name__ == "__main__":
    logger.info("Iniciando proceso de inicialización de la base de datos...")

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
    db_session_for_listing = SessionLocal()
    try:
        listar_datos_para_verificacion(db_session_for_listing)
    finally:
        db_session_for_listing.close()

    logger.info("Proceso de inicialización de la base de datos completado.")