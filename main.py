# main.py - COMPLETO Y CORREGIDO

from fastapi import FastAPI, HTTPException, Depends, Request, File, UploadFile, Form, status, Response
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional, Dict, Any
import os
import logging
import sys
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
from sqlalchemy import func
import uuid  # Para generar nombres únicos para las imágenes

# Importaciones de modelos y dependencias
from modelos import AutoElectrico, AutoElectricoConID, AutoActualizado
from modelos import CargaBase, CargaConID, CargaActualizada
from modelos import EstacionBase, EstacionConID, EstacionActualizada
# Importar UsuarioRespuesta si está definido en modelos.py (asumido para el tipo de retorno)
from modelos import UsuarioRegistro, UsuarioLogin, CambioPassword


# Asumiendo que existe un modelo de respuesta para el usuario, si no, se puede usar un dict o BaseModel simple
class UsuarioRespuesta(UsuarioRegistro):
    id: int

    class Config:
        from_attributes = True


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
def get_current_active_user(user: UsuarioRespuesta = Depends(get_current_user)):
    """Dependencia para proteger las rutas, asegurando que el usuario esté autenticado."""
    return user


# --------------------- MANEJO DE VISTAS HTML ---------------------

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def welcome_page(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})


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
async def register_user(request: Request, db: Session = Depends(get_db),
                        nombre: str = Form(...), edad: int = Form(...), correo: str = Form(...),
                        cedula: str = Form(...), celular: Optional[str] = Form(None), password: str = Form(...)):
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
        return RedirectResponse(url="/login?success_message=Registro%20exitoso.%20Ahora%20puedes%20iniciar%20sesión.",
                                status_code=status.HTTP_302_FOUND)

    except HTTPException as e:
        return templates.TemplateResponse("register.html",
                                          {"request": request, "error_message": e.detail, "form_data": user_data},
                                          status_code=e.status_code)
    except Exception as e:
        logger.error(f"Error durante el registro: {e}", exc_info=True)
        return templates.TemplateResponse("register.html",
                                          {"request": request,
                                           "error_message": "Error interno del servidor durante el registro.",
                                           "form_data": user_data},
                                          status_code=500)


@app.get("/change_password", response_class=HTMLResponse, include_in_schema=False)
async def change_password_form(request: Request):
    return templates.TemplateResponse("change_password.html",
                                      {"request": request, "error_message": None, "form_data": {}})


@app.post("/change_password", response_class=HTMLResponse, include_in_schema=False)
async def handle_change_password(request: Request, db: Session = Depends(get_db),
                                 identificador: str = Form(...),
                                 password_anterior: Optional[str] = Form(None),
                                 password_nueva: str = Form(...),
                                 password_nueva_confirmacion: str = Form(...)):
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
            status_code=status.HTTP_302_FOUND)

    except Exception as e:
        error_detail = "Error desconocido."
        status_code = 500
        if isinstance(e, HTTPException):
            error_detail = e.detail
            status_code = e.status_code
        elif hasattr(e, 'errors'):  # Pydantic ValidationError
            # Manejar errores de Pydantic
            error_detail = next(iter(e.errors()))['msg']
            status_code = 422

        logger.error(f"Error durante el cambio de contraseña: {error_detail}", exc_info=True)
        return templates.TemplateResponse("change_password.html",
                                          {"request": request, "error_message": error_detail, "form_data": form_data},
                                          status_code=status_code)


# --------------------- AUTENTICACIÓN (API) ---------------------

@app.post("/api/login")
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint API para iniciar sesión y obtener el token."""
    user = user_crud.get_user_by_cedula_or_correo(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # El token es el identificador (cédula)
    return {"access_token": user.cedula, "token_type": "bearer"}


@app.get("/api/logout")
async def logout():
    """Redirecciona al login después de cerrar sesión (stateless)."""
    return RedirectResponse(url="/login?success_message=Sesión%20cerrada%20exitosamente.",
                            status_code=status.HTTP_302_FOUND)


# --------------------- VISTAS PROTEGIDAS Y CRUD PRINCIPAL ---------------------

@app.get("/cars", response_class=HTMLResponse, include_in_schema=False)
async def cars_page(request: Request, user: UsuarioRespuesta = Depends(get_current_active_user)):
    return templates.TemplateResponse("cars.html", {"request": request, "current_user": user})


@app.get("/charges", response_class=HTMLResponse, include_in_schema=False)
async def charges_page(request: Request, user: UsuarioRespuesta = Depends(get_current_active_user)):
    return templates.TemplateResponse("charges.html", {"request": request, "current_user": user})


@app.get("/stations", response_class=HTMLResponse, include_in_schema=False)
async def stations_page(request: Request, user: UsuarioRespuesta = Depends(get_current_active_user)):
    return templates.TemplateResponse("stations.html", {"request": request, "current_user": user})


@app.get("/statistics_page", response_class=HTMLResponse, include_in_schema=False)
async def statistics_page(request: Request, user: UsuarioRespuesta = Depends(get_current_active_user)):
    return templates.TemplateResponse("statistics_page.html", {"request": request, "current_user": user})


# --------------------- UTILIDAD DE IMAGEN ---------------------

async def write_image_to_disk(file: UploadFile, buffer: bytes):
    """Escribe un buffer de bytes a un archivo en el disco con un nombre único."""
    # Genera un nombre de archivo único con un UUID y conserva la extensión
    suffix = Path(file.filename).suffix if file.filename else ''
    unique_filename = f"{uuid.uuid4()}{suffix}"
    file_path = UPLOAD_DIRECTORY / unique_filename

    # Escribir el archivo
    try:
        with open(file_path, "wb") as f:
            f.write(buffer)
        return unique_filename
    except Exception as e:
        logger.error(f"Error al escribir imagen al disco: {e}", exc_info=True)
        raise e


@app.post("/api/upload-image")
async def upload_image(
        file: UploadFile = File(...),
        user: UsuarioRespuesta = Depends(get_current_active_user)
):
    """Sube una imagen y devuelve su URL estática."""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Archivo no es una imagen.")

    MAX_FILE_SIZE = 5 * 1024 * 1024  # Límite de 5MB

    # Leer el archivo y verificar tamaño
    buffer = await file.read()
    if len(buffer) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="El tamaño de la imagen excede el límite de 5MB.")

    try:
        unique_filename = await write_image_to_disk(file, buffer)
        return {"url": f"/static/images/{unique_filename}"}
    except Exception as e:
        logger.error(f"Error al subir imagen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {e}")


# --------------------- CRUD: AUTOS ELÉCTRICOS ---------------------

@app.get("/api/autos", response_model=List[AutoElectricoConID], tags=["Autos"])
async def read_autos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                     user: UsuarioRespuesta = Depends(get_current_active_user)):
    autos = crud.get_autos(db, skip=skip, limit=limit)
    return autos


@app.get("/api/autos/{auto_id}", response_model=AutoElectricoConID, tags=["Autos"])
async def read_auto(auto_id: int, db: Session = Depends(get_db),
                    user: UsuarioRespuesta = Depends(get_current_active_user)):
    db_auto = crud.get_auto(db, auto_id=auto_id)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto


@app.post("/api/autos", response_model=AutoElectricoConID, status_code=status.HTTP_201_CREATED, tags=["Autos"])
async def create_auto_endpoint(auto: AutoElectrico, db: Session = Depends(get_db),
                               user: UsuarioRespuesta = Depends(get_current_active_user)):
    db_auto = crud.create_auto(db, auto)
    if db_auto is None:
        raise HTTPException(status_code=400, detail="Ya existe un auto con el mismo modelo y año.")
    return db_auto


@app.put("/api/autos/{auto_id}", response_model=AutoElectricoConID, tags=["Autos"])
async def update_auto_endpoint(auto_id: int, auto: AutoActualizado, db: Session = Depends(get_db),
                               user: UsuarioRespuesta = Depends(get_current_active_user)):
    db_auto = crud.update_auto(db, auto_id, auto)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado para actualizar")
    return db_auto


@app.delete("/api/autos/{auto_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Autos"])
async def delete_auto_endpoint(auto_id: int, db: Session = Depends(get_db),
                               user: UsuarioRespuesta = Depends(get_current_active_user)):
    success = crud.delete_auto_to_history(db, auto_id)
    if not success:
        raise HTTPException(status_code=404, detail="Auto no encontrado para eliminar")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------- CRUD: REGISTROS DE CARGA ---------------------

@app.get("/api/cargas", response_model=List[CargaConID], tags=["Cargas"])
async def read_cargas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                      user: UsuarioRespuesta = Depends(get_current_active_user)):
    cargas = crud.get_cargas(db, skip=skip, limit=limit)
    return cargas


@app.get("/api/cargas/{carga_id}", response_model=CargaConID, tags=["Cargas"])
async def read_carga(carga_id: int, db: Session = Depends(get_db),
                     user: UsuarioRespuesta = Depends(get_current_active_user)):
    db_carga = crud.get_carga(db, carga_id=carga_id)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro de carga no encontrado")
    return db_carga


@app.post("/api/cargas", response_model=CargaConID, status_code=status.HTTP_201_CREATED, tags=["Cargas"])
async def create_carga_endpoint(carga: CargaBase, db: Session = Depends(get_db),
                                user: UsuarioRespuesta = Depends(get_current_active_user)):
    return crud.create_carga(db, carga)


@app.put("/api/cargas/{carga_id}", response_model=CargaConID, tags=["Cargas"])
async def update_carga_endpoint(carga_id: int, carga: CargaActualizada, db: Session = Depends(get_db),
                                user: UsuarioRespuesta = Depends(get_current_active_user)):
    db_carga = crud.update_carga(db, carga_id, carga)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro de carga no encontrado para actualizar")
    return db_carga


@app.delete("/api/cargas/{carga_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Cargas"])
async def delete_carga_endpoint(carga_id: int, db: Session = Depends(get_db),
                                user: UsuarioRespuesta = Depends(get_current_active_user)):
    success = crud.delete_carga_to_history(db, carga_id)
    if not success:
        raise HTTPException(status_code=404, detail="Registro de carga no encontrado para eliminar")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------- CRUD: ESTACIONES DE CARGA ---------------------

@app.get("/api/estaciones", response_model=List[EstacionConID], tags=["Estaciones"])
async def read_estaciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                          user: UsuarioRespuesta = Depends(get_current_active_user)):
    estaciones = crud.get_estaciones(db, skip=skip, limit=limit)
    return estaciones


@app.get("/api/estaciones/{estacion_id}", response_model=EstacionConID, tags=["Estaciones"])
async def read_estacion(estacion_id: int, db: Session = Depends(get_db),
                        user: UsuarioRespuesta = Depends(get_current_active_user)):
    db_estacion = crud.get_estacion(db, estacion_id=estacion_id)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación de carga no encontrada")
    return db_estacion


@app.post("/api/estaciones", response_model=EstacionConID, status_code=status.HTTP_201_CREATED, tags=["Estaciones"])
async def create_estacion_endpoint(estacion: EstacionBase, db: Session = Depends(get_db),
                                   user: UsuarioRespuesta = Depends(get_current_active_user)):
    return crud.create_estacion(db, estacion)


@app.put("/api/estaciones/{estacion_id}", response_model=EstacionConID, tags=["Estaciones"])
async def update_estacion_endpoint(estacion_id: int, estacion: EstacionActualizada, db: Session = Depends(get_db),
                                   user: UsuarioRespuesta = Depends(get_current_active_user)):
    db_estacion = crud.update_estacion(db, estacion_id, estacion)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación de carga no encontrada para actualizar")
    return db_estacion


@app.delete("/api/estaciones/{estacion_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Estaciones"])
async def delete_estacion_endpoint(estacion_id: int, db: Session = Depends(get_db),
                                   user: UsuarioRespuesta = Depends(get_current_active_user)):
    success = crud.delete_estacion_to_history(db, estacion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Estación de carga no encontrada para eliminar")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------- VISTAS DE HISTORIAL (ELIMINADOS) ---------------------

@app.get("/deleted_cars", response_class=HTMLResponse, include_in_schema=False)
async def deleted_cars_page(request: Request, db: Session = Depends(get_db),
                            user: UsuarioRespuesta = Depends(get_current_active_user)):
    autos_eliminados = crud.get_autos_eliminados(db)
    return templates.TemplateResponse("deleted_cars.html",
                                      {"request": request, "autos_eliminados": autos_eliminados, "current_user": user})


@app.get("/deleted_charges", response_class=HTMLResponse, include_in_schema=False)
async def deleted_charges_page(request: Request, db: Session = Depends(get_db),
                               user: UsuarioRespuesta = Depends(get_current_active_user)):
    cargas_eliminadas = crud.get_cargas_eliminadas(db)
    return templates.TemplateResponse("deleted_charges.html",
                                      {"request": request, "cargas_eliminadas": cargas_eliminadas,
                                       "current_user": user})


@app.get("/deleted_stations", response_class=HTMLResponse, include_in_schema=False)
async def deleted_stations_page(request: Request, db: Session = Depends(get_db),
                                user: UsuarioRespuesta = Depends(get_current_active_user)):
    estaciones_eliminadas = crud.get_estaciones_eliminadas(db)
    return templates.TemplateResponse("deleted_stations.html",
                                      {"request": request, "estaciones_eliminadas": estaciones_eliminadas,
                                       "current_user": user})


# --------------------- ESTADÍSTICAS (API) ---------------------

@app.get("/api/statistics/cars_by_brand", tags=["Estadísticas"])
async def get_cars_by_brand_stats(db: Session = Depends(get_db)):
    """Cuenta el número de autos por marca."""
    stats = db.query(
        models_sql.AutoElectricoSQL.marca,
        func.count(models_sql.AutoElectricoSQL.id)
    ).group_by(models_sql.AutoElectricoSQL.marca).all()
    return [{"marca": brand, "count": count} for brand, count in stats]


@app.get("/api/statistics/station_power_by_connector_type", tags=["Estadísticas"])
async def get_station_power_by_connector_type_stats(db: Session = Depends(get_db)):
    """Calcula la potencia promedio de estaciones por tipo de conector."""
    stats = db.query(
        models_sql.EstacionSQL.tipo_conector,
        func.avg(models_sql.EstacionSQL.potencia_kw)
    ).group_by(models_sql.EstacionSQL.tipo_conector).all()
    return [
        {"tipo_conector": ct, "avg_potencia_kw": round(ap, 2)}
        for ct, ap in stats
    ]


@app.get("/api/statistics/charge_difficulty_distribution", tags=["Estadísticas"])
async def get_charge_difficulty_distribution(db: Session = Depends(get_db)):
    """Calcula la distribución de los registros de carga por dificultad."""
    stats = db.query(
        models_sql.CargaSQL.dificultad_carga,
        func.count(models_sql.CargaSQL.id)
    ).group_by(models_sql.CargaSQL.dificultad_carga).all()
    return [
        {"dificultad": diff.capitalize(), "count": count}
        for diff, count in stats
    ]


@app.get("/api/statistics/autonomy_vs_battery", tags=["Estadísticas"])
async def get_autonomy_vs_battery(db: Session = Depends(get_db)):
    """Retorna los datos de autonomía y capacidad de batería para un scatter plot."""
    data = db.query(
        models_sql.AutoElectricoSQL.modelo,
        models_sql.AutoElectricoSQL.capacidad_bateria_kwh,
        models_sql.AutoElectricoSQL.autonomia_km
    ).limit(200).all()

    return [
        {"modelo": model, "bateria": b, "autonomia": a}
        for model, b, a in data
    ]


# --------------------- INICIO DE LA APP (uvicorn/gunicorn) ---------------------

if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando Uvicorn en modo desarrollo. Visita http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)