from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

# 1. Obtiene la URL y corrige el prefijo 'postgres://' a 'postgresql://'
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./default.db").replace("postgres://", "postgresql://", 1)

connect_args = {}
pool_settings = {}
is_postgres = SQLALCHEMY_DATABASE_URL.startswith("postgresql")

if is_postgres:
    # CONFIGURACIÓN CRÍTICA PARA RENDER (SSL y Pool)
    pool_settings = {
        "pool_recycle": 300,        # Reciclar la conexión cada 5 minutos
        "pool_pre_ping": True,      # Probar antes de usar
        "pool_size": 5              # Pool pequeño para ahorrar memoria
    }
    connect_args = {
        "sslmode": "require",       # 🔑 CLAVE para la conexión segura en Render
    }
    print("INFO: Usando conexión PostgreSQL con pool y SSL.")
else:
    # Conexión local con SQLite
    connect_args = {"check_same_thread": False}
    print("INFO: Usando conexión SQLite local.")


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