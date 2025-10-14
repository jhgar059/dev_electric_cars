#!/usr/bin/env bash

# Hacer el script ejecutable
chmod +x build.sh

# Instalar dependencias de Python
echo "Instalando dependencias de Python..."
pip install -r requirements.txt

# Crear directorios para archivos CSV y estáticos si no existen
echo "Creando directorios 'datos', 'eliminados' y 'static/images'..."
mkdir -p datos
mkdir -p eliminados
mkdir -p static/images # ¡Esta es la línea clave que faltaba!

# Inicializar la base de datos automáticamente
echo "Inicializando la base de datos..."
python db_init.py

echo "Proceso de construcción y preparación completado."

# snippet de build.sh
# ...
# Inicializar la base de datos automáticamente
echo "Inicializando la base de datos..."
python db_init.py

# Migrar datos CSV existentes (incluyendo los de la carpeta 'eliminados')
echo "Migrando datos CSV a la base de datos..."
python migrate_csv_to_db.py
# ...