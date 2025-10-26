# main.py - CORREGIDO

from fastapi import FastAPI, HTTPException, Depends, Request, File, UploadFile, Form, status
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, Dict, Any
import os
import logging
import sys
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
from sqlalchemy import func

# Importaciones de modelos
from modelos import AutoElectrico, AutoElectricoConID
from modelos import CargaBase, CargaConID, CargaActualizada
from modelos import EstacionBase, EstacionConID, EstacionActualizada
from modelos import UsuarioRegistro, UsuarioLogin, CambioPassword

from database import get_db, engine, Base
import models_sql
import crud
import crud_usuarios as user_crud
from auth_utils import get_password_hash, verify_password, get_current_user

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

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

# Crear tablas
Base.metadata.create_all(bind=engine)


# --------------------- MIDDLEWARE DE AUTENTICACIÓN ---------------------

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    public_paths = ["/", "/register", "/login", "/change_password", "/api/register",
                    "/api/login", "/api/change_password", "/static", "/docs", "/openapi.json"]

    is_public_path = any(request.url.path.startswith(path) for path in public_paths)
    session_cookie = request.cookies.get("session_user")

    if not is_public_path and not session_cookie:
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                                content={"detail": "No autenticado."})
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    response = await call_next(request)
    return response


# --------------------- RUTAS HTML PÚBLICAS ---------------------

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_root_public(request: Request):
    """Página de login/registro"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/change_password", response_class=HTMLResponse)
async def change_password_form(request: Request):
    return templates.TemplateResponse("change_password.html", {"request": request})


# --------------------- RUTAS HTML PROTEGIDAS ---------------------

@app.get("/index", response_class=HTMLResponse)
async def index_page(request: Request, db: Session = Depends(get_db)):
    total_autos = db.query(models_sql.AutoElectricoSQL).count()
    total_estaciones = db.query(models_sql.EstacionSQL).count()
    total_cargas = db.query(models_sql.CargaSQL).count()
    avg_autonomia = db.query(func.avg(models_sql.AutoElectricoSQL.autonomia_km)).scalar()
    avg_autonomia = round(avg_autonomia, 2) if avg_autonomia else 0

    return templates.TemplateResponse("index.html", {
        "request": request,
        "total_autos": total_autos,
        "total_estaciones": total_estaciones,
        "total_cargas": total_cargas,
        "avg_autonomia": avg_autonomia
    })


@app.get("/cars", response_class=HTMLResponse)
async def cars_page(request: Request):
    return templates.TemplateResponse("cars.html", {"request": request})


@app.get("/charges", response_class=HTMLResponse)
async def charges_page(request: Request):
    return templates.TemplateResponse("charges.html", {"request": request})


@app.get("/stations", response_class=HTMLResponse)
async def stations_page(request: Request):
    return templates.TemplateResponse("stations.html", {"request": request})


@app.get("/deleted_cars", response_class=HTMLResponse)
async def deleted_cars_page(request: Request, db: Session = Depends(get_db)):
    autos_eliminados = crud.get_autos_eliminados(db)
    return templates.TemplateResponse("deleted_cars.html",
                                      {"request": request, "autos_eliminados": autos_eliminados})


@app.get("/deleted_charges", response_class=HTMLResponse)
async def deleted_charges_page(request: Request, db: Session = Depends(get_db)):
    cargas_eliminadas = crud.get_cargas_eliminadas(db)
    return templates.TemplateResponse("deleted_charges.html",
                                      {"request": request, "cargas_eliminadas": cargas_eliminadas})


@app.get("/deleted_stations", response_class=HTMLResponse)
async def deleted_stations_page(request: Request, db: Session = Depends(get_db)):
    estaciones_eliminadas = crud.get_estaciones_eliminadas(db)
    return templates.TemplateResponse("deleted_stations.html",
                                      {"request": request, "estaciones_eliminadas": estaciones_eliminadas})


@app.get("/project_objective", response_class=HTMLResponse)
async def project_objective_page(request: Request):
    return templates.TemplateResponse("project_objective.html", {"request": request})


@app.get("/planning_design", response_class=HTMLResponse)
async def planning_design_page(request: Request):
    return templates.TemplateResponse("planning_design.html", {"request": request})


@app.get("/mockups_wireframes", response_class=HTMLResponse)
async def mockups_page(request: Request):
    return templates.TemplateResponse("mockups_wireframes.html", {"request": request})


@app.get("/endpoint_map", response_class=HTMLResponse)
async def endpoints_page(request: Request):
    return templates.TemplateResponse("endpoint_map.html", {"request": request})


@app.get("/developer_info", response_class=HTMLResponse)
async def developer_info_page(request: Request):
    return templates.TemplateResponse("developer_info.html", {"request": request})


@app.get("/statistics_page", response_class=HTMLResponse)
async def statistics_page(request: Request):
    return templates.TemplateResponse("statistics_page.html", {"request": request})


# --------------------- ENDPOINTS DE AUTENTICACIÓN ---------------------

@app.post("/api/register")
async def register_user(
        request: Request,
        nombre: str = Form(...),
        edad: Optional[int] = Form(None),
        correo: str = Form(...),
        cedula: str = Form(...),
        celular: Optional[str] = Form(None),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    try:
        user_data = UsuarioRegistro(
            nombre=nombre, edad=edad, correo=correo,
            cedula=cedula, celular=celular, password=password
        )

        if user_crud.get_user_by_cedula(db, user_data.cedula):
            raise HTTPException(status_code=400, detail="La cédula ya está registrada.")
        if user_crud.get_user_by_correo(db, user_data.correo):
            raise HTTPException(status_code=400, detail="El correo ya está registrado.")

        user_crud.create_user(db, user_data)
        response = RedirectResponse(url="/login?success_message=Registro exitoso. Inicia sesión.",
                                    status_code=status.HTTP_303_SEE_OTHER)
        return response

    except ValueError as e:
        form_data = await request.form()
        return templates.TemplateResponse("register.html",
                                          {"request": request, "error_message": f"Error: {e}",
                                           "form_data": dict(form_data)})
    except HTTPException as e:
        form_data = await request.form()
        return templates.TemplateResponse("register.html",
                                          {"request": request, "error_message": e.detail,
                                           "form_data": dict(form_data)})


@app.post("/api/login")
async def login_user(
        request: Request,
        cedula_o_correo: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user = user_crud.get_user_by_cedula_or_correo(db, cedula_o_correo)

    if user and verify_password(password, user.hashed_password):
        response = RedirectResponse(url="/index", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="session_user", value=user.cedula, max_age=3600, httponly=True)
        return response

    return templates.TemplateResponse("login.html",
                                      {"request": request,
                                       "error_message": "Cédula/Correo o contraseña incorrectos."})


@app.post("/api/change_password")
async def handle_change_password(
        request: Request,
        identificador: str = Form(...),
        password_anterior: Optional[str] = Form(None),
        password_nueva: str = Form(...),
        password_nueva_confirmacion: str = Form(...),
        db: Session = Depends(get_db)
):
    try:
        change_data = CambioPassword(
            identificador=identificador,
            password_anterior=password_anterior,
            password_nueva=password_nueva,
            password_nueva_confirmacion=password_nueva_confirmacion
        )

        user = user_crud.get_user_by_cedula_or_correo(db, change_data.identificador)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        if password_anterior and not verify_password(password_anterior, user.hashed_password):
            raise HTTPException(status_code=400, detail="La contraseña anterior es incorrecta.")

        user_crud.update_user_password(db, user.id, change_data.password_nueva)
        response = RedirectResponse(
            url="/login?success_message=Contraseña actualizada. Inicia sesión.",
            status_code=status.HTTP_303_SEE_OTHER)
        return response

    except ValueError as e:
        form_data = await request.form()
        return templates.TemplateResponse("change_password.html",
                                          {"request": request, "error_message": f"Error: {e}",
                                           "form_data": dict(form_data)})
    except HTTPException as e:
        form_data = await request.form()
        return templates.TemplateResponse("change_password.html",
                                          {"request": request, "error_message": e.detail,
                                           "form_data": dict(form_data)})


# --------------------- ENDPOINTS DE LA API (AUTOS) ---------------------

@app.get("/api/autos/", response_model=List[AutoElectricoConID])
async def read_autos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_autos(db, skip=skip, limit=limit)


@app.get("/api/autos/{auto_id}", response_model=AutoElectricoConID)
async def read_auto(auto_id: int, db: Session = Depends(get_db)):
    db_auto = crud.get_auto(db, auto_id=auto_id)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto


@app.get("/api/autos/search/", response_model=List[AutoElectricoConID])
async def search_auto_by_modelo(modelo: str, db: Session = Depends(get_db)):
    autos = crud.get_auto_by_modelo(db, modelo=modelo)
    if not autos:
        raise HTTPException(status_code=404, detail="No se encontraron autos")
    return autos


@app.post("/api/autos/", response_model=AutoElectricoConID, status_code=201)
async def create_new_auto(auto: AutoElectrico, db: Session = Depends(get_db)):
    try:
        return crud.create_auto(db=db, auto=auto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/autos/{auto_id}", response_model=AutoElectricoConID)
async def update_existing_auto(auto_id: int, auto: AutoElectrico, db: Session = Depends(get_db)):
    db_auto = crud.update_auto(db=db, auto_id=auto_id, auto=auto)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto


@app.patch("/api/autos/{auto_id}", response_model=AutoElectricoConID)
async def patch_existing_auto(auto_id: int, auto: Dict[str, Any], db: Session = Depends(get_db)):
    db_auto = crud.get_auto(db, auto_id)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    for key, value in auto.items():
        if hasattr(db_auto, key):
            setattr(db_auto, key, value)
    db.commit()
    db.refresh(db_auto)
    return db_auto


@app.delete("/api/autos/{auto_id}")
async def delete_existing_auto(auto_id: int, db: Session = Depends(get_db)):
    db_auto = crud.delete_auto(db=db, auto_id=auto_id)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto


# --------------------- ENDPOINTS CARGAS ---------------------

@app.get("/api/cargas/", response_model=List[CargaConID])
async def read_cargas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_cargas(db, skip=skip, limit=limit)


@app.get("/api/cargas/{carga_id}", response_model=CargaConID)
async def read_carga(carga_id: int, db: Session = Depends(get_db)):
    db_carga = crud.get_carga(db, carga_id=carga_id)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return db_carga


@app.get("/api/cargas/search/", response_model=List[CargaConID])
async def search_carga_by_modelo_auto(modelo_auto: str, db: Session = Depends(get_db)):
    cargas = crud.get_carga_by_modelo_auto(db, modelo_auto=modelo_auto)
    if not cargas:
        raise HTTPException(status_code=404, detail="No se encontraron registros")
    return cargas


@app.post("/api/cargas/", response_model=CargaConID, status_code=201)
async def create_new_carga(carga: CargaBase, db: Session = Depends(get_db)):
    return crud.create_carga(db=db, carga=carga)


@app.put("/api/cargas/{carga_id}", response_model=CargaConID)
async def update_existing_carga(carga_id: int, carga: CargaActualizada, db: Session = Depends(get_db)):
    db_carga = crud.update_carga(db=db, carga_id=carga_id, carga=carga)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return db_carga


@app.patch("/api/cargas/{carga_id}", response_model=CargaConID)
async def patch_existing_carga(carga_id: int, carga: Dict[str, Any], db: Session = Depends(get_db)):
    db_carga = crud.get_carga(db, carga_id)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    for key, value in carga.items():
        if hasattr(db_carga, key):
            setattr(db_carga, key, value)
    db.commit()
    db.refresh(db_carga)
    return db_carga


@app.delete("/api/cargas/{carga_id}")
async def delete_existing_carga(carga_id: int, db: Session = Depends(get_db)):
    db_carga = crud.delete_carga(db=db, carga_id=carga_id)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return db_carga


# --------------------- ENDPOINTS ESTACIONES ---------------------

@app.get("/api/estaciones/", response_model=List[EstacionConID])
async def read_estaciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_estaciones(db, skip=skip, limit=limit)


@app.get("/api/estaciones/{estacion_id}", response_model=EstacionConID)
async def read_estacion(estacion_id: int, db: Session = Depends(get_db)):
    db_estacion = crud.get_estacion(db, estacion_id=estacion_id)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    return db_estacion


@app.get("/api/estaciones/search/", response_model=List[EstacionConID])
async def search_estacion_by_nombre(nombre: str, db: Session = Depends(get_db)):
    estaciones = crud.get_estacion_by_nombre(db, nombre=nombre)
    if not estaciones:
        raise HTTPException(status_code=404, detail="No se encontraron estaciones")
    return estaciones


@app.post("/api/estaciones/", response_model=EstacionConID, status_code=201)
async def create_new_estacion(estacion: EstacionBase, db: Session = Depends(get_db)):
    return crud.create_estacion(db=db, estacion=estacion)


@app.put("/api/estaciones/{estacion_id}", response_model=EstacionConID)
async def update_existing_estacion(estacion_id: int, estacion: EstacionActualizada,
                                   db: Session = Depends(get_db)):
    db_estacion = crud.update_estacion(db=db, estacion_id=estacion_id, estacion=estacion)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    return db_estacion


@app.patch("/api/estaciones/{estacion_id}", response_model=EstacionConID)
async def patch_existing_estacion(estacion_id: int, estacion: Dict[str, Any],
                                  db: Session = Depends(get_db)):
    db_estacion = crud.get_estacion(db, estacion_id)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    for key, value in estacion.items():
        if hasattr(db_estacion, key):
            setattr(db_estacion, key, value)
    db.commit()
    db.refresh(db_estacion)
    return db_estacion


@app.delete("/api/estaciones/{estacion_id}")
async def delete_existing_estacion(estacion_id: int, db: Session = Depends(get_db)):
    db_estacion = crud.delete_estacion(db=db, estacion_id=estacion_id)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    return db_estacion


# --------------------- SUBIDA DE IMÁGENES ---------------------

@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_extension = Path(file.filename).suffix
        if file_extension.lower() not in [".png", ".jpg", ".jpeg", ".gif"]:
            raise HTTPException(status_code=400, detail="Formato no soportado")

        unique_filename = f"{os.urandom(16).hex()}{file_extension}"
        file_path = UPLOAD_DIRECTORY / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {"url": f"/static/images/{unique_filename}"}
    except Exception as e:
        logger.error(f"Error al subir imagen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {e}")


# --------------------- ESTADÍSTICAS ---------------------

@app.get("/api/statistics/cars_by_brand")
async def get_cars_by_brand_stats(db: Session = Depends(get_db)):
    stats = db.query(
        models_sql.AutoElectricoSQL.marca,
        func.count(models_sql.AutoElectricoSQL.id)
    ).group_by(models_sql.AutoElectricoSQL.marca).all()
    return [{"marca": brand, "count": count} for brand, count in stats]


@app.get("/api/statistics/station_power_by_connector_type")
async def get_station_power_by_connector_type_stats(db: Session = Depends(get_db)):
    stats = db.query(
        models_sql.EstacionSQL.tipo_conector,
        func.avg(models_sql.EstacionSQL.potencia_kw)
    ).group_by(models_sql.EstacionSQL.tipo_conector).all()
    return [{"tipo_conector": ct, "avg_potencia_kw": round(ap, 2)}
            for ct, ap in stats]


@app.get("/api/statistics/charge_difficulty_distribution")
async def get_charge_difficulty_distribution_stats(db: Session = Depends(get_db)):
    stats = db.query(
        models_sql.CargaSQL.dificultad_carga,
        func.count(models_sql.CargaSQL.id)
    ).group_by(models_sql.CargaSQL.dificultad_carga).all()
    return [{"dificultad": d, "count": c} for d, c in stats]