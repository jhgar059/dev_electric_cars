from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import Optional

from database import Base

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

class CargaSQL(Base):
    __tablename__ = "dificultad_carga"

    id = Column(Integer, primary_key=True, index=True)
    modelo = Column(String(50), nullable=False)
    tipo_autonomia = Column(String(10), nullable=False)
    autonomia_km = Column(Float, nullable=False)
    consumo_kwh_100km = Column(Float, nullable=False)
    tiempo_carga_horas = Column(Float, nullable=False)
    dificultad_carga = Column(String(5), nullable=False)
    requiere_instalacion_domestica = Column(Boolean, default=False)

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

# Mantenemos los modelos Pydantic para validación y serialización de la API
# (puedes mantener tu archivo modelos.py existente)