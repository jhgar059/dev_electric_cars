from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import Optional
from database import Base
from datetime import datetime



# ------------------ Modelos de SQLAlchemy para la DB ------------------

class AutoElectricoSQL(Base):
    __tablename__ = "autos_electricos"

    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String(30), nullable=False)
    modelo = Column(String(30), nullable=False)
    anio = Column(Integer, nullable=False)
    capacidad_bateria_kwh = Column(Float, nullable=False)
    autonomia_km = Column(Float, nullable=False)
    disponible = Column(Boolean, default=True)
    url_imagen = Column(String(255), nullable=True) # Nuevo campo

class AutoEliminadoSQL(Base):
    __tablename__ = "autos_eliminados"

    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String(30), nullable=False)
    modelo = Column(String(30), nullable=False)
    anio = Column(Integer, nullable=False)
    capacidad_bateria_kwh = Column(Float, nullable=False)
    autonomia_km = Column(Float, nullable=False)
    disponible = Column(Boolean, default=True)
    url_imagen = Column(String(255), nullable=True) # Nuevo campo


class CargaSQL(Base):
    __tablename__ = "cargas"

    id = Column(Integer, primary_key=True, index=True)
    modelo_auto = Column(String(50), nullable=False)
    tipo_autonomia = Column(String(10), nullable=False)
    autonomia_km = Column(Float, nullable=False)
    consumo_kwh_100km = Column(Float, nullable=False)
    tiempo_carga_horas = Column(Float, nullable=False)
    dificultad_carga = Column(String(10), nullable=False) # 'baja', 'media', 'alta'
    requiere_instalacion_domestica = Column(Boolean, default=False)
    url_imagen = Column(String(255), nullable=True) # Nuevo campo


class CargaEliminadaSQL(Base):
    __tablename__ = "cargas_eliminadas"

    id = Column(Integer, primary_key=True, index=True)
    modelo_auto = Column(String(50), nullable=False)
    tipo_autonomia = Column(String(10), nullable=False)
    autonomia_km = Column(Float, nullable=False)
    consumo_kwh_100km = Column(Float, nullable=False)
    tiempo_carga_horas = Column(Float, nullable=False)
    dificultad_carga = Column(String(10), nullable=False)
    requiere_instalacion_domestica = Column(Boolean, default=False)
    url_imagen = Column(String(255), nullable=True) # Nuevo campo


class EstacionSQL(Base):
    __tablename__ = "estaciones_carga"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    ubicacion = Column(String(100), nullable=False)
    tipo_conector = Column(String(10), nullable=False)
    potencia_kw = Column(Float, nullable=False)
    num_conectores = Column(Integer, nullable=False)
    acceso_publico = Column(Boolean, default=True)
    horario_apertura = Column(String(50), nullable=False)
    coste_por_kwh = Column(Float, nullable=False)
    operador = Column(String(50), nullable=False)
    url_imagen = Column(String(255), nullable=True) # Nuevo campo

class EstacionEliminadaSQL(Base):
    __tablename__ = "estaciones_eliminadas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    ubicacion = Column(String(100), nullable=False)
    tipo_conector = Column(String(10), nullable=False)
    potencia_kw = Column(Float, nullable=False)
    num_conectores = Column(Integer, nullable=False)
    acceso_publico = Column(Boolean, default=True)
    horario_apertura = Column(String(50), nullable=False)
    coste_por_kwh = Column(Float, nullable=False)
    operador = Column(String(50), nullable=False)
    url_imagen = Column(String(255), nullable=True) # Nuevo campo

    class UsuarioSQL(Base):
        __tablename__ = "usuarios"

        id = Column(Integer, primary_key=True, index=True)
        # Datos de registro
        nombre = Column(String(50), nullable=False)
        edad = Column(Integer, nullable=True)  # Puede ser opcional, aunque lo pides
        correo = Column(String(100), unique=True, index=True, nullable=False)
        cedula = Column(String(20), unique=True, index=True, nullable=False)
        celular = Column(String(20), nullable=True)

        # Seguridad
        hashed_password = Column(String(255), nullable=False)  # Contraseña encriptada

        # Control
        fecha_registro = Column(DateTime, default=datetime.utcnow)
        activo = Column(Boolean, default=True)