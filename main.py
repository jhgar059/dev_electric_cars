# main.py
from fastapi import FastAPI, HTTPException, Depends, Request, File, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional, Dict, Any
import os
import logging
import sys
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
from sqlalchemy import func # Importar func para estadísticas

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

# Importaciones de modelos Pydantic (para validación de entrada/salida)
from modelos import AutoElectrico, AutoElectricoConID
from modelos import CargaBase, CargaConID, CargaActualizada
from modelos import EstacionBase, EstacionConID, EstacionActualizada

# Importar la configuración de base de datos y modelos SQL
from database import get_db, engine, Base
import models_sql
import crud # Importar todas las funciones CRUD

# Crear las tablas en la base de datos (redundante si db_init.py ya se ejecuta, pero no hace daño)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Unificada de Autos Eléctricos")

# Configuración de Jinja2Templates para servir archivos HTML
templates = Jinja2Templates(directory="templates") # Asume que tus templates HTML están en una carpeta 'templates'

# Ruta para servir archivos estáticos (ej. CSS, JS, imágenes si no se sirven directamente desde 'static')
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# --------------------- ENDPOINTS PARA VISTAS HTML ---------------------

@app.get("/", response_class=HTMLResponse, summary="Página de Inicio")
async def read_root(request: Request, db: Session = Depends(get_db)):
    """
    Muestra la página principal de la aplicación con la autonomía promedio.
    """
    average_autonomy = crud.get_average_autonomy(db)
    return templates.TemplateResponse("index.html", {"request": request, "average_autonomy": average_autonomy})

@app.get("/cars", response_class=HTMLResponse, summary="Página de Gestión de Autos")
async def cars_page(request: Request):
    """
    Muestra la página para gestionar autos eléctricos (CRUD).
    """
    return templates.TemplateResponse("cars.html", {"request": request})

@app.get("/charges", response_class=HTMLResponse, summary="Página de Gestión de Cargas")
async def charges_page(request: Request):
    """
    Muestra la página para gestionar registros de dificultad de carga (CRUD).
    """
    return templates.TemplateResponse("charges.html", {"request": request})

@app.get("/stations", response_class=HTMLResponse, summary="Página de Gestión de Estaciones")
async def stations_page(request: Request):
    """
    Muestra la página para gestionar estaciones de carga (CRUD).
    """
    return templates.TemplateResponse("stations.html", {"request": request})

@app.get("/deleted_cars", response_class=HTMLResponse, summary="Página de Autos Eliminados")
async def deleted_cars_page(request: Request, db: Session = Depends(get_db)):
    """
    Muestra el historial de autos eléctricos eliminados.
    """
    autos_eliminados = crud.get_autos_eliminados(db)
    return templates.TemplateResponse("deleted_cars.html", {"request": request, "autos_eliminados": autos_eliminados})

@app.get("/deleted_charges", response_class=HTMLResponse, summary="Página de Cargas Eliminadas")
async def deleted_charges_page(request: Request, db: Session = Depends(get_db)):
    """
    Muestra el historial de registros de carga eliminados.
    """
    try:
        cargas_eliminadas = crud.get_cargas_eliminadas(db)
        return templates.TemplateResponse("deleted_charges.html", {"request": request, "cargas_eliminadas": cargas_eliminadas})
    except Exception as e:
        logger.error(f"Error al cargar la página de cargas eliminadas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor al cargar cargas eliminadas.")


@app.get("/deleted_stations", response_class=HTMLResponse, summary="Página de Estaciones Eliminadas")
async def deleted_stations_page(request: Request, db: Session = Depends(get_db)):
    """
    Muestra el historial de estaciones de carga eliminadas.
    """
    estaciones_eliminadas = crud.get_estaciones_eliminadas(db)
    return templates.TemplateResponse("deleted_stations.html", {"request": request, "estaciones_eliminadas": estaciones_eliminadas})

@app.get("/project_objective", response_class=HTMLResponse, summary="Página Objetivo del Proyecto")
async def project_objective_page(request: Request):
    """
    Muestra la página con el objetivo del proyecto.
    """
    return templates.TemplateResponse("project_objective.html", {"request": request})

@app.get("/developer_info", response_class=HTMLResponse, summary="Página Información del Desarrollador")
async def developer_info_page(request: Request):
    """
    Muestra la página con información sobre el desarrollador.
    """
    return templates.TemplateResponse("developer_info.html", {"request": request})

@app.get("/planning_design", response_class=HTMLResponse, summary="Página de Planeación y Diseño")
async def planning_design_page(request: Request):
    """
    Muestra la página con detalles de la planeación y diseño del proyecto.
    """
    return templates.TemplateResponse("planning_design.html", {"request": request})

@app.get("/mockups_wireframes", response_class=HTMLResponse, summary="Página de Mockups y Wireframes")
async def mockups_wireframes_page(request: Request):
    """
    Muestra la página con los mockups y wireframes del proyecto.
    """
    return templates.TemplateResponse("mockups_wireframes.html", {"request": request})

@app.get("/endpoint_map", response_class=HTMLResponse, summary="Mapa de Endpoints de la API")
async def endpoint_map_page(request: Request):
    """
    Muestra un mapa con todos los endpoints de la API.
    """
    return templates.TemplateResponse("endpoint_map.html", {"request": request})

@app.get("/statistics_page", response_class=HTMLResponse, summary="Página de Estadísticas")
async def statistics_page(request: Request):
    """
    Muestra la página con gráficos y estadísticas.
    """
    return templates.TemplateResponse("statistics_page.html", {"request": request})

# --------------------- ENDPOINTS DE ESTADÍSTICAS (API) ---------------------

@app.get("/api/statistics/cars_by_brand", response_model=Dict[str, int], summary="Estadísticas de Autos por Marca")
async def get_cars_by_brand_stats(db: Session = Depends(get_db)):
    """
    Obtiene el número de autos eléctricos por marca.
    """
    try:
        brand_counts = db.query(models_sql.AutoElectricoSQL.marca, func.count(models_sql.AutoElectricoSQL.marca)) \
                         .group_by(models_sql.AutoElectricoSQL.marca).all()
        return {brand: count for brand, count in brand_counts}
    except Exception as e:
        logger.error(f"Error al obtener estadísticas de autos por marca: {e}")
        raise HTTPException(status_code=500, detail="Error al cargar estadísticas de autos por marca.")

@app.get("/api/statistics/charge_difficulty", response_model=Dict[str, int], summary="Estadísticas de Dificultad de Carga")
async def get_charge_difficulty_stats(db: Session = Depends(get_db)):
    """
    Obtiene el número de registros de carga por nivel de dificultad.
    """
    try:
        difficulty_counts = db.query(models_sql.CargaSQL.dificultad_carga, func.count(models_sql.CargaSQL.dificultad_carga)) \
                             .group_by(models_sql.CargaSQL.dificultad_carga).all()
        return {difficulty: count for difficulty, count in difficulty_counts}
    except Exception as e:
        logger.error(f"Error al obtener estadísticas de dificultad de carga: {e}")
        raise HTTPException(status_code=500, detail="Error al cargar estadísticas de dificultad de carga.")

@app.get("/api/statistics/station_power_distribution", response_model=Dict[str, int], summary="Estadísticas de Distribución de Potencia de Estaciones")
async def get_station_power_distribution(db: Session = Depends(get_db)):
    """
    Obtiene el número de estaciones de carga por tipo de conector.
    """
    try:
        power_distribution = db.query(models_sql.EstacionSQL.tipo_conector, func.count(models_sql.EstacionSQL.tipo_conector)) \
                                .group_by(models_sql.EstacionSQL.tipo_conector).all()
        return {connector_type: count for connector_type, count in power_distribution}
    except Exception as e:
        logger.error(f"Error al obtener estadísticas de distribución de potencia de estaciones: {e}")
        raise HTTPException(status_code=500, detail="Error al cargar estadísticas de distribución de potencia de estaciones.")

@app.get("/api/statistics/average_autonomy", response_model=Dict[str, float], summary="Autonomía Promedio de Autos")
async def get_average_autonomy_api(db: Session = Depends(get_db)):
    """
    Obtiene la autonomía promedio de todos los autos eléctricos.
    """
    try:
        average_autonomy = crud.get_average_autonomy(db)
        return {"average_autonomy": round(average_autonomy, 2)} # Redondear a 2 decimales
    except Exception as e:
        logger.error(f"Error al obtener autonomía promedio: {e}")
        raise HTTPException(status_code=500, detail="Error al cargar la autonomía promedio.")

# --------------------- ENDPOINTS CRUD PARA AUTOS ELÉCTRICOS ---------------------

@app.post("/autos/", response_model=AutoElectricoConID, status_code=201, summary="Crea un nuevo auto eléctrico")
async def create_new_auto(auto: AutoElectrico, db: Session = Depends(get_db)):
    db_auto = crud.create_auto(db=db, auto=auto)
    if db_auto is None:
        raise HTTPException(status_code=400, detail="Ya existe un auto con el mismo modelo y año.")
    return db_auto

@app.get("/autos/", response_model=List[AutoElectricoConID], summary="Obtiene todos los autos eléctricos")
async def read_autos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    autos = crud.get_autos(db, skip=skip, limit=limit)
    return autos

@app.get("/autos/{auto_id}", response_model=AutoElectricoConID, summary="Obtiene un auto eléctrico por ID")
async def read_auto(auto_id: int, db: Session = Depends(get_db)):
    db_auto = crud.get_auto(db, auto_id=auto_id)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto

@app.get("/autos/search/", response_model=List[AutoElectricoConID], summary="Busca autos por modelo")
async def search_auto_by_model(modelo: str, db: Session = Depends(get_db)):
    autos = crud.get_auto_by_modelo(db, modelo=modelo)
    if not autos:
        raise HTTPException(status_code=404, detail=f"No se encontraron autos con el modelo '{modelo}'")
    return autos

@app.put("/autos/{auto_id}", response_model=AutoElectricoConID, summary="Actualiza un auto eléctrico existente")
async def update_existing_auto(auto_id: int, auto: AutoElectrico, db: Session = Depends(get_db)):
    db_auto = crud.update_auto(db=db, auto_id=auto_id, auto=auto)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto

@app.delete("/autos/{auto_id}", response_model=AutoElectricoConID, summary="Elimina un auto eléctrico (lo mueve a eliminados)")
async def delete_existing_auto(auto_id: int, db: Session = Depends(get_db)):
    db_auto = crud.delete_auto(db=db, auto_id=auto_id)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto

# --------------------- ENDPOINTS CRUD PARA CARGAS ---------------------

@app.post("/cargas/", response_model=CargaConID, status_code=201, summary="Crea un nuevo registro de carga")
async def create_new_carga(carga: CargaBase, db: Session = Depends(get_db)):
    db_carga = crud.create_carga(db=db, carga=carga)
    if db_carga is None:
        raise HTTPException(status_code=400, detail="Ya existe un registro de carga para el mismo modelo y tipo de autonomía.")
    return db_carga

@app.get("/cargas/", response_model=List[CargaConID], summary="Obtiene todos los registros de carga")
async def read_cargas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cargas = crud.get_cargas(db, skip=skip, limit=limit)
    return cargas

@app.get("/cargas/{carga_id}", response_model=CargaConID, summary="Obtiene un registro de carga por ID")
async def read_carga(carga_id: int, db: Session = Depends(get_db)):
    db_carga = crud.get_carga(db, carga_id=carga_id)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro de carga no encontrado")
    return db_carga

@app.put("/cargas/{carga_id}", response_model=CargaConID, summary="Actualiza un registro de carga existente")
async def update_existing_carga(carga_id: int, carga: CargaActualizada, db: Session = Depends(get_db)):
    db_carga = crud.update_carga(db=db, carga_id=carga_id, carga=carga)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro de carga no encontrado")
    return db_carga

@app.delete("/cargas/{carga_id}", response_model=CargaConID, summary="Elimina un registro de carga (lo mueve a eliminados)")
async def delete_existing_carga(carga_id: int, db: Session = Depends(get_db)):
    db_carga = crud.delete_carga(db=db, carga_id=carga_id)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro de carga no encontrado")
    return db_carga

# --------------------- ENDPOINTS CRUD PARA ESTACIONES DE CARGA ---------------------

@app.post("/estaciones/", response_model=EstacionConID, status_code=201, summary="Crea una nueva estación de carga")
async def create_new_estacion(estacion: EstacionBase, db: Session = Depends(get_db)):
    db_estacion = crud.create_estacion(db=db, estacion=estacion)
    if db_estacion is None:
        raise HTTPException(status_code=400, detail="Ya existe una estación de carga con el mismo nombre y ubicación.")
    return db_estacion

@app.get("/estaciones/", response_model=List[EstacionConID], summary="Obtiene todas las estaciones de carga")
async def read_estaciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    estaciones = crud.get_estaciones(db, skip=skip, limit=limit)
    return estaciones

@app.get("/estaciones/{estacion_id}", response_model=EstacionConID, summary="Obtiene una estación de carga por ID")
async def read_estacion(estacion_id: int, db: Session = Depends(get_db)):
    db_estacion = crud.get_estacion(db, estacion_id=estacion_id)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación de carga no encontrada")
    return db_estacion

@app.put("/estaciones/{estacion_id}", response_model=EstacionConID, summary="Actualiza una estación de carga existente")
async def update_existing_estacion(estacion_id: int, estacion: EstacionActualizada, db: Session = Depends(get_db)):
    db_estacion = crud.update_estacion(db=db, estacion_id=estacion_id, estacion=estacion)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación de carga no encontrada")
    return db_estacion

@app.delete("/estaciones/{estacion_id}", response_model=EstacionConID, summary="Elimina una estación de carga (la mueve a eliminados)")
async def delete_existing_estacion(estacion_id: int, db: Session = Depends(get_db)):
    db_estacion = crud.delete_estacion(db=db, estacion_id=estacion_id)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación de carga no encontrada")
    return db_estacion


# --------------------- MANEJO DE IMÁGENES (Subida) ---------------------

UPLOAD_DIRECTORY = Path("static/images") # Define un directorio para guardar imágenes
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

@app.post("/upload_image/", summary="Sube una imagen y devuelve su URL")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_extension = Path(file.filename).suffix
        if file_extension.lower() not in [".png", ".jpg", ".jpeg", ".gif"]:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado. Se permiten .png, .jpg, .jpeg, .gif")

        # Genera un nombre de archivo único
        unique_filename = f"{os.urandom(16).hex()}{file_extension}"
        file_path = UPLOAD_DIRECTORY / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Devuelve la URL relativa de la imagen
        return {"filename": unique_filename, "url": f"/static/images/{unique_filename}"}
    except Exception as e:
        logger.error(f"Error al subir imagen: {e}")
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {e}")