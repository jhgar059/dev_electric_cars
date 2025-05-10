#!/usr/bin/env python3
"""
Script para inicializar la base de datos y crear datos de prueba
Ejecutar con: python db_init.py
"""

import os
import sys
import logging
from sqlalchemy import inspect
from database import engine, Base, SessionLocal
import models_sql
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
    """Crea las tablas en la base de datos"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas exitosamente")

        # Mostrar tablas creadas
        inspector = inspect(engine)
        tablas = inspector.get_table_names()
        logger.info(f"Tablas disponibles: {tablas}")

        return True
    except Exception as e:
        logger.error(f"❌ Error al crear tablas: {e}")
        return False


def insertar_datos_prueba():
    """Inserta datos de prueba en la base de datos"""
    try:
        db = SessionLocal()

        # Verificar si ya hay datos
        autos_count = db.query(models_sql.AutoElectricoSQL).count()
        cargas_count = db.query(models_sql.CargaSQL).count()
        estaciones_count = db.query(models_sql.EstacionSQL).count()

        if autos_count > 0 or cargas_count > 0 or estaciones_count > 0:
            logger.info(
                f"📊 La base de datos ya contiene datos: {autos_count} autos, {cargas_count} cargas, {estaciones_count} estaciones")
            return True

        # Autos de prueba
        autos = [
            models_sql.AutoElectricoSQL(
                marca="Tesla",
                modelo="Model 3",
                anio=2023,
                capacidad_bateria_kwh=75.0,
                autonomia_km=450.0,
                disponible=True
            ),
            models_sql.AutoElectricoSQL(
                marca="Volkswagen",
                modelo="ID.4",
                anio=2022,
                capacidad_bateria_kwh=82.0,
                autonomia_km=420.0,
                disponible=True
            ),
            models_sql.AutoElectricoSQL(
                marca="Hyundai",
                modelo="Ioniq 5",
                anio=2023,
                capacidad_bateria_kwh=72.6,
                autonomia_km=481.0,
                disponible=True
            )
        ]

        # Datos de carga
        cargas = [
            models_sql.CargaSQL(
                modelo="Tesla Model 3",
                tipo_autonomia="mixta",
                autonomia_km=450.0,
                consumo_kwh_100km=16.5,
                tiempo_carga_horas=8.0,
                dificultad_carga="baja",
                requiere_instalacion_domestica=False
            ),
            models_sql.CargaSQL(
                modelo="Volkswagen ID.4",
                tipo_autonomia="urbana",
                autonomia_km=420.0,
                consumo_kwh_100km=18.2,
                tiempo_carga_horas=9.5,
                dificultad_carga="media",
                requiere_instalacion_domestica=True
            ),
            models_sql.CargaSQL(
                modelo="Hyundai Ioniq 5",
                tipo_autonomia="autopista",
                autonomia_km=481.0,
                consumo_kwh_100km=19.1,
                tiempo_carga_horas=6.2,
                dificultad_carga="baja",
                requiere_instalacion_domestica=False
            )
        ]

        # Estaciones de carga
        estaciones = [
            models_sql.EstacionSQL(
                nombre="Supercharger Madrid",
                ubicacion="Calle Gran Vía 1, Madrid",
                tipo_conector="Tesla",
                potencia_kw=150.0,
                num_conectores=8,
                acceso_publico=True,
                horario_apertura="24/7",
                coste_por_kwh=0.45,
                operador="Tesla"
            ),
            models_sql.EstacionSQL(
                nombre="Ionity Barcelona",
                ubicacion="Avinguda Diagonal 100, Barcelona",
                tipo_conector="CCS",
                potencia_kw=350.0,
                num_conectores=6,
                acceso_publico=True,
                horario_apertura="24/7",
                coste_por_kwh=0.79,
                operador="Ionity"
            ),
            models_sql.EstacionSQL(
                nombre="Endesa X Valencia",
                ubicacion="Plaza del Ayuntamiento 5, Valencia",
                tipo_conector="Tipo 2",
                potencia_kw=22.0,
                num_conectores=4,
                acceso_publico=True,
                horario_apertura="08:00-22:00",
                coste_por_kwh=0.39,
                operador="Endesa X"
            )
        ]

        # Añadir a la sesión
        for auto in autos:
            db.add(auto)

        for carga in cargas:
            db.add(carga)

        for estacion in estaciones:
            db.add(estacion)

        # Guardar todos los cambios
        db.commit()

        logger.info(
            f"✅ Datos de prueba insertados: {len(autos)} autos, {len(cargas)} cargas, {len(estaciones)} estaciones")

        # Verificar los datos insertados
        nuevo_autos_count = db.query(models_sql.AutoElectricoSQL).count()
        nuevo_cargas_count = db.query(models_sql.CargaSQL).count()
        nuevo_estaciones_count = db.query(models_sql.EstacionSQL).count()

        logger.info(
            f"📊 Total en base de datos: {nuevo_autos_count} autos, {nuevo_cargas_count} cargas, {nuevo_estaciones_count} estaciones")

        db.close()
        return True
    except Exception as e:
        logger.error(f"❌ Error al insertar datos de prueba: {e}")
        return False


def listar_datos():
    """Lista algunos datos para verificar que se han insertado correctamente"""
    try:
        db = SessionLocal()

        autos = db.query(models_sql.AutoElectricoSQL).all()
        logger.info("📋 AUTOS ELÉCTRICOS:")
        for auto in autos:
            logger.info(f"  ID: {auto.id}, Marca: {auto.marca}, Modelo: {auto.modelo}, Año: {auto.anio}")

        cargas = db.query(models_sql.CargaSQL).all()
        logger.info("📋 DATOS DE CARGA:")
        for carga in cargas:
            logger.info(f"  ID: {carga.id}, Modelo: {carga.modelo}, Dificultad: {carga.dificultad_carga}")

        estaciones = db.query(models_sql.EstacionSQL).all()
        logger.info("📋 ESTACIONES DE CARGA:")
        for estacion in estaciones:
            logger.info(f"  ID: {estacion.id}, Nombre: {estacion.nombre}, Operador: {estacion.operador}")

        db.close()
        return True
    except Exception as e:
        logger.error(f"❌ Error al listar datos: {e}")
        return False


def main():
    """Función principal que ejecuta todas las operaciones"""
    logger.info("🚀 Iniciando inicialización de base de datos...")

    # Verificar conexión
    if not verificar_conexion():
        logger.error("❌ No se pudo establecer conexión con la base de datos. Abortando.")
        return

    # Crear tablas
    if not crear_tablas():
        logger.error("❌ Error al crear tablas. Abortando.")
        return

    # Insertar datos de prueba
    if not insertar_datos_prueba():
        logger.error("❌ Error al insertar datos de prueba.")

    # Listar datos para verificar
    listar_datos()

    logger.info("✅ Proceso de inicialización completado.")


if __name__ == "__main__":
    main()