import os
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

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

# Determinar si se requiere SSL
# Si la DATABASE_URL no es localhost, asumimos que es un entorno remoto y requerimos SSL
# Esto es una heurística; ajusta si tu entorno local también usa SSL o si tu proveedor no lo requiere
if "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
else:
    engine = create_engine(DATABASE_URL)

# Crear una sesión localizada
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos declarativos
Base = declarative_base()

# Función para obtener la DB (para usar con FastAPI Depends)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Esta función es un ejemplo de conexión directa con psycopg2 y no se usa directamente en la configuración de SQLAlchemy
# pero es útil para verificar la conectividad de bajo nivel si es necesario.
def obtener_conexion():
    """Establece conexión con la base de datos en Render (o cualquier PostgreSQL)."""
    # Usar la misma DATABASE_URL que se usa para SQLAlchemy
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error al conectar con la base de datos (psycopg2): {e}")
        raise