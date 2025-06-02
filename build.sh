#!/usr/bin/env bash

# Hacer el script ejecutable
chmod +x build.sh

# Instalar dependencias de Python
echo "Instalando dependencias de Python..."
pip install -r requirements.txt

# Crear directorio para archivos CSV si no existe
echo "Creando directorios 'datos' y 'eliminados'..."
mkdir -p datos
mkdir -p eliminados

# Inicializar la base de datos automáticamente
echo "Inicializando la base de datos..."
python db_init.py

# Migrar datos CSV existentes (incluyendo los de la carpeta 'eliminados')
echo "Migrando datos CSV a la base de datos..."
python migrate_csv_to_db.py

echo "Proceso de construcción y preparación completado."