from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
import sys
import logging

# Configuración de Logging para ver si esto es el punto de falla
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("DB_FATAL_FIX")

load_dotenv()

# --- 1. PREPARACIÓN CRÍTICA DE LA URL (Debe ser 'postgresql://') ---
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    logger.error("❌ FATAL: Variable de entorno DATABASE_URL no encontrada.")
    # Usar SQLite como fallback si falla, pero el despliegue de Render fallará
    SQLALCHEMY_DATABASE_URL = "sqlite:///./default.db"

# Render a veces usa 'postgres://' en lugar de 'postgresql://'
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("URL corregida a postgresql://")

# --- 2. CONFIGURACIÓN DEL ENGINE (EL PUNTO DE CRASH MÁS COMÚN) ---

connect_args = {}
pool_settings = {}
Base = declarative_base() # Definir Base aquí para que sea consistente

if SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
    # CONFIGURACIÓN OBLIGATORIA PARA RENDER (SSL, Memoria, Robustez)
    pool_settings = {
        "pool_recycle": 300,        # Reciclar la conexión cada 5 minutos
        "pool_pre_ping": True,      # Probar antes de usar
        "pool_size": 5              # Pool pequeño para ahorrar memoria
    }
    connect_args = {
        # 🔑 CLAVE: Forzar el SSL, la ausencia de este argumento MATA la conexión
        "sslmode": "require",
    }
    logger.info("✅ PostgreSQL detectado. Aplicando SSL y pool settings.")
elif SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # Conexión local con SQLite
    connect_args = {"check_same_thread": False}
    logger.info("⚠️ SQLite detectado. Modo desarrollo local.")


# --- 3. CREACIÓN DEL MOTOR ---
try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args=connect_args,
        **pool_settings
    )
    logger.info("✅ Engine de SQLAlchemy creado exitosamente.")
except Exception as e:
    logger.critical(f"❌ FATAL CRASH: Fallo al crear el Engine de DB: {e}", exc_info=True)
    # Re-lanzar o terminar para que Render lo registre
    sys.exit(1)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()