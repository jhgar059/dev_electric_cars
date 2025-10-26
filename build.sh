#!/usr/bin/env bash

# Salir inmediatamente si un comando falla
set -e

echo "--- Iniciando Proceso de Construcción para Render ---"

# 1. Asegurar la ejecución del script
chmod +x build.sh

# 2. Instalar dependencias
echo "1. Instalando dependencias de Python..."
pip install -r requirements.txt

# 3. Crear directorios (Esencial para archivos de imagen y CSV)
echo "2. Creando directorios 'datos', 'eliminados' y 'static/images'..."
mkdir -p datos
mkdir -p eliminados
mkdir -p static/images # ¡Es crucial que static/images exista antes de la migración!

# 4. Inicializar solo la estructura de la base de datos
# db_init.py debe SOLO crear las tablas, no cargar datos.
echo "3. Inicializando la estructura de la base de datos con db_init.py..."
python db_init.py

# 5. Migrar datos CSV
# Este paso es separado y explícito.
echo "4. Migrando datos CSV existentes a la base de datos con migrate_csv_to_db.py..."
python migrate_csv_to_db.py

echo "--- Proceso de Construcción Completado Exitosamente ---"