from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional

# ------------------ Modelos para Autos Eléctricos ------------------

class AutoElectrico(BaseModel):
    marca: str = Field(..., min_length=2, max_length=30)
    modelo: str = Field(..., min_length=1, max_length=30)
    anio: int = Field(..., gt=2010, lt=2026) # Año mayor que 2010 y menor que 2026
    capacidad_bateria_kwh: float = Field(..., gt=0)
    autonomia_km: float = Field(..., gt=0)
    disponible: bool = Field(...)
    url_imagen: Optional[str] = Field(None, max_length=255) # Nuevo campo para la URL de la imagen

class AutoElectricoConID(AutoElectrico):
    id: int # El ID será generado por la base de datos

class AutoActualizado(BaseModel):
    # Campos opcionales para actualizaciones parciales (PATCH)
    marca: Optional[str] = Field(None, min_length=2, max_length=30)
    modelo: Optional[str] = Field(None, min_length=1, max_length=30)
    anio: Optional[int] = Field(None, gt=2010, lt=2026)
    capacidad_bateria_kwh: Optional[float] = Field(None, gt=0)
    autonomia_km: Optional[float] = Field(None, gt=0)
    disponible: Optional[bool] = Field(None)
    url_imagen: Optional[str] = Field(None, max_length=255)


# ------------------ Modelos para Carga ------------------

class CargaBase(BaseModel):
    modelo_auto: str = Field(..., min_length=1, max_length=50)
    tipo_autonomia: str = Field(..., pattern="^(EPA|WLTP|NEDC|Mixta)$", description="Tipo de autonomía (EPA, WLTP, NEDC, Mixta)")
    autonomia_km: float = Field(..., gt=0)
    consumo_kwh_100km: float = Field(..., gt=0)
    tiempo_carga_horas: float = Field(..., gt=0)
    dificultad_carga: str = Field(..., pattern="^(baja|media|alta)$", description="Nivel de dificultad de carga (baja, media, alta)")
    requiere_instalacion_domestica: bool = Field(...)
    url_imagen: Optional[str] = Field(None, max_length=255) # Nuevo campo

class CargaConID(CargaBase):
    id: int

class CargaActualizada(BaseModel):
    modelo_auto: Optional[str] = Field(None, min_length=1, max_length=50)
    tipo_autonomia: Optional[str] = Field(None, pattern="^(EPA|WLTP|NEDC|Mixta)$")
    autonomia_km: Optional[float] = Field(None, gt=0)
    consumo_kwh_100km: Optional[float] = Field(None, gt=0)
    tiempo_carga_horas: Optional[float] = Field(None, gt=0)
    dificultad_carga: Optional[str] = Field(None, pattern="^(baja|media|alta)$")
    requiere_instalacion_domestica: Optional[bool] = Field(None)
    url_imagen: Optional[str] = Field(None, max_length=255)


# ------------------ Modelos para Estaciones de Carga ------------------

class EstacionBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)
    ubicacion: str = Field(..., min_length=5, max_length=100)
    tipo_conector: str = Field(..., pattern="^(CCS|CHAdeMO|Tipo 2|Schuko|Tesla)$", description="Tipo de conector (CCS, CHAdeMO, Tipo 2, Schuko, Tesla)")
    potencia_kw: float = Field(..., ge=3.7, le=350) # Rango típico de potencia de carga
    num_conectores: int = Field(..., ge=1, le=20)
    acceso_publico: bool = Field(...)
    horario_apertura: str = Field(..., min_length=3, max_length=50)
    coste_por_kwh: float = Field(..., ge=0, le=1) # Costo razonable por kWh
    operador: str = Field(..., min_length=2, max_length=50)
    url_imagen: Optional[str] = Field(None, max_length=255) # Nuevo campo

class EstacionConID(EstacionBase):
    id: int

class EstacionActualizada(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=50)
    ubicacion: Optional[str] = Field(None, min_length=5, max_length=100)
    tipo_conector: Optional[str] = Field(None, pattern="^(CCS|CHAdeMO|Tipo 2|Schuko|Tesla)$")
    potencia_kw: Optional[float] = Field(None, ge=3.7, le=350)
    num_conectores: Optional[int] = Field(None, ge=1, le=20)
    acceso_publico: Optional[bool] = Field(None)
    horario_apertura: Optional[str] = Field(None, min_length=3, max_length=50)
    coste_por_kwh: Optional[float] = Field(None, ge=0, le=1)
    operador: Optional[str] = Field(None, min_length=2, max_length=50)
    url_imagen: Optional[str] = Field(None, max_length=255)

class UsuarioBase(BaseModel):
    correo: EmailStr
    nombre: str = Field(..., min_length=2, max_length=50)
    edad: Optional[int] = Field(None, gt=0, le=120)
    cedula: str = Field(..., min_length=5, max_length=20)
    celular: Optional[str] = Field(None, min_length=7, max_length=20)

class UsuarioRegistro(UsuarioBase):
    password: str = Field(..., min_length=8, description="Debe contener al menos 8 caracteres y un número.")

    # Pydantic valida que la contraseña cumpla los requisitos
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres.')
        if not any(char.isdigit() for char in v):
            raise ValueError('La contraseña debe contener al menos un número.')
        return v

class UsuarioLogin(BaseModel):
    cedula_o_correo: str
    password: str

class CambioPassword(BaseModel):
    identificador: str # Cedula o correo
    password_anterior: Optional[str] = None # Campo opcional si se usa la cedula como identificador
    password_nueva: str = Field(..., min_length=8)
    password_nueva_confirmacion: str = Field(..., min_length=8)

    @validator('password_nueva', 'password_nueva_confirmacion')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('La nueva contraseña debe tener al menos 8 caracteres.')
        if not any(char.isdigit() for char in v):
            raise ValueError('La nueva contraseña debe contener al menos un número.')
        return v

    @validator('password_nueva_confirmacion')
    def passwords_match(cls, v, values, **kwargs):
        if 'password_nueva' in values and v != values['password_nueva']:
            raise ValueError('Las contraseñas no coinciden.')
        return v