from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List
import os
import logging
import sys
from sqlalchemy.orm import Session

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

# Importaciones de modelos
from modelos import AutoElectrico, AutoElectricoConID
from modelos import CargaBase, CargaConID, CargaActualizada
from modelos import EstacionBase, EstacionConID, EstacionActualizada

# Importar la configuración de base de datos y modelos SQL
from database import get_db, engine, Base
import models_sql
import crud

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Unificada de Autos Eléctricos")

# --------------------- RAÍZ GENERAL ---------------------

@app.get("/")
def inicio_general():
    return {"mensaje": "Bienvenido a la API Unificada de Autos Eléctricos"}

# --------------------- SECCIÓN AUTOS ---------------------

@app.get("/autos", response_model=List[AutoElectricoConID])
def obtener_autos(db: Session = Depends(get_db)):
    try:
        return crud.get_autos(db)
    except Exception as e:
        logger.error(f"Error al leer autos: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/auto/{auto_id}", response_model=AutoElectricoConID)
def obtener_auto(auto_id: int, db: Session = Depends(get_db)):
    try:
        auto = crud.get_auto(db, auto_id)
        if not auto:
            raise HTTPException(status_code=404, detail="Auto no encontrado")
        return auto
    except ValueError as e:
        logger.error(f"Error de valor al obtener auto {auto_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Error de formato: {str(e)}")
    except Exception as e:
        logger.error(f"Error al obtener auto {auto_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/auto", response_model=AutoElectricoConID)
def crear_nuevo_auto(auto: AutoElectrico, db: Session = Depends(get_db)):
    try:
        return crud.create_auto(db, auto)
    except Exception as e:
        logger.error(f"Error al crear auto: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear: {str(e)}")

@app.put("/auto/{auto_id}", response_model=AutoElectricoConID)
def modificar_auto(auto_id: int, actualizacion: dict, db: Session = Depends(get_db)):
    try:
        auto_actualizado = crud.update_auto(db, auto_id, actualizacion)
        if not auto_actualizado:
            raise HTTPException(status_code=404, detail="No se pudo actualizar el auto")
        return auto_actualizado
    except Exception as e:
        logger.error(f"Error al actualizar auto {auto_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

@app.delete("/auto/{auto_id}", response_model=AutoElectricoConID)
def borrar_auto(auto_id: int, db: Session = Depends(get_db)):
    try:
        auto_eliminado = crud.delete_auto(db, auto_id)
        if not auto_eliminado:
            raise HTTPException(status_code=404, detail="No se pudo eliminar el auto")
        return auto_eliminado
    except Exception as e:
        logger.error(f"Error al eliminar auto {auto_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

@app.get("/autos/filtrar/marca/{marca}", response_model=List[AutoElectricoConID])
def filtrar_autos_por_marca(marca: str, db: Session = Depends(get_db)):
    try:
        autos_filtrados = crud.filter_autos_by_marca(db, marca)
        if not autos_filtrados:
            raise HTTPException(status_code=404, detail="No se encontraron autos con esa marca")
        return autos_filtrados
    except Exception as e:
        logger.error(f"Error al filtrar por marca {marca}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# --------------------- SECCIÓN DIFICULTAD DE CARGA ---------------------

@app.get("/cargas", response_model=List[CargaConID])
def listar_cargas(db: Session = Depends(get_db)):
    try:
        return crud.get_cargas(db)
    except Exception as e:
        logger.error(f"Error al leer cargas: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/carga/{carga_id}", response_model=CargaConID)
def obtener_carga(carga_id: int, db: Session = Depends(get_db)):
    try:
        carga = crud.get_carga(db, carga_id)
        if not carga:
            raise HTTPException(status_code=404, detail="Carga no encontrada")
        return carga
    except Exception as e:
        logger.error(f"Error al obtener carga {carga_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/carga", response_model=CargaConID)
def crear_nueva_carga(carga: CargaBase, db: Session = Depends(get_db)):
    try:
        return crud.create_carga(db, carga)
    except Exception as e:
        logger.error(f"Error al crear carga: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear: {str(e)}")

@app.put("/carga/{carga_id}", response_model=CargaConID)
def actualizar_carga(carga_id: int, datos: CargaActualizada, db: Session = Depends(get_db)):
    try:
        actualizada = crud.update_carga(db, carga_id, datos.model_dump(exclude_unset=True))
        if not actualizada:
            raise HTTPException(status_code=404, detail="No se pudo actualizar")
        return actualizada
    except Exception as e:
        logger.error(f"Error al actualizar carga {carga_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

@app.delete("/carga/{carga_id}", response_model=CargaConID)
def eliminar_carga(carga_id: int, db: Session = Depends(get_db)):
    try:
        eliminada = crud.delete_carga(db, carga_id)
        if not eliminada:
            raise HTTPException(status_code=404, detail="No se pudo eliminar")
        return eliminada
    except Exception as e:
        logger.error(f"Error al eliminar carga {carga_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

@app.get("/cargas/filtrar/modelo/{modelo}", response_model=List[CargaConID])
def filtrar_cargas_modelo(modelo: str, db: Session = Depends(get_db)):
    try:
        resultado = crud.filter_cargas_by_modelo(db, modelo)
        if not resultado:
            raise HTTPException(status_code=404, detail="No se encontraron coincidencias")
        return resultado
    except Exception as e:
        logger.error(f"Error al filtrar cargas por modelo {modelo}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/cargas/filtrar/dificultad/{nivel}", response_model=List[CargaConID])
def filtrar_cargas_dificultad(nivel: str, db: Session = Depends(get_db)):
    try:
        resultado = crud.filter_cargas_by_dificultad(db, nivel)
        if not resultado:
            raise HTTPException(status_code=404, detail="No se encontraron coincidencias")
        return resultado
    except Exception as e:
        logger.error(f"Error al filtrar cargas por dificultad {nivel}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# --------------------- SECCIÓN ESTACIONES DE CARGA ---------------------

@app.get("/estaciones", response_model=List[EstacionConID])
def listar_estaciones(db: Session = Depends(get_db)):
    try:
        return crud.get_estaciones(db)
    except Exception as e:
        logger.error(f"Error al leer estaciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/estacion/{estacion_id}", response_model=EstacionConID)
def obtener_estacion(estacion_id: int, db: Session = Depends(get_db)):
    try:
        estacion = crud.get_estacion(db, estacion_id)
        if not estacion:
            raise HTTPException(status_code=404, detail="Estación no encontrada")
        return estacion
    except Exception as e:
        logger.error(f"Error al obtener estación {estacion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/estaciones/filtrar/operador/{operador}", response_model=List[EstacionConID])
def filtrar_por_operador(operador: str, db: Session = Depends(get_db)):
    try:
        resultados = crud.filter_estaciones_by_operador(db, operador)
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron estaciones con ese operador")
        return resultados
    except Exception as e:
        logger.error(f"Error al filtrar por operador {operador}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/estaciones/filtrar/conector/{tipo_conector}", response_model=List[EstacionConID])
def filtrar_por_conector(tipo_conector: str, db: Session = Depends(get_db)):
    try:
        resultados = crud.filter_estaciones_by_tipo_conector(db, tipo_conector)
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron estaciones con ese tipo de conector")
        return resultados
    except Exception as e:
        logger.error(f"Error al filtrar por conector {tipo_conector}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/estacion", response_model=EstacionConID)
def agregar_estacion(estacion: EstacionBase, db: Session = Depends(get_db)):
    try:
        return crud.create_estacion(db, estacion)
    except Exception as e:
        logger.error(f"Error al crear estación: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear: {str(e)}")

@app.put("/estacion/{estacion_id}", response_model=EstacionConID)
def actualizar_estacion(estacion_id: int, cambios: EstacionActualizada, db: Session = Depends(get_db)):
    try:
        actualizada = crud.update_estacion(db, estacion_id, cambios.model_dump(exclude_unset=True))
        if not actualizada:
            raise HTTPException(status_code=404, detail="No se pudo actualizar la estación")
        return actualizada
    except Exception as e:
        logger.error(f"Error al actualizar estación {estacion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

@app.delete("/estacion/{estacion_id}", response_model=EstacionConID)
def eliminar_estacion(estacion_id: int, db: Session = Depends(get_db)):
    try:
        eliminada = crud.delete_estacion(db, estacion_id)
        if not eliminada:
            raise HTTPException(status_code=404, detail="No se encontró la estación a eliminar")
        return eliminada
    except Exception as e:
        logger.error(f"Error al eliminar estación {estacion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Obtener el puerto desde las variables de entorno (necesario para Render)
    port = int(os.environ.get("PORT", 5050))
    logger.info(f"Iniciando servidor FastAPI en puerto {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)