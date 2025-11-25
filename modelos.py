from pydantic import BaseModel, Field, EmailStr, field_validator, ValidationInfo
from typing import Optional


# ------------------ Modelos para Autos Eléctricos ------------------

class AutoElectrico(BaseModel):
    marca: str = Field(..., min_length=2, max_length=30)
    modelo: str = Field(..., min_length=1, max_length=30)
    anio: int = Field(..., gt=2010, lt=2026)
    capacidad_bateria_kwh: float = Field(..., gt=0)
    autonomia_km: float = Field(..., gt=0)
    disponible: bool = Field(...)
    url_imagen: Optional[str] = Field(None, max_length=255)


class AutoElectricoConID(AutoElectrico):
    id: int

    class Config:
        from_attributes = True


class AutoActualizado(BaseModel):
    marca: Optional[str] = Field(None, min_length=2, max_length=30)
    modelo: Optional[str] = Field(None, min_length=1, max_length=30)
    anio: Optional[int] = Field(None, gt=2010, lt=2026)
    capacidad_bateria_kwh: Optional[float] = Field(None, gt=0)
    autonomia_km: Optional[float] = Field(None, gt=0)
    disponible: Optional[bool] = None
    url_imagen: Optional[str] = Field(None, max_length=255)


# ------------------ Modelos para Cargas ------------------

class CargaBase(BaseModel):
    modelo_auto: str = Field(..., min_length=1, max_length=50)
    tipo_autonomia: str = Field(..., max_length=20)
    autonomia_km: float = Field(..., gt=0)
    consumo_kwh_100km: float = Field(..., gt=0)
    tiempo_carga_horas: float = Field(..., gt=0)
    dificultad_carga: str = Field(..., max_length=10)
    requiere_instalacion_domestica: bool = Field(...)
    url_imagen: Optional[str] = Field(None, max_length=255)


class CargaConID(CargaBase):
    id: int

    class Config:
        from_attributes = True


class CargaActualizada(BaseModel):
    modelo_auto: Optional[str] = Field(None, min_length=1, max_length=50)
    tipo_autonomia: Optional[str] = Field(None, max_length=20)
    autonomia_km: Optional[float] = Field(None, gt=0)
    consumo_kwh_100km: Optional[float] = Field(None, gt=0)
    tiempo_carga_horas: Optional[float] = Field(None, gt=0)
    dificultad_carga: Optional[str] = Field(None, max_length=10)
    requiere_instalacion_domestica: Optional[bool] = None
    url_imagen: Optional[str] = Field(None, max_length=255)


# ------------------ Modelos para Estaciones de Carga ------------------

class EstacionBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)
    ubicacion: str = Field(..., min_length=5, max_length=100)
    tipo_conector: str = Field(..., max_length=10)
    potencia_kw: float = Field(..., gt=0)
    num_conectores: int = Field(..., gt=0)
    acceso_publico: bool = Field(...)
    horario_apertura: str = Field(..., max_length=50)
    coste_por_kwh: float = Field(..., ge=0)
    operador: str = Field(..., max_length=50)
    url_imagen: Optional[str] = Field(None, max_length=255)


class EstacionConID(EstacionBase):
    id: int

    class Config:
        from_attributes = True


class EstacionActualizada(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=50)
    ubicacion: Optional[str] = Field(None, min_length=5, max_length=100)
    tipo_conector: Optional[str] = Field(None, max_length=10)
    potencia_kw: Optional[float] = Field(None, gt=0)
    num_conectores: Optional[int] = Field(None, gt=0)
    acceso_publico: Optional[bool] = None
    horario_apertura: Optional[str] = Field(None, max_length=50)
    coste_por_kwh: Optional[float] = Field(None, ge=0)
    operador: Optional[str] = Field(None, max_length=50)
    url_imagen: Optional[str] = Field(None, max_length=255)


# ------------------ Modelos para Autenticación de Usuarios ------------------

class UsuarioRegistro(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)
    edad: int = Field(..., gt=17, lt=100)
    correo: EmailStr
    cedula: str = Field(..., min_length=5, max_length=15)
    celular: str = Field(..., min_length=7, max_length=15)
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="debe contener entre 8 y 72 caracteres y un número."
    )

    @field_validator('password')
    @classmethod
    def validate_password_content(cls, v: str):
        if not any(char.isdigit() for char in v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v


class UsuarioRespuesta(BaseModel):
    id: int
    nombre: str
    edad: int
    correo: str
    cedula: str
    celular: Optional[str]
    activo: bool

    class Config:
        from_attributes = True


class UsuarioLogin(BaseModel):
    cedula_o_correo: str
    password: str


class CambioPassword(BaseModel):
    identificador: str
    password_anterior: Optional[str] = None
    password_nueva: str = Field(..., min_length=8, max_length=72)
    password_nueva_confirmacion: str = Field(..., min_length=8, max_length=72)

    @field_validator('password_nueva')
    @classmethod
    def validate_new_password_content(cls, v: str):
        if len(v) < 8:
            raise ValueError('La nueva contraseña debe tener al menos 8 caracteres')
        if len(v) > 72:
            raise ValueError('La nueva contraseña no puede exceder 72 caracteres')
        if not any(char.isdigit() for char in v):
            raise ValueError('La nueva contraseña debe contener al menos un número')
        return v

    @field_validator('password_nueva_confirmacion')
    @classmethod
    def passwords_match(cls, v: str, info: ValidationInfo):
        if 'password_nueva' in info.data and v != info.data['password_nueva']:
            raise ValueError('Las contraseñas no coinciden')
        return v