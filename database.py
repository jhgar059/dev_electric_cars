from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

# 1. Obtiene la URL de la variable de entorno y corrige el prefijo
# Render a veces usa 'postgres://' y SQLAlchemy requiere 'postgresql://'
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./default.db").replace("postgres://", "postgresql://", 1)

# --- CONFIGURACIÓN DE CONEXIÓN OPTIMIZADA ---
connect_args = {}
pool_settings = {}
is_postgres = SQLALCHEMY_DATABASE_URL.startswith("postgresql")

if is_postgres:
    # CLAVE 1: Configuración de pool para estabilidad y ahorro de memoria
    pool_settings = {
        "pool_recycle": 300,        # Reciclar la conexión cada 5 minutos
        "pool_pre_ping": True,      # Probar la conexión antes de usarla
        "pool_size": 5              # Límite bajo de conexiones
    }
    # CLAVE 2: Configuración de SSL/TLS para Render
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