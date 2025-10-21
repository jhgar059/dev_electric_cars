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
from sqlalchemy import func  # Importar func para estadísticas
import os
from sqlalchemy import create_engine

# ✅ CORRECTO - Lee la variable de entorno
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

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
import crud  # Importar todas las funciones CRUD

# Crear las tablas en la base de datos (redundante si db_init.py ya se ejecuta, pero no hace daño)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Unificada de Autos Eléctricos")

# Configuración de Jinja2Templates para servir archivos HTML
templates = Jinja2Templates(directory="templates")


# Middleware para manejar errores 404 para las rutas de la API (no para las HTML)
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": "No encontrado. Por favor, verifica la URL de la API."},
        )
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


# --------------------- RUTAS DE PÁGINAS HTML (FRONTEND) ---------------------

@app.get("/", response_class=HTMLResponse, summary="Muestra la página de inicio")
async def read_root(request: Request, db: Session = Depends(get_db)):
    total_autos = db.query(models_sql.AutoElectricoSQL).count()
    total_estaciones = db.query(models_sql.EstacionSQL).count()
    total_cargas = db.query(models_sql.CargaSQL).count()

    # Calcular autonomía promedio
    avg_autonomia = db.query(func.avg(models_sql.AutoElectricoSQL.autonomia_km)).scalar()
    avg_autonomia = round(avg_autonomia, 2) if avg_autonomia else 0

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "total_autos": total_autos,
            "total_estaciones": total_estaciones,
            "total_cargas": total_cargas,
            "avg_autonomia": avg_autonomia
        }
    )


@app.get("/cars", response_class=HTMLResponse, summary="Muestra la página de gestión de autos")
async def cars_page(request: Request):
    return templates.TemplateResponse("cars.html", {"request": request})


@app.get("/charges", response_class=HTMLResponse, summary="Muestra la página de gestión de cargas")
async def charges_page(request: Request):
    return templates.TemplateResponse("charges.html", {"request": request})


@app.get("/stations", response_class=HTMLResponse, summary="Muestra la página de gestión de estaciones")
async def stations_page(request: Request):
    return templates.TemplateResponse("stations.html", {"request": request})


@app.get("/deleted_cars", response_class=HTMLResponse, summary="Muestra el historial de autos eliminados")
async def deleted_cars_page(request: Request, db: Session = Depends(get_db)):
    autos_eliminados = crud.get_autos_eliminados(db)
    return templates.TemplateResponse("deleted_cars.html", {"request": request, "autos_eliminados": autos_eliminados})


@app.get("/deleted_charges", response_class=HTMLResponse, summary="Muestra el historial de cargas eliminadas")
async def deleted_charges_page(request: Request, db: Session = Depends(get_db)):
    cargas_eliminadas = crud.get_cargas_eliminadas(db)
    return templates.TemplateResponse("deleted_charges.html",
                                      {"request": request, "cargas_eliminadas": cargas_eliminadas})


@app.get("/deleted_stations", response_class=HTMLResponse, summary="Muestra el historial de estaciones eliminadas")
async def deleted_stations_page(request: Request, db: Session = Depends(get_db)):
    estaciones_eliminadas = crud.get_estaciones_eliminadas(db)
    return templates.TemplateResponse("deleted_stations.html",
                                      {"request": request, "estaciones_eliminadas": estaciones_eliminadas})


@app.get("/project_objective", response_class=HTMLResponse, summary="Muestra el objetivo del proyecto")
async def project_objective_page(request: Request):
    return templates.TemplateResponse("project_objective.html", {"request": request})


@app.get("/planning_design", response_class=HTMLResponse, summary="Muestra la página de planeación y diseño")
async def planning_design_page(request: Request):
    return templates.TemplateResponse("planning_design.html", {"request": request})


@app.get("/mockups_wireframes", response_class=HTMLResponse, summary="Muestra la página de mockups y wireframes")
async def mockups_wireframes_page(request: Request):
    return templates.TemplateResponse("mockups_wireframes.html", {"request": request})


@app.get("/endpoint_map", response_class=HTMLResponse, summary="Muestra el mapa de endpoints de la API")
async def endpoint_map_page(request: Request):
    return templates.TemplateResponse("endpoint_map.html", {"request": request})


@app.get("/developer_info", response_class=HTMLResponse, summary="Muestra información sobre el desarrollador")
async def developer_info_page(request: Request):
    return templates.TemplateResponse("developer_info.html", {"request": request})


@app.get("/statistics_page", response_class=HTMLResponse, summary="Muestra la página de estadísticas y gráficos")
async def statistics_page(request: Request):
    return templates.TemplateResponse("statistics_page.html", {"request": request})


# --------------------- ENDPOINTS DE LA API (AUTOS) ---------------------

@app.get("/api/autos/", response_model=List[AutoElectricoConID], summary="Obtener todos los autos eléctricos")
async def read_autos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    autos = crud.get_autos(db, skip=skip, limit=limit)
    return autos


@app.get("/api/autos/{auto_id}", response_model=AutoElectricoConID, summary="Obtener un auto eléctrico por ID")
async def read_auto(auto_id: int, db: Session = Depends(get_db)):
    db_auto = crud.get_auto(db, auto_id=auto_id)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto


@app.get("/api/autos/search/", response_model=List[AutoElectricoConID],
         summary="Buscar autos por modelo (búsqueda parcial)")
async def search_auto_by_modelo(modelo: str, db: Session = Depends(get_db)):
    autos = crud.get_auto_by_modelo(db, modelo=modelo)
    if not autos:
        raise HTTPException(status_code=404, detail="No se encontraron autos con ese modelo")
    return autos


@app.post("/api/autos/", response_model=AutoElectricoConID, status_code=201, summary="Crear un nuevo auto eléctrico")
async def create_new_auto(auto: AutoElectrico, db: Session = Depends(get_db)):
    try:
        return crud.create_auto(db=db, auto=auto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/autos/{auto_id}", response_model=AutoElectricoConID, summary="Actualizar un auto eléctrico existente")
async def update_existing_auto(auto_id: int, auto: AutoElectrico, db: Session = Depends(get_db)):
    db_auto = crud.update_auto(db=db, auto_id=auto_id, auto=auto)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto


@app.patch("/api/autos/{auto_id}", response_model=AutoElectricoConID,
           summary="Actualizar parcialmente un auto eléctrico")
async def patch_existing_auto(auto_id: int, auto: Dict[str, Any], db: Session = Depends(get_db)):
    db_auto = crud.get_auto(db, auto_id)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")

    # Actualizar solo los campos proporcionados
    for key, value in auto.items():
        if hasattr(db_auto, key):
            setattr(db_auto, key, value)
    db.commit()
    db.refresh(db_auto)
    return db_auto


@app.delete("/api/autos/{auto_id}", summary="Eliminar un auto eléctrico (lo mueve al historial)")
async def delete_existing_auto(auto_id: int, db: Session = Depends(get_db)):
    db_auto = crud.delete_auto(db=db, auto_id=auto_id)
    if db_auto is None:
        raise HTTPException(status_code=404, detail="Auto no encontrado")
    return db_auto


# --------------------- ENDPOINTS DE LA API (CARGAS) ---------------------

@app.get("/api/cargas/", response_model=List[CargaConID], summary="Obtener todos los registros de carga")
async def read_cargas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cargas = crud.get_cargas(db, skip=skip, limit=limit)
    return cargas


@app.get("/api/cargas/{carga_id}", response_model=CargaConID, summary="Obtener un registro de carga por ID")
async def read_carga(carga_id: int, db: Session = Depends(get_db)):
    db_carga = crud.get_carga(db, carga_id=carga_id)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro de carga no encontrado")
    return db_carga


@app.get("/api/cargas/search/", response_model=List[CargaConID], summary="Buscar registros de carga por modelo de auto")
async def search_carga_by_modelo_auto(modelo_auto: str, db: Session = Depends(get_db)):
    cargas = crud.get_carga_by_modelo_auto(db, modelo_auto=modelo_auto)
    if not cargas:
        raise HTTPException(status_code=404, detail="No se encontraron registros de carga para ese modelo de auto")
    return cargas


@app.post("/api/cargas/", response_model=CargaConID, status_code=201, summary="Crear un nuevo registro de carga")
async def create_new_carga(carga: CargaBase, db: Session = Depends(get_db)):
    return crud.create_carga(db=db, carga=carga)


@app.put("/api/cargas/{carga_id}", response_model=CargaConID, summary="Actualizar un registro de carga existente")
async def update_existing_carga(carga_id: int, carga: CargaActualizada, db: Session = Depends(get_db)):
    db_carga = crud.update_carga(db=db, carga_id=carga_id, carga=carga)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro de carga no encontrado")
    return db_carga


@app.patch("/api/cargas/{carga_id}", response_model=CargaConID, summary="Actualizar parcialmente un registro de carga")
async def patch_existing_carga(carga_id: int, carga: Dict[str, Any], db: Session = Depends(get_db)):
    db_carga = crud.get_carga(db, carga_id)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro de carga no encontrado")

    for key, value in carga.items():
        if hasattr(db_carga, key):
            setattr(db_carga, key, value)
    db.commit()
    db.refresh(db_carga)
    return db_carga


@app.delete("/api/cargas/{carga_id}", summary="Eliminar un registro de carga (lo mueve al historial)")
async def delete_existing_carga(carga_id: int, db: Session = Depends(get_db)):
    db_carga = crud.delete_carga(db=db, carga_id=carga_id)
    if db_carga is None:
        raise HTTPException(status_code=404, detail="Registro de carga no encontrado")
    return db_carga


# --------------------- ENDPOINTS DE LA API (ESTACIONES) ---------------------

@app.get("/api/estaciones/", response_model=List[EstacionConID], summary="Obtener todas las estaciones de carga")
async def read_estaciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    estaciones = crud.get_estaciones(db, skip=skip, limit=limit)
    return estaciones


@app.get("/api/estaciones/{estacion_id}", response_model=EstacionConID, summary="Obtener una estación de carga por ID")
async def read_estacion(estacion_id: int, db: Session = Depends(get_db)):
    db_estacion = crud.get_estacion(db, estacion_id=estacion_id)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación de carga no encontrada")
    return db_estacion


@app.get("/api/estaciones/search/", response_model=List[EstacionConID], summary="Buscar estaciones por nombre")
async def search_estacion_by_nombre(nombre: str, db: Session = Depends(get_db)):
    estaciones = crud.get_estacion_by_nombre(db, nombre=nombre)
    if not estaciones:
        raise HTTPException(status_code=404, detail="No se encontraron estaciones con ese nombre")
    return estaciones


@app.post("/api/estaciones/", response_model=EstacionConID, status_code=201,
          summary="Crear una nueva estación de carga")
async def create_new_estacion(estacion: EstacionBase, db: Session = Depends(get_db)):
    return crud.create_estacion(db=db, estacion=estacion)


@app.put("/api/estaciones/{estacion_id}", response_model=EstacionConID,
         summary="Actualizar una estación de carga existente")
async def update_existing_estacion(estacion_id: int, estacion: EstacionActualizada, db: Session = Depends(get_db)):
    db_estacion = crud.update_estacion(db=db, estacion_id=estacion_id, estacion=estacion)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación de carga no encontrada")
    return db_estacion


@app.patch("/api/estaciones/{estacion_id}", response_model=EstacionConID,
           summary="Actualizar parcialmente una estación de carga")
async def patch_existing_estacion(estacion_id: int, estacion: Dict[str, Any], db: Session = Depends(get_db)):
    db_estacion = crud.get_estacion(db, estacion_id)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación de carga no encontrada")

    for key, value in estacion.items():
        if hasattr(db_estacion, key):
            setattr(db_estacion, key, value)
    db.commit()
    db.refresh(db_estacion)
    return db_estacion


@app.delete("/api/estaciones/{estacion_id}", summary="Eliminar una estación de carga (la mueve al historial)")
async def delete_existing_estacion(estacion_id: int, db: Session = Depends(get_db)):
    db_estacion = crud.delete_estacion(db=db, estacion_id=estacion_id)
    if db_estacion is None:
        raise HTTPException(status_code=404, detail="Estación de carga no encontrada")
    return db_estacion


# --------------------- MANEJO DE IMÁGENES (Subida) ---------------------

UPLOAD_DIRECTORY = Path("static/images")  # Define un directorio para guardar imágenes
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


@app.post("/upload_image/", summary="Sube una imagen y devuelve su URL")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_extension = Path(file.filename).suffix
        if file_extension.lower() not in [".png", ".jpg", ".jpeg", ".gif"]:
            raise HTTPException(status_code=400,
                                detail="Formato de archivo no soportado. Se permiten .png, .jpg, .jpeg, .gif")

        # Genera un nombre de archivo único
        unique_filename = f"{os.urandom(16).hex()}{file_extension}"
        file_path = UPLOAD_DIRECTORY / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Devuelve la URL relativa de la imagen para ser guardada en la DB
        return {"url": f"/static/images/{unique_filename}"}
    except Exception as e:
        logger.error(f"Error al subir imagen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al subir la imagen: {e}")


# Servir archivos estáticos (imágenes, CSS, JS)
app.mount("/static", (Path(__file__).parent / "static").resolve(), name="static")


# --------------------- ENDPOINTS DE ESTADÍSTICAS ---------------------

@app.get("/api/statistics/cars_by_brand", summary="Obtener el número de autos por marca")
async def get_cars_by_brand_stats(db: Session = Depends(get_db)):
    stats = db.query(
        models_sql.AutoElectricoSQL.marca,
        func.count(models_sql.AutoElectricoSQL.id)
    ).group_by(models_sql.AutoElectricoSQL.marca).all()

    return [{"marca": brand, "count": count} for brand, count in stats]


@app.get("/api/statistics/station_power_by_connector_type",
         summary="Obtener la potencia promedio de estaciones por tipo de conector")
async def get_station_power_by_connector_type_stats(db: Session = Depends(get_db)):
    stats = db.query(
        models_sql.EstacionSQL.tipo_conector,
        func.avg(models_sql.EstacionSQL.potencia_kw)
    ).group_by(models_sql.EstacionSQL.tipo_conector).all()

    return [{"tipo_conector": connector_type, "avg_potencia_kw": round(avg_power, 2)} for connector_type, avg_power in
            stats]


@app.get("/api/statistics/charge_difficulty_distribution", summary="Obtener la distribución de dificultad de carga")
async def get_charge_difficulty_distribution_stats(db: Session = Depends(get_db)):
    stats = db.query(
        models_sql.CargaSQL.dificultad_carga,
        func.count(models_sql.CargaSQL.id)
    ).group_by(models_sql.CargaSQL.dificultad_carga).all()

    return [{"dificultad": difficulty, "count": count} for difficulty, count in stats]