# main.py - VERSIÓN COMPLETA CON SISTEMA DE SESIÓN Y LOGOUT

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

# Importaciones de modelos
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
from auth_utils import get_password_hash, verify_password

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
    description="API RESTful para la gestión de datos de autos y estaciones de carga eléctricas.",
    version="1.0.0",
)


# Manejador global de excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error global capturado: {exc}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error interno del servidor: {str(exc)}"}
    )


# Configuración de directorios
templates = Jinja2Templates(directory="templates")
UPLOAD_DIRECTORY = Path("static/images")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")


# --------------------- FUNCIÓN HELPER PARA VERIFICAR SESIÓN ---------------------

def check_user_session(request: Request) -> dict:
    """
    Verifica si el usuario tiene una sesión activa.
    Retorna un diccionario con información de la sesión.
    """
    user_cedula = request.cookies.get("user_session")

    if user_cedula:
        return {
            "logged_in": True,
            "user_cedula": user_cedula
        }
    else:
        return {
            "logged_in": False,
            "user_cedula": None
        }


# --------------------- VISTAS HTML SIN AUTENTICACIÓN ---------------------

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def welcome_page(request: Request):
    try:
        session_info = check_user_session(request)
        return templates.TemplateResponse("welcome.html", {
            "request": request,
            **session_info
        })
    except Exception as e:
        logger.error(f"Error en welcome_page: {e}", exc_info=True)
        raise


@app.get("/index", response_class=HTMLResponse, include_in_schema=False)
async def index_page(request: Request, db: Session = Depends(get_db)):
    """Página de inicio con estadísticas - PÚBLICA"""
    try:
        session_info = check_user_session(request)

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
            "is_home_page": True,
            **session_info
        })
    except Exception as e:
        logger.error(f"Error en index_page: {e}", exc_info=True)
        raise


@app.get("/project_objective", response_class=HTMLResponse, include_in_schema=False)
async def project_objective_page(request: Request):
    session_info = check_user_session(request)
    return templates.TemplateResponse("project_objective.html", {
        "request": request,
        **session_info
    })


@app.get("/mockups_wireframes", response_class=HTMLResponse, include_in_schema=False)
async def mockups_wireframes_page(request: Request):
    session_info = check_user_session(request)
    return templates.TemplateResponse("mockups_wireframes.html", {
        "request": request,
        **session_info
    })


@app.get("/endpoint_map", response_class=HTMLResponse, include_in_schema=False)
async def endpoint_map_page(request: Request):
    session_info = check_user_session(request)
    return templates.TemplateResponse("endpoint_map.html", {
        "request": request,
        **session_info
    })


@app.get("/developer_info", response_class=HTMLResponse, include_in_schema=False)
async def developer_info_page(request: Request):
    session_info = check_user_session(request)
    return templates.TemplateResponse("developer_info.html", {
        "request": request,
        **session_info
    })


@app.get("/planning_design", response_class=HTMLResponse, include_in_schema=False)
async def planning_design_page(request: Request):
    session_info = check_user_session(request)
    return templates.TemplateResponse("planning_design.html", {
        "request": request,
        **session_info
    })


# --------------------- AUTENTICACIÓN Y REGISTRO ---------------------

@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error_message": None
    })


@app.get("/register", response_class=HTMLResponse, include_in_schema=False)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {
        "request": request,
        "error_message": None,
        "form_data": {}
    })


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
        logger.info(f"Intento de registro para: {correo}")

        # Validaciones de existencia
        existing_user = user_crud.get_user_by_cedula(db, cedula)
        if existing_user:
            logger.warning(f"Cédula ya registrada: {cedula}")
            raise HTTPException(status_code=400, detail="La cédula ya está registrada.")

        existing_email = user_crud.get_user_by_correo(db, correo)
        if existing_email:
            logger.warning(f"Correo ya registrado: {correo}")
            raise HTTPException(status_code=400, detail="El correo ya está registrado.")

        # Validar el modelo Pydantic
        new_user = UsuarioRegistro(**user_data)

        # Crear usuario
        created_user = user_crud.create_user(db, new_user)
        logger.info(f"Usuario registrado exitosamente: {created_user.cedula}")

        return RedirectResponse(
            url="/login?success_message=Registro%20exitoso.%20Ahora%20puedes%20iniciar%20sesión.",
            status_code=status.HTTP_302_FOUND
        )

    except HTTPException as e:
        logger.error(f"HTTPException en registro: {e.detail}")
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error_message": e.detail, "form_data": user_data},
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Error inesperado en registro: {e}", exc_info=True)
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error_message": f"Error interno: {str(e)}",
                "form_data": user_data
            },
            status_code=500
        )


@app.post("/api/login", response_class=HTMLResponse, include_in_schema=False)
async def login_for_access_token(
        request: Request,
        db: Session = Depends(get_db),
        username: str = Form(...),
        password: str = Form(...)
):
    """Endpoint para iniciar sesión - FORMULARIO HTML"""
    try:
        logger.info(f"Intento de login para: {username}")

        # Buscar usuario
        user = user_crud.get_user_by_cedula_or_correo(db, username)

        if not user:
            logger.warning(f"Usuario no encontrado: {username}")
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error_message": "Credenciales incorrectas"
                },
                status_code=401
            )

        # Verificar contraseña
        logger.debug(f"Verificando contraseña para usuario: {user.cedula}")
        password_valid = verify_password(password, user.hashed_password)

        if not password_valid:
            logger.warning(f"Contraseña incorrecta para: {username}")
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error_message": "Credenciales incorrectas"
                },
                status_code=401
            )

        # Verificar usuario activo
        if not user.activo:
            logger.warning(f"Usuario inactivo intentó login: {username}")
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error_message": "Usuario inactivo. Contacte al administrador."
                },
                status_code=403
            )

        # Login exitoso - Crear sesión con cookie
        logger.info(f"Login exitoso para: {user.cedula}")

        # Crear respuesta de redirección
        response = RedirectResponse(url="/index", status_code=status.HTTP_302_FOUND)

        # Establecer cookie de sesión (válida por 7 días)
        response.set_cookie(
            key="user_session",
            value=user.cedula,
            max_age=7 * 24 * 60 * 60,  # 7 días en segundos
            httponly=True,  # Seguridad: no accesible desde JavaScript
            samesite="lax"  # Protección CSRF
        )

        return response

    except Exception as e:
        logger.error(f"Error crítico en login: {e}", exc_info=True)
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error_message": f"Error del servidor: {str(e)}"
            },
            status_code=500
        )


@app.get("/change_password", response_class=HTMLResponse, include_in_schema=False)
async def change_password_form(request: Request):
    session_info = check_user_session(request)
    return templates.TemplateResponse(
        "change_password.html",
        {
            "request": request,
            "error_message": None,
            "form_data": {},
            **session_info
        }
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
        logger.info(f"Intento de cambio de contraseña para: {identificador}")

        # 1. Validar modelo Pydantic
        pass_change = CambioPassword(**form_data)

        # 2. Buscar usuario
        user = user_crud.get_user_by_cedula_or_correo(db, identificador)
        if user is None:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        # 3. Verificar contraseña anterior
        if user.hashed_password:
            if not password_anterior:
                raise HTTPException(status_code=400, detail="Debes ingresar la contraseña anterior.")
            if not verify_password(password_anterior, user.hashed_password):
                raise HTTPException(status_code=401, detail="Contraseña anterior incorrecta.")

        # 4. Actualizar contraseña
        user_crud.update_user_password(db, user.id, pass_change.password_nueva)
        logger.info(f"Contraseña actualizada para: {identificador}")

        return RedirectResponse(
            url="/login?success_message=Contraseña%20actualizada%20exitosamente.",
            status_code=status.HTTP_302_FOUND
        )

    except HTTPException as e:
        logger.error(f"HTTPException en cambio de contraseña: {e.detail}")
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "error_message": e.detail, "form_data": form_data},
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Error en cambio de contraseña: {e}", exc_info=True)
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "error_message": f"Error: {str(e)}", "form_data": form_data},
            status_code=500
        )


@app.get("/api/logout")
async def logout():
    """Cerrar sesión - Elimina la cookie de sesión"""
    logger.info("Usuario cerrando sesión")

    # Crear respuesta de redirección
    response = RedirectResponse(
        url="/login?success_message=Sesión%20cerrada%20exitosamente.",
        status_code=status.HTTP_302_FOUND
    )

    # Eliminar la cookie de sesión
    response.delete_cookie(key="user_session")

    return response


# --------------------- PÁGINAS PROTEGIDAS (SIN PROTECCIÓN POR AHORA) ---------------------

@app.get("/cars", response_class=HTMLResponse, include_in_schema=False)
async def cars_page(request: Request):
    session_info = check_user_session(request)
    return templates.TemplateResponse("cars.html", {
        "request": request,
        **session_info
    })


@app.get("/charges", response_class=HTMLResponse, include_in_schema=False)
async def charges_page(request: Request):
    session_info = check_user_session(request)
    return templates.TemplateResponse("charges.html", {
        "request": request,
        **session_info
    })


@app.get("/stations", response_class=HTMLResponse, include_in_schema=False)
async def stations_page(request: Request):
    session_info = check_user_session(request)
    return templates.TemplateResponse("stations.html", {
        "request": request,
        **session_info
    })


@app.get("/statistics_page", response_class=HTMLResponse, include_in_schema=False)
async def statistics_page(request: Request):
    session_info = check_user_session(request)
    return templates.TemplateResponse("statistics_page.html", {
        "request": request,
        **session_info
    })


@app.get("/deleted_cars", response_class=HTMLResponse, include_in_schema=False)
async def deleted_cars_page(request: Request, db: Session = Depends(get_db)):
    session_info = check_user_session(request)
    autos_eliminados = crud.get_autos_eliminados(db)
    return templates.TemplateResponse("deleted_cars.html", {
        "request": request,
        "autos_eliminados": autos_eliminados,
        **session_info
    })


@app.get("/deleted_charges", response_class=HTMLResponse, include_in_schema=False)
async def deleted_charges_page(request: Request, db: Session = Depends(get_db)):
    session_info = check_user_session(request)
    cargas_eliminadas = crud.get_cargas_eliminadas(db)
    return templates.TemplateResponse("deleted_charges.html", {
        "request": request,
        "cargas_eliminadas": cargas_eliminadas,
        **session_info
    })


@app.get("/deleted_stations", response_class=HTMLResponse, include_in_schema=False)
async def deleted_stations_page(request: Request, db: Session = Depends(get_db)):
    session_info = check_user_session(request)
    estaciones_eliminadas = crud.get_estaciones_eliminadas(db)
    return templates.TemplateResponse("deleted_stations.html", {
        "request": request,
        "estaciones_eliminadas": estaciones_eliminadas,
        **session_info
    })


# --------------------- API ENDPOINTS AUTOS ---------------------

@app.get("/api/autos", response_model=List[AutoElectricoConID], tags=["Autos"])
async def read_autos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_autos(db, skip=skip, limit=limit)


@app.get("/api/autos/search/", response_model=List[AutoElectricoConID], tags=["Autos"])
async def search_autos(modelo: str, db: Session = Depends(get_db)):
    autos = crud.get_auto_by_modelo(db, modelo)
    if not autos:
        raise HTTPException(status_code=404, detail="No se encontraron autos")
    return autos


@app.get("/api/autos/{auto_id}", response_model=AutoElectricoConID, tags=["Autos"])
async def read_auto(auto_id: int, db: Session = Depends(get_db)):
    db_auto = crud.get_auto(db, auto_id=auto_id)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto


@app.post("/api/autos", response_model=AutoElectricoConID, status_code=201, tags=["Autos"])
async def create_auto_endpoint(auto: AutoElectrico, db: Session = Depends(get_db)):
    try:
        return crud.create_auto(db, auto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/autos/{auto_id}", response_model=AutoElectricoConID, tags=["Autos"])
async def update_auto_endpoint(auto_id: int, auto: AutoActualizado, db: Session = Depends(get_db)):
    db_auto = crud.update_auto(db, auto_id, auto)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto


@app.delete("/api/autos/{auto_id}", status_code=204, tags=["Autos"])
async def delete_auto_endpoint(auto_id: int, db: Session = Depends(get_db)):
    success = crud.delete_auto(db, auto_id)
    if not success:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return Response(status_code=204)


# --------------------- API ENDPOINTS CARGAS ---------------------

@app.get("/api/cargas", response_model=List[CargaConID], tags=["Cargas"])
async def read_cargas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_cargas(db, skip=skip, limit=limit)


@app.get("/api/cargas/search/", response_model=List[CargaConID], tags=["Cargas"])
async def search_cargas(modelo_auto: str, db: Session = Depends(get_db)):
    cargas = crud.get_carga_by_modelo(db, modelo_auto)
    if not cargas:
        raise HTTPException(status_code=404, detail="No se encontraron cargas")
    return cargas


@app.get("/api/cargas/{carga_id}", response_model=CargaConID, tags=["Cargas"])
async def read_carga(carga_id: int, db: Session = Depends(get_db)):
    db_carga = crud.get_carga(db, carga_id=carga_id)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Carga no encontrada")
    return db_carga


@app.post("/api/cargas", response_model=CargaConID, status_code=201, tags=["Cargas"])
async def create_carga_endpoint(carga: CargaBase, db: Session = Depends(get_db)):
    return crud.create_carga(db, carga)


@app.put("/api/cargas/{carga_id}", response_model=CargaConID, tags=["Cargas"])
async def update_carga_endpoint(carga_id: int, carga: CargaActualizada, db: Session = Depends(get_db)):
    db_carga = crud.update_carga(db, carga_id, carga)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Carga no encontrada")
    return db_carga


@app.delete("/api/cargas/{carga_id}", status_code=204, tags=["Cargas"])
async def delete_carga_endpoint(carga_id: int, db: Session = Depends(get_db)):
    success = crud.delete_carga(db, carga_id)
    if not success:
        raise HTTPException(status_code=404, detail="Carga no encontrada")
    return Response(status_code=204)


# --------------------- API ENDPOINTS ESTACIONES ---------------------

@app.get("/api/estaciones", response_model=List[EstacionConID], tags=["Estaciones"])
async def read_estaciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_estaciones(db, skip=skip, limit=limit)


@app.get("/api/estaciones/search/", response_model=List[EstacionConID], tags=["Estaciones"])
async def search_estaciones(nombre: str, db: Session = Depends(get_db)):
    estaciones = crud.get_estacion_by_nombre(db, nombre)
    if not estaciones:
        raise HTTPException(status_code=404, detail="No se encontraron estaciones")
    return estaciones


@app.get("/api/estaciones/{estacion_id}", response_model=EstacionConID, tags=["Estaciones"])
async def read_estacion(estacion_id: int, db: Session = Depends(get_db)):
    db_estacion = crud.get_estacion(db, estacion_id=estacion_id)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    return db_estacion


@app.post("/api/estaciones", response_model=EstacionConID, status_code=201, tags=["Estaciones"])
async def create_estacion_endpoint(estacion: EstacionBase, db: Session = Depends(get_db)):
    return crud.create_estacion(db, estacion)


@app.put("/api/estaciones/{estacion_id}", response_model=EstacionConID, tags=["Estaciones"])
async def update_estacion_endpoint(estacion_id: int, estacion: EstacionActualizada, db: Session = Depends(get_db)):
    db_estacion = crud.update_estacion(db, estacion_id, estacion)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    return db_estacion


@app.delete("/api/estaciones/{estacion_id}", status_code=204, tags=["Estaciones"])
async def delete_estacion_endpoint(estacion_id: int, db: Session = Depends(get_db)):
    success = crud.delete_estacion(db, estacion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    return Response(status_code=204)


# --------------------- UPLOAD IMAGEN ---------------------

@app.post("/api/upload-image")
@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...)):
    """Sube una imagen y devuelve su URL"""
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="El archivo no es una imagen")

        MAX_FILE_SIZE = 5 * 1024 * 1024
        buffer = await file.read()

        if len(buffer) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Imagen muy grande (máx 5MB)")

        suffix = Path(file.filename).suffix if file.filename else ''
        unique_filename = f"{uuid.uuid4()}{suffix}"
        file_path = UPLOAD_DIRECTORY / unique_filename

        with open(file_path, "wb") as f:
            f.write(buffer)

        return {"url": f"/static/images/{unique_filename}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al subir imagen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# --------------------- ESTADÍSTICAS ---------------------

@app.get("/api/statistics/cars_by_brand", tags=["Estadísticas"])
async def get_cars_by_brand_stats(db: Session = Depends(get_db)):
    stats = db.query(
        models_sql.AutoElectricoSQL.marca,
        func.count(models_sql.AutoElectricoSQL.id)
    ).group_by(models_sql.AutoElectricoSQL.marca).all()
    return [{"marca": brand, "count": count} for brand, count in stats]


@app.get("/api/statistics/station_power_by_connector_type", tags=["Estadísticas"])
async def get_station_power_by_connector_type_stats(db: Session = Depends(get_db)):
    stats = db.query(
        models_sql.EstacionSQL.tipo_conector,
        func.avg(models_sql.EstacionSQL.potencia_kw)
    ).group_by(models_sql.EstacionSQL.tipo_conector).all()
    return [
        {"tipo_conector": ct, "avg_potencia_kw": round(ap, 2) if ap else 0}
        for ct, ap in stats
    ]


@app.get("/api/statistics/charge_difficulty_distribution", tags=["Estadísticas"])
async def get_charge_difficulty_distribution(db: Session = Depends(get_db)):
    stats = db.query(
        models_sql.CargaSQL.dificultad_carga,
        func.count(models_sql.CargaSQL.id)
    ).group_by(models_sql.CargaSQL.dificultad_carga).all()
    return [
        {"dificultad": diff.capitalize(), "count": count}
        for diff, count in stats
    ]


# --------------------- HEALTH CHECK ---------------------

@app.get("/health")
async def health_check():
    """Endpoint para verificar que la aplicación está funcionando"""
    return {"status": "healthy", "message": "La aplicacion está funcionando correctamente"}


if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando servidor en modo desarrollo")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")