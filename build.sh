#!/usr/bin/env bash

# Hacer el script ejecutable
chmod +x build.sh

# Instalar dependencias de Python
pip install -r requirements.txt

# Crear directorio para archivos CSV si no existe
mkdir -p datos
mkdir -p eliminados