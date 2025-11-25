# main.py - VERSIÓN COMPLETA CON SISTEMA DE SESIÓN Y LOGOUT CORREGIDO

from fastapi import FastAPI, HTTPException, Depends, Request, File, UploadFile, Form, status, Response, Cookie
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional
import os
import logging
import sys
import traceback
from sqlalchemy.orm import Session
from pathlib import Path
from sqlalchemy import func
import uuid

# Importaciones de modelos y utilidades
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
# Usamos un alias para la función protegida para distinguirla del helper opcional
from auth_utils import get_password_hash, verify_password, get_current_user_simplified as get_authenticated_user

# Configuración de Logging MÁS DETALLADO
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("FastAPI")

# Inicialización de FastAPI
app = FastAPI(
    title="Electric Cars Database API",
    description="API y Dashboard para gestión de datos de Vehículos Eléctricos y Estaciones de Carga.",
    version="1.0.0",
)

# Configuración de Jinja2
templates = Jinja2Templates(directory="templates")

# Configuración de Archivos Estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")


# --------------------------------------------------------------------------------------
#                         HELPER DE SESIÓN PARA RUTAS WEB
# --------------------------------------------------------------------------------------

def get_optional_current_user(
        db: Session = Depends(get_db),
        # El nombre de la cookie debe coincidir con el que usa tu ruta de login
        session_token: Optional[str] = Cookie(None, alias="session_token")
) -> Optional[models_sql.UsuarioSQL]:
    """
    Intenta recuperar el usuario a partir del token de sesión (cookie).
    No lanza excepción, solo devuelve None si no hay sesión o es inválida.
    """
    if not session_token:
        return None
    try:
        # El token (cedula/correo) se usa para buscar el usuario en la BD
        user = user_crud.get_user_by_cedula_or_correo(db, session_token)
        if user and user.activo:
            return user
        return None
    except Exception as e:
        logger.warning(f"Error recuperando usuario de la sesión (posible token inválido/expirado): {e}")
        return None


# --------------------------------------------------------------------------------------
#                             RUTAS DE AUTENTICACIÓN (PÚBLICAS)
# --------------------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse, tags=["Web UI"], name="welcome_page")
async def welcome_page(request: Request, user: Optional[models_sql.UsuarioSQL] = Depends(get_optional_current_user)):
    """Página de bienvenida. Redirige si está logueado."""
    if user:
        # Si está logueado, lo envía al dashboard principal
        return RedirectResponse(url="/index", status_code=status.HTTP_302_FOUND)

    # Renderiza la página de bienvenida (solo enlaces de Auth)
    return templates.TemplateResponse("welcome.html", {"request": request, "current_user": user})


@app.get("/login", response_class=HTMLResponse, tags=["Web UI"], name="login_form")
async def login_form(request: Request, user: Optional[models_sql.UsuarioSQL] = Depends(get_optional_current_user)):
    """Formulario de Iniciar Sesión. Redirige si ya está logueado."""
    if user:
        return RedirectResponse(url="/index", status_code=status.HTTP_302_FOUND)
    # Se pasa 'user' (que será None) al template para la barra de navegación
    return templates.TemplateResponse("login.html", {"request": request, "current_user": user})


@app.get("/register", response_class=HTMLResponse, tags=["Web UI"], name="register_form")
async def register_form(request: Request, user: Optional[models_sql.UsuarioSQL] = Depends(get_optional_current_user)):
    """Formulario de Registro. Redirige si ya está logueado."""
    if user:
        return RedirectResponse(url="/index", status_code=status.HTTP_302_FOUND)
    # Se pasa 'user' (que será None) al template
    return templates.TemplateResponse("register.html", {"request": request, "form_data": {}, "current_user": user})


@app.get("/change_password", response_class=HTMLResponse, tags=["Web UI"], name="change_password_form")
async def change_password_form(request: Request,
                               user: Optional[models_sql.UsuarioSQL] = Depends(get_optional_current_user)):
    """Formulario de Cambio de Contraseña."""
    # Se permite cambiar la contraseña sin estar logueado, pero el nav bar se muestra sin opciones de CRUD
    return templates.TemplateResponse("change_password.html",
                                      {"request": request, "form_data": {}, "current_user": user})


@app.get("/logout", tags=["Web UI"], name="logout")
async def logout(request: Request):
    """Cierra la sesión y elimina la cookie."""
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session_token")
    # Limpieza de caché por si acaso
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    logger.info("Usuario cerró sesión.")
    return response


# --------------------------------------------------------------------------------------
#                             RUTAS DEL DASHBOARD (PROTEGIDAS)
# --------------------------------------------------------------------------------------
# Todas estas rutas usan Depends(get_authenticated_user) para garantizar el login.

@app.get("/index", response_class=HTMLResponse, tags=["Web UI"], name="index_page")
async def index_page(
        request: Request,
        db: Session = Depends(get_db),
        user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)
):
    """Página de inicio (Dashboard) autenticada."""
    # Aquí puedes agregar la lógica para obtener estadísticas o datos para la página principal
    context = {
        "request": request,
        "current_user": user,  # El usuario está garantizado
        "average_autonomy": "250 km",  # Datos de ejemplo
    }
    return templates.TemplateResponse("index.html", context)


@app.get("/cars", response_class=HTMLResponse, tags=["Web UI"], name="cars_page")
async def cars_page(request: Request, db: Session = Depends(get_db),
                    user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)):
    autos = crud.get_autos(db)
    return templates.TemplateResponse("cars.html", {"request": request, "autos": autos, "current_user": user})


@app.get("/charges", response_class=HTMLResponse, tags=["Web UI"], name="charges_page")
async def charges_page(request: Request, db: Session = Depends(get_db),
                       user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)):
    cargas = crud.get_cargas(db)
    return templates.TemplateResponse("charges.html", {"request": request, "cargas": cargas, "current_user": user})


@app.get("/stations", response_class=HTMLResponse, tags=["Web UI"], name="stations_page")
async def stations_page(request: Request, db: Session = Depends(get_db),
                        user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)):
    estaciones = crud.get_estaciones(db)
    return templates.TemplateResponse("stations.html",
                                      {"request": request, "estaciones": estaciones, "current_user": user})


@app.get("/statistics_page", response_class=HTMLResponse, tags=["Web UI"], name="statistics_page")
async def statistics_page(request: Request,
                          user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)):
    return templates.TemplateResponse("statistics_page.html", {"request": request, "current_user": user})


# --- Rutas de Historial ---
@app.get("/deleted_cars", response_class=HTMLResponse, tags=["Web UI"], name="deleted_cars_page")
async def deleted_cars_page(request: Request, db: Session = Depends(get_db),
                            user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)):
    autos_eliminados = crud.get_deleted_autos(db)
    return templates.TemplateResponse("deleted_cars.html",
                                      {"request": request, "autos_eliminados": autos_eliminados, "current_user": user})


@app.get("/deleted_charges", response_class=HTMLResponse, tags=["Web UI"], name="deleted_charges_page")
async def deleted_charges_page(request: Request, db: Session = Depends(get_db),
                               user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)):
    cargas_eliminadas = crud.get_deleted_cargas(db)
    return templates.TemplateResponse("deleted_charges.html",
                                      {"request": request, "cargas_eliminadas": cargas_eliminadas,
                                       "current_user": user})


@app.get("/deleted_stations", response_class=HTMLResponse, tags=["Web UI"], name="deleted_stations_page")
async def deleted_stations_page(request: Request, db: Session = Depends(get_db),
                                user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)):
    estaciones_eliminadas = crud.get_deleted_estaciones(db)
    return templates.TemplateResponse("deleted_stations.html",
                                      {"request": request, "estaciones_eliminadas": estaciones_eliminadas,
                                       "current_user": user})


# --- Rutas de Proyecto (También se protegen) ---
# Se necesita una ruta para cada página del dropdown "Proyecto" para que url_for funcione.
@app.get("/project_objective", response_class=HTMLResponse, tags=["Web UI"], name="project_objective_page")
async def project_objective_page(request: Request,
                                 user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)):
    return templates.TemplateResponse("project_objective.html", {"request": request, "current_user": user})


@app.get("/planning_design", response_class=HTMLResponse, tags=["Web UI"], name="planning_design_page")
async def planning_design_page(request: Request,
                               user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)):
    return templates.TemplateResponse("planning_design.html", {"request": request, "current_user": user})


@app.get("/mockups_wireframes", response_class=HTMLResponse, tags=["Web UI"], name="mockups_wireframes_page")
async def mockups_wireframes_page(request: Request,
                                  user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)):
    return templates.TemplateResponse("mockups_wireframes.html", {"request": request, "current_user": user})


@app.get("/endpoint_map", response_class=HTMLResponse, tags=["Web UI"], name="endpoint_map_page")
async def endpoint_map_page(request: Request,
                            user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)):
    return templates.TemplateResponse("endpoint_map.html", {"request": request, "current_user": user})


@app.get("/developer_info", response_class=HTMLResponse, tags=["Web UI"], name="developer_info_page")
async def developer_info_page(request: Request,
                              user: models_sql.UsuarioSQL = Depends(get_authenticated_user, use_cache=False)):
    return templates.TemplateResponse("developer_info.html", {"request": request, "current_user": user})


# --------------------------------------------------------------------------------------
#                             RUTAS DE API (CRUD, ESTADÍSTICAS, ETC.)
# --------------------------------------------------------------------------------------
# Asegúrate de que TODAS tus rutas API usen el Depends(get_authenticated_user)
# Esto garantiza que la API solo es utilizable con un token válido, una vez que el usuario se ha logueado.

# EJEMPLO DE RUTA API PROTEGIDA:
@app.get("/api/autos", response_model=List[AutoElectricoConID], tags=["Autos"])
async def read_autos(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        # 🚨 CRÍTICO: Agregar esta dependencia a todas las rutas API
        user: models_sql.UsuarioSQL = Depends(get_authenticated_user)
):
    """Obtiene una lista de autos eléctricos (requiere autenticación)."""
    autos = crud.get_autos(db, skip=skip, limit=limit)
    return autos

# ... (El resto de tus rutas API/CRUD/Estadísticas deben tener la misma protección) ...