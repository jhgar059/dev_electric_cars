import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

import os
import psycopg2


def obtener_conexion():
    """Establece conexión con la base de datos en Render"""
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgres://usuario:contraseña@host:puerto/nombre_db')

    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Cargar variables de entorno
load_dotenv()

# Para desarrollo local se puede usar una variable de entorno o un valor por defecto
# En producción (Render), se usará la variable de entorno DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/electricos_db")

# Configuración para SQLAlchemy cuando el DATABASE_URL comienza con "postgres://" (necesario para Render)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL)

# Crear una sesión localizada
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Función para obtener la DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()