from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./test.db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "sslmode": "require"  # Requerido por Render para SSL
        },
        # ===============================================
        # PARÁMETROS CRUCIALES PARA ESTABILIDAD EN RENDER:
        # ===============================================
        pool_size=10,             # Conexiones abiertas en el pool
        max_overflow=20,          # Conexiones adicionales permitidas
        pool_recycle=3600,        # Reciclar conexiones después de 1 hora (evita conexiones muertas)
        pool_pre_ping=True        # Verificar que la conexión esté viva antes de usarla (soluciona muchos 500s)
        # ===============================================
    )
    print("INFO: Usando conexión PostgreSQL con SSL y Pool optimizado.")

elif DATABASE_URL.startswith("sqlite"):
    # Desarrollo Local (SQLite)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    print("INFO: Usando conexión SQLite local.")
else:
    # Lanza un error si la URL no es reconocida
    raise ValueError(f"URL de base de datos no compatible: {DATABASE_URL}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()