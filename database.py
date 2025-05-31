import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

import os
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

def obtener_conexion():
    """Establece conexión con la base de datos en Render"""
    # Esta función no se usa directamente en la configuración de SQLAlchemy,
    # pero es un buen ejemplo de cómo psycopg2 podría conectarse.
    # La conexión principal se hace a través de SQLAlchemy más abajo.
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgres://usuario:contraseña@host:puerto/nombre_db')

    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Cargar variables de entorno del archivo .env
load_dotenv()

# Obtener la URL de la base de datos desde las variables de entorno.
# Si DATABASE_URL no está definida en el entorno o en .env, usará el valor por defecto (localhost).
# Asegúrate de que tu .env o tu entorno de Render tenga la URL correcta.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/electricos_db")

# Configuración para SQLAlchemy cuando el DATABASE_URL comienza con "postgres://" (necesario para Render)
# Render a veces proporciona URLs que empiezan con 'postgres://', SQLAlchemy prefiere 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL)

# Crear una sesión localizada
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Función para obtener la DB (para inyección de dependencias en FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
