# main.py - COMPLETO Y CORREGIDO

from fastapi import FastAPI, HTTPException, Depends, Request, File, UploadFile, Form, status, Response
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional
import os
import logging
import sys
from sqlalchemy.orm import Session
from pathlib import Path
from sqlalchemy import func
import uuid

# Importaciones de modelos y dependencias
from modelos import (
    AutoElectrico, AutoElectricoConID, AutoActualizado,
    CargaBase, CargaConID, CargaActualizada,
    EstacionBase, EstacionConID, EstacionActualizada,
    UsuarioRegistro, UsuarioLogin, CambioPassword, UsuarioRespuesta
)

from database import get_db, engine, Base
import models_sql
import crud
import crud_usuarios as user_crud
from auth_utils import get_password_hash, verify_password, get_current_user

# Configuración de Logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("FastAPI")

# Inicialización de FastAPI
app = FastAPI(
    title="Electric Cars Database API",
    description="API RESTful para la gestión de datos de autos y estaciones de carga eléctricas.",
    version="1.0.0",
)

# Configuración de directorios
templates = Jinja2Templates(directory="templates")
UPLOAD_DIRECTORY = Path("static/images")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")


# Dependencia de seguridad: Obtener el usuario activo actual
def get_current_active_user(user: models_sql.UsuarioSQL = Depends(get_current_user)):
    """Dependencia para proteger las rutas, asegurando que el usuario esté autenticado."""
    if not user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return user


# --------------------- MANEJO DE VISTAS HTML ---------------------

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def welcome_page(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})


@app.get("/index", response_class=HTMLResponse, include_in_schema=False)
async def index_page(request: Request, db: Session = Depends(get_db)):
    """Página de inicio con estadísticas"""
    total_autos = crud.get_autos_count(db)
    total_cargas = crud.get_cargas_count(db)
    total_estaciones = crud.get_estaciones_count(db)
    avg_autonomia = crud.get_average_autonomia(db)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "total_autos": total_autos,
        "total_cargas": total_cargas,
        "total_estaciones": total_estaciones,
        "avg_autonomia": avg_autonomia,
        "is_home_page": True
    })


@app.get("/project_objective", response_class=HTMLResponse, include_in_schema=False)
async def project_objective_page(request: Request):
    return templates.TemplateResponse("project_objective.html", {"request": request})


@app.get("/mockups_wireframes", response_class=HTMLResponse, include_in_schema=False)
async def mockups_wireframes_page(request: Request):
    return templates.TemplateResponse("mockups_wireframes.html", {"request": request})


@app.get("/endpoint_map", response_class=HTMLResponse, include_in_schema=False)
async def endpoint_map_page(request: Request):
    return templates.TemplateResponse("endpoint_map.html", {"request": request})


@app.get("/developer_info", response_class=HTMLResponse, include_in_schema=False)
async def developer_info_page(request: Request):
    return templates.TemplateResponse("developer_info.html", {"request": request})


@app.get("/planning_design", response_class=HTMLResponse, include_in_schema=False)
async def planning_design_page(request: Request):
    return templates.TemplateResponse("planning_design.html", {"request": request})


# --------------------- AUTENTICACIÓN Y REGISTRO (VISTAS Y LÓGICA) ---------------------

@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error_message": None})


@app.get("/register", response_class=HTMLResponse, include_in_schema=False)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error_message": None, "form_data": {}})


@app.post("/register", response_class=HTMLResponse, include_in_schema=False)
async def register_user(
        request: Request,
        db: Session = Depends(get_db),
        nombre: str = Form(...),
        edad: int = Form(...),
        correo: str = Form(...),
        cedula: str = Form(...),
        celular: Optional[str] = Form(None),
        password: str = Form(...)
):
    user_data = {
        "nombre": nombre, "edad": edad, "correo": correo,
        "cedula": cedula, "celular": celular, "password": password
    }

    try:
        # Validaciones de existencia
        if user_crud.get_user_by_cedula(db, cedula):
            raise HTTPException(status_code=400, detail="La cédula ya está registrada.")
        if user_crud.get_user_by_correo(db, correo):
            raise HTTPException(status_code=400, detail="El correo ya está registrado.")

        # Validar el modelo Pydantic para el registro
        new_user = UsuarioRegistro(**user_data)
        user_crud.create_user(db, new_user)

        # Redireccionar al login con mensaje de éxito
        return RedirectResponse(
            url="/login?success_message=Registro%20exitoso.%20Ahora%20puedes%20iniciar%20sesión.",
            status_code=status.HTTP_302_FOUND
        )

    except HTTPException as e:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error_message": e.detail, "form_data": user_data},
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Error durante el registro: {e}", exc_info=True)
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error_message": "Error interno del servidor durante el registro.",
                "form_data": user_data
            },
            status_code=500
        )


@app.get("/change_password", response_class=HTMLResponse, include_in_schema=False)
async def change_password_form(request: Request):
    return templates.TemplateResponse(
        "change_password.html",
        {"request": request, "error_message": None, "form_data": {}}
    )


@app.post("/change_password", response_class=HTMLResponse, include_in_schema=False)
async def handle_change_password(
        request: Request,
        db: Session = Depends(get_db),
        identificador: str = Form(...),
        password_anterior: Optional[str] = Form(None),
        password_nueva: str = Form(...),
        password_nueva_confirmacion: str = Form(...)
):
    form_data = {
        "identificador": identificador,
        "password_anterior": password_anterior,
        "password_nueva": password_nueva,
        "password_nueva_confirmacion": password_nueva_confirmacion
    }

    try:
        # 1. Validar coincidencia de contraseñas nuevas y requisitos
        pass_change = CambioPassword(**form_data)

        # 2. Buscar al usuario
        user = user_crud.get_user_by_cedula_or_correo(db, identificador)
        if user is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        # 3. Verificar contraseña anterior
        if user.hashed_password:
            if not password_anterior:
                raise HTTPException(status_code=400, detail="Debes ingresar la contraseña anterior.")
            if not verify_password(password_anterior, user.hashed_password):
                raise HTTPException(status_code=401, detail="Contraseña anterior incorrecta.")

        # 4. Actualizar la contraseña
        user_crud.update_user_password(db, user.id, pass_change.password_nueva)

        return RedirectResponse(
            url="/login?success_message=Contraseña%20actualizada%20exitosamente.%20Inicia%20sesión%20con%20la%20nueva%20clave.",
            status_code=status.HTTP_302_FOUND
        )

    except Exception as e:
        error_detail = "Error desconocido."
        status_code = 500
        if isinstance(e, HTTPException):
            error_detail = e.detail
            status_code = e.status_code
        elif hasattr(e, 'errors'):
            error_detail = next(iter(e.errors()))['msg']
            status_code = 422

        logger.error(f"Error durante el cambio de contraseña: {error_detail}", exc_info=True)
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "error_message": error_detail, "form_data": form_data},
            status_code=status_code
        )


# --------------------- AUTENTICACIÓN (API) ---------------------

@app.post("/api/login")
async def login_for_access_token(
        db: Session = Depends(get_db),
        form_data: OAuth2PasswordRequestForm = Depends()
):
    """Endpoint API para iniciar sesión y obtener el token."""
    try:
        # Buscar usuario
        user = user_crud.get_user_by_cedula_or_correo(db, form_data.username)

        if not user:
            logger.warning(f"Intento de login fallido: usuario no encontrado - {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verificar contraseña
        if not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Intento de login fallido: contraseña incorrecta - {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Login exitoso
        logger.info(f"Login exitoso: {user.cedula}")

        # Redireccionar a /index después del login exitoso
        return RedirectResponse(url="/index", status_code=status.HTTP_302_FOUND)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@app.get("/api/logout")
async def logout():
    """Redirecciona al login después de cerrar sesión (stateless)."""
    return RedirectResponse(
        url="/login?success_message=Sesión%20cerrada%20exitosamente.",
        status_code=status.HTTP_302_FOUND
    )


# --------------------- VISTAS PROTEGIDAS Y CRUD PRINCIPAL ---------------------

@app.get("/cars", response_class=HTMLResponse, include_in_schema=False)
async def cars_page(request: Request, user: models_sql.UsuarioSQL = Depends(get_current_active_user)):
    return templates.TemplateResponse("cars.html", {"request": request, "current_user": user})


@app.get("/charges", response_class=HTMLResponse, include_in_schema=False)
async def charges_page(request: Request, user: models_sql.UsuarioSQL = Depends(get_current_active_user)):
    return templates.TemplateResponse("charges.html", {"request": request, "current_user": user})


@app.get("/stations", response_class=HTMLResponse, include_in_schema=False)
async def stations_page(request: Request, user: models_sql.UsuarioSQL = Depends(get_current_active_user)):
    return templates.TemplateResponse("stations.html", {"request": request, "current_user": user})


@app.get("/statistics_page", response_class=HTMLResponse, include_in_schema=False)
async def statistics_page(request: Request, user: models_sql.UsuarioSQL = Depends(get_current_active_user)):
    return templates.TemplateResponse("statistics_page.html", {"request": request, "current_user": user})


# --------------------- UTILIDAD DE IMAGEN ---------------------

async def write_image_to_disk(file: UploadFile, buffer: bytes):
    """Escribe un buffer de bytes a un archivo en el disco con un nombre único."""
    suffix = Path(file.filename).suffix if file.filename else ''
    unique_filename = f"{uuid.uuid4()}{suffix}"
    file_path = UPLOAD_DIRECTORY / unique_filename

    try:
        with open(file_path, "wb") as f:
            f.write(buffer)
        return unique_filename
    except Exception as e:
        logger.error(f"Error al escribir imagen al disco: {e}", exc_info=True)
        raise e


@app.post("/api/upload-image")
@app.post("/upload_image/")
async def upload_image(
        file: UploadFile = File(...),
        user: models_sql.UsuarioSQL = Depends(get_current_active_user)
):
    """Sube una imagen y devuelve su URL estática."""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Archivo no es una imagen.")

    MAX_FILE_SIZE = 5 * 1024 * 1024  # Límite de 5MB

    buffer = await file.read()
    if len(buffer) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="El tamaño de la imagen excede el límite de 5MB.")

    try:
        unique_filename = await write_image_to_disk(file, buffer)
        return {"url": f"/static/images/{unique_filename}"}
    except Exception as e:
        logger.error(f"Error al subir imagen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {e}")


# [Continúa con el resto de los endpoints CRUD...]
# Los endpoints de CRUD de autos, cargas y estaciones permanecen igual

if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando Uvicorn en modo desarrollo. Visita http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)