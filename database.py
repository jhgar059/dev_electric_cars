from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

# Lógica para manejar 'postgres://' a 'postgresql://'
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./default.db").replace("postgres://", "postgresql://", 1)

connect_args = {}
pool_settings = {}
is_postgres = SQLALCHEMY_DATABASE_URL.startswith("postgresql")

if is_postgres:
    # Configuración CLAVE para PostgreSQL en Render
    pool_settings = {
        "pool_recycle": 300, # Reciclar la conexión cada 5 minutos
        "pool_pre_ping": True, # Probar la conexión antes de usarla
        "pool_size": 5 # Limita el número de conexiones en el pool
    }
    connect_args = {
        "sslmode": "require", # Requerido para la conexión SSL de Render
    }
else:
    # Desarrollo Local: SQLite
    connect_args = {"check_same_thread": False}


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    **pool_settings
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