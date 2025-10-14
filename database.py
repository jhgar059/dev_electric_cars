from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
# ... otras importaciones ...

load_dotenv()

# 1. Obtiene la URL: en Render es la de Postgres; en local, es la de SQLite del .env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    # Fallback si no hay variable (debería ser la de SQLite si .env está configurado)
    SQLALCHEMY_DATABASE_URL = "sqlite:///./default.db"

# --- LÓGICA DE CONEXIÓN CONDICIONAL Y SSL ---

if SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
    # Render usa PostgreSQL: aplica SSL
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={
            "sslmode": "require"  # Clave para Render
        }
    )
    print("INFO: Usando conexión PostgreSQL con SSL.")

elif SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # Desarrollo Local: usa SQLite y permite hilos
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    print("INFO: Usando conexión SQLite local.")

load_dotenv()


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

# Configuración para la base de datos (SQLite para desarrollo local, PostgreSQL para Render)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Render a veces usa 'postgres://' en lugar de 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    # Necesario para SQLite con FastAPI (un hilo por solicitud)
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Configuración para la base de datos (SQLite para desarrollo local, PostgreSQL para Render)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Render a veces usa 'postgres://' en lugar de 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    # Necesario para SQLite con FastAPI (un hilo por solicitud)
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

    if SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
        # Render usa PostgreSQL: aplica SSL
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={
                "sslmode": "require"  # Clave para Render
            }
        )
        print("INFO: Usando conexión PostgreSQL con SSL.")
    # ...