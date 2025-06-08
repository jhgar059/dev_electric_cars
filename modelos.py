# modelos.py
from pydantic import BaseModel, Field
from typing import Optional

# ------------------ Modelos para Autos Eléctricos ------------------

class AutoElectrico(BaseModel):
    marca: str = Field(..., min_length=2, max_length=30, description="Marca del auto (2-30 caracteres)")
    modelo: str = Field(..., min_length=1, max_length=30, description="Modelo del auto (1-30 caracteres)")
    anio: int = Field(..., gt=2010, lt=2026, description="Año de fabricación (entre 2011 y 2025)") # Año mayor que 2010 y menor que 2026
    capacidad_bateria_kwh: float = Field(..., gt=0, le=200, description="Capacidad de la batería en kWh (mayor a 0, hasta 200)") # Límite superior añadido
    autonomia_km: float = Field(..., gt=0, le=1000, description="Autonomía en km (mayor a 0, hasta 1000)") # Límite superior añadido
    disponible: bool = Field(..., description="Disponibilidad del auto")
    url_imagen: Optional[str] = Field(None, max_length=255, description="URL de la imagen (hasta 255 caracteres)")

class AutoElectricoConID(AutoElectrico):
    id: int # El ID será generado por la base de datos

class AutoActualizado(BaseModel):
    # Campos opcionales para actualizaciones parciales (PATCH)
    marca: Optional[str] = Field(None, min_length=2, max_length=30, description="Marca del auto (2-30 caracteres)")
    modelo: Optional[str] = Field(None, min_length=1, max_length=30, description="Modelo del auto (1-30 caracteres)")
    anio: Optional[int] = Field(None, gt=2010, lt=2026, description="Año de fabricación (entre 2011 y 2025)")
    capacidad_bateria_kwh: Optional[float] = Field(None, gt=0, le=200, description="Capacidad de la batería en kWh (mayor a 0, hasta 200)")
    autonomia_km: Optional[float] = Field(None, gt=0, le=1000, description="Autonomía en km (mayor a 0, hasta 1000)")
    disponible: Optional[bool] = Field(None, description="Disponibilidad del auto")
    url_imagen: Optional[str] = Field(None, max_length=255, description="URL de la imagen (hasta 255 caracteres)")

# ------------------ Modelos para Carga ------------------

class CargaBase(BaseModel):
    modelo: str = Field(..., min_length=1, max_length=50, description="Modelo de auto (1-50 caracteres)")
    tipo_autonomia: str = Field(..., pattern="^(WLTP|EPA|NEDC|Otra)$", description="Tipo de autonomía (WLTP, EPA, NEDC, Otra)")
    consumo_kwh_100km: float = Field(..., gt=0, le=50, description="Consumo en kWh/100km (mayor a 0, hasta 50)") # Límite superior añadido
    tiempo_carga_horas: float = Field(..., gt=0, le=48, description="Tiempo de carga en horas (mayor a 0, hasta 48)") # Límite superior añadido
    dificultad_carga: str = Field(..., pattern="^(baja|media|alta)$", description="Dificultad de carga (baja, media, alta)")
    requiere_instalacion_domestica: bool = Field(..., description="Requiere instalación doméstica")
    url_imagen: Optional[str] = Field(None, max_length=255, description="URL de la imagen (hasta 255 caracteres)")

class CargaConID(CargaBase):
    id: int

class CargaActualizada(BaseModel):
    modelo: Optional[str] = Field(None, min_length=1, max_length=50, description="Modelo de auto (1-50 caracteres)")
    tipo_autonomia: Optional[str] = Field(None, pattern="^(WLTP|EPA|NEDC|Otra)$", description="Tipo de autonomía (WLTP, EPA, NEDC, Otra)")
    consumo_kwh_100km: Optional[float] = Field(None, gt=0, le=50, description="Consumo en kWh/100km (mayor a 0, hasta 50)")
    tiempo_carga_horas: Optional[float] = Field(None, gt=0, le=48, description="Tiempo de carga en horas (mayor a 0, hasta 48)")
    dificultad_carga: Optional[str] = Field(None, pattern="^(baja|media|alta)$", description="Dificultad de carga (baja, media, alta)")
    requiere_instalacion_domestica: Optional[bool] = Field(None, description="Requiere instalación doméstica")
    url_imagen: Optional[str] = Field(None, max_length=255, description="URL de la imagen (hasta 255 caracteres)")

# ------------------ Modelos para Estaciones de Carga ------------------

class EstacionBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50, description="Nombre de la estación (2-50 caracteres)")
    ubicacion: str = Field(..., min_length=5, max_length=100, description="Ubicación de la estación (5-100 caracteres)")
    tipo_conector: str = Field(..., pattern="^(CCS|CHAdeMO|Tipo 2|Schuko|Tesla|Otro)$", description="Tipo de conector (CCS, CHAdeMO, Tipo 2, Schuko, Tesla, Otro)") # Añadido "Otro"
    potencia_kw: float = Field(..., ge=1, le=500, description="Potencia en kW (entre 1 y 500)") # Rango típico de potencia de carga
    num_conectores: int = Field(..., ge=1, le=50, description="Número de conectores (entre 1 y 50)")
    acceso_publico: bool = Field(..., description="Acceso público a la estación")
    horario_apertura: str = Field(..., min_length=3, max_length=50, description="Horario de apertura (3-50 caracteres)")
    coste_por_kwh: float = Field(..., ge=0, le=2, description="Costo por kWh (entre 0 y 2)") # Costo razonable por kWh, ampliado ligeramente
    operador: str = Field(..., min_length=2, max_length=50, description="Operador de la estación (2-50 caracteres)")
    url_imagen: Optional[str] = Field(None, max_length=255, description="URL de la imagen (hasta 255 caracteres)") # Nuevo campo

class EstacionConID(EstacionBase):
    id: int

class EstacionActualizada(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=50, description="Nombre de la estación (2-50 caracteres)")
    ubicacion: Optional[str] = Field(None, min_length=5, max_length=100, description="Ubicación de la estación (5-100 caracteres)")
    tipo_conector: Optional[str] = Field(None, pattern="^(CCS|CHAdeMO|Tipo 2|Schuko|Tesla|Otro)$", description="Tipo de conector (CCS, CHAdeMO, Tipo 2, Schuko, Tesla, Otro)")
    potencia_kw: Optional[float] = Field(None, ge=1, le=500, description="Potencia en kW (entre 1 y 500)")
    num_conectores: Optional[int] = Field(None, ge=1, le=50, description="Número de conectores (entre 1 y 50)")
    acceso_publico: Optional[bool] = Field(None, description="Acceso público a la estación")
    horario_apertura: Optional[str] = Field(None, min_length=3, max_length=50, description="Horario de apertura (3-50 caracteres)")
    coste_por_kwh: Optional[float] = Field(None, ge=0, le=2, description="Costo por kWh (entre 0 y 2)")
    operador: Optional[str] = Field(None, min_length=2, max_length=50, description="Operador de la estación (2-50 caracteres)")
    url_imagen: Optional[str] = Field(None, max_length=255, description="URL de la imagen (hasta 255 caracteres)")