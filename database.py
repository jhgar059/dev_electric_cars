from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
import ssl

load_dotenv()

# 1. Obtiene la URL: en Render es la de Postgres; en local, es la de SQLite del .env
# Reemplaza 'postgres://' por 'postgresql://' si es necesario para SQLAlchemy
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./default.db").replace("postgres://", "postgresql://", 1)

# --- CONFIGURACIÓN DE CONEXIÓN OPTIMIZADA ---

# Configuración de pool para PostgreSQL
connect_args = {}
pool_settings = {}
is_postgres = SQLALCHEMY_DATABASE_URL.startswith("postgresql")

if is_postgres:
    # Configuración CLAVE para el pool de conexiones en Render
    pool_settings = {
        # Reciclar la conexión cada 300 segundos (5 minutos)
        # Esto previene que conexiones viejas se queden colgadas y consuman memoria
        "pool_recycle": 300,
        # Hacer un ping antes de usar la conexión para asegurar que esté viva
        "pool_pre_ping": True,
        # Un pool de 5 a 10 es bueno para empezar con Gunicorn workers
        "pool_size": 10
    }
    # Configuración de SSL/TLS para Render
    connect_args = {
        "sslmode": "require",
    }
    print("INFO: Usando conexión PostgreSQL con pool y SSL.")
else:
    # Desarrollo Local: usa SQLite y permite hilos
    connect_args = {"check_same_thread": False}
    print("INFO: Usando conexión SQLite local.")


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    **pool_settings # Desempaquetar la configuración del pool
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia para obtener la sesión de la base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()