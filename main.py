from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import logging
import sys
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from modelos import ElectricCar

app = FastAPI()

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/cars")
def leer_autos(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    autos = db.query(ElectricCar).offset(skip).limit(limit).all()
    return autos

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

# Crear directorios necesarios si no existen
try:
    os.makedirs("datos", exist_ok=True)
    os.makedirs("eliminados", exist_ok=True)
    logger.info(f"Directorio de trabajo actual: {os.getcwd()}")
    logger.info(f"Directorio 'datos' existe: {os.path.exists('datos')}")
    logger.info(f"Directorio 'eliminados' existe: {os.path.exists('eliminados')}")
except Exception as e:
    logger.error(f"Error al crear directorios: {e}")

# Importaciones de modelos y operaciones de cada módulo
try:
    from modelos import AutoElectrico, AutoElectricoConID
    from modelos import CargaBase, CargaConID, CargaActualizada
    from modelos import EstacionBase, EstacionConID, EstacionActualizada
    logger.info("Modelos importados correctamente")
except ImportError as e:
    logger.error(f"Error al importar modelos: {e}")
    raise

try:
    from operaciones import (
        leer_autos, leer_auto_por_id, crear_auto, actualizar_auto, eliminar_auto,
        autos_eliminados, filtrar_por_marca
    )
    from operaciones import (
        leer_cargas, obtener_carga_por_id, crear_carga, actualizar_dato_carga,
        eliminar_dato_carga, leer_eliminados, filtrar_por_modelo as filtrar_carga_modelo,
        filtrar_por_dificultad
    )
    from operaciones import (
        leer_estaciones, obtener_estaciones_eliminadas, obtener_estacion_por_id,
        filtrar_estaciones_por_operador, filtrar_estaciones_por_tipo_conector,
        crear_estacion, modificar_estacion, borrar_estacion
    )
    logger.info("Operaciones importadas correctamente")
except ImportError as e:
    logger.error(f"Error al importar operaciones: {e}")
    raise

app = FastAPI(title="API Unificada de Autos Eléctricos")

# --------------------- RAÍZ GENERAL ---------------------

@app.get("/")
def inicio_general():
    return {"mensaje": "Bienvenido a la API Unificada de Autos Eléctricos"}

# --------------------- SECCIÓN AUTOS ---------------------

@app.get("/autos", response_model=List[AutoElectricoConID])
def obtener_autos():
    try:
        return leer_autos()
    except Exception as e:
        logger.error(f"Error al leer autos: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/auto/{auto_id}", response_model=AutoElectricoConID)
def obtener_auto(auto_id: int):
    try:
        auto = leer_auto_por_id(auto_id)
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
def crear_nuevo_auto(auto: AutoElectrico):
    try:
        return crear_auto(auto)
    except Exception as e:
        logger.error(f"Error al crear auto: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear: {str(e)}")

@app.put("/auto/{auto_id}", response_model=AutoElectricoConID)
def modificar_auto(auto_id: int, actualizacion: dict):
    try:
        auto_actualizado = actualizar_auto(auto_id, actualizacion)
        if not auto_actualizado:
            raise HTTPException(status_code=404, detail="No se pudo actualizar el auto")
        return auto_actualizado
    except Exception as e:
        logger.error(f"Error al actualizar auto {auto_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

@app.delete("/auto/{auto_id}", response_model=AutoElectrico)
def borrar_auto(auto_id: int):
    try:
        auto_eliminado = eliminar_auto(auto_id)
        if not auto_eliminado:
            raise HTTPException(status_code=404, detail="No se pudo eliminar el auto")
        return auto_eliminado
    except Exception as e:
        logger.error(f"Error al eliminar auto {auto_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

@app.get("/autos/eliminados", response_model=List[AutoElectricoConID])
def listar_autos_eliminados():
    try:
        return autos_eliminados()
    except Exception as e:
        logger.error(f"Error al listar autos eliminados: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/autos/filtrar/marca/{marca}", response_model=List[AutoElectricoConID])
def filtrar_autos_por_marca(marca: str):
    try:
        autos_filtrados = filtrar_por_marca(marca)
        if not autos_filtrados:
            raise HTTPException(status_code=404, detail="No se encontraron autos con esa marca")
        return autos_filtrados
    except Exception as e:
        logger.error(f"Error al filtrar por marca {marca}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# --------------------- SECCIÓN DIFICULTAD DE CARGA ---------------------

@app.get("/cargas", response_model=List[CargaConID])
def listar_cargas():
    try:
        return leer_cargas()
    except Exception as e:
        logger.error(f"Error al leer cargas: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/carga/{carga_id}", response_model=CargaConID)
def obtener_carga(carga_id: int):
    try:
        carga = obtener_carga_por_id(carga_id)
        if not carga:
            raise HTTPException(status_code=404, detail="Carga no encontrada")
        return carga
    except Exception as e:
        logger.error(f"Error al obtener carga {carga_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/carga", response_model=CargaConID)
def crear_nueva_carga(carga: CargaBase):
    try:
        return crear_carga(carga)
    except Exception as e:
        logger.error(f"Error al crear carga: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear: {str(e)}")

@app.put("/carga/{carga_id}", response_model=CargaConID)
def actualizar_carga(carga_id: int, datos: CargaActualizada):
    try:
        actualizada = actualizar_dato_carga(carga_id, datos.model_dump(exclude_unset=True))
        if not actualizada:
            raise HTTPException(status_code=404, detail="No se pudo actualizar")
        return actualizada
    except Exception as e:
        logger.error(f"Error al actualizar carga {carga_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

@app.delete("/carga/{carga_id}", response_model=CargaConID)
def eliminar_carga(carga_id: int):
    try:
        eliminada = eliminar_dato_carga(carga_id)
        if not eliminada:
            raise HTTPException(status_code=404, detail="No se pudo eliminar")
        return eliminada
    except Exception as e:
        logger.error(f"Error al eliminar carga {carga_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

@app.get("/cargas/eliminadas", response_model=List[CargaConID])
def listar_cargas_eliminadas():
    try:
        return leer_eliminados()
    except Exception as e:
        logger.error(f"Error al listar cargas eliminadas: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/cargas/filtrar/modelo/{modelo}", response_model=List[CargaConID])
def filtrar_cargas_modelo(modelo: str):
    try:
        resultado = filtrar_carga_modelo(modelo)
        if not resultado:
            raise HTTPException(status_code=404, detail="No se encontraron coincidencias")
        return resultado
    except Exception as e:
        logger.error(f"Error al filtrar cargas por modelo {modelo}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/cargas/filtrar/dificultad/{nivel}", response_model=List[CargaConID])
def filtrar_cargas_dificultad(nivel: str):
    try:
        resultado = filtrar_por_dificultad(nivel)
        if not resultado:
            raise HTTPException(status_code=404, detail="No se encontraron coincidencias")
        return resultado
    except Exception as e:
        logger.error(f"Error al filtrar cargas por dificultad {nivel}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# --------------------- SECCIÓN ESTACIONES DE CARGA ---------------------

@app.get("/estaciones", response_model=List[EstacionConID])
def listar_estaciones():
    try:
        return leer_estaciones()
    except Exception as e:
        logger.error(f"Error al leer estaciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/estaciones/eliminadas", response_model=List[EstacionConID])
def estaciones_eliminadas():
    try:
        return obtener_estaciones_eliminadas()
    except Exception as e:
        logger.error(f"Error al obtener estaciones eliminadas: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/estacion/{estacion_id}", response_model=EstacionConID)
def obtener_estacion(estacion_id: int):
    try:
        estacion = obtener_estacion_por_id(estacion_id)
        if not estacion:
            raise HTTPException(status_code=404, detail="Estación no encontrada")
        return estacion
    except Exception as e:
        logger.error(f"Error al obtener estación {estacion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/estaciones/filtrar/operador/{operador}", response_model=List[EstacionConID])
def filtrar_por_operador(operador: str):
    try:
        resultados = filtrar_estaciones_por_operador(operador)
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron estaciones con ese operador")
        return resultados
    except Exception as e:
        logger.error(f"Error al filtrar por operador {operador}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/estaciones/filtrar/conector/{tipo_conector}", response_model=List[EstacionConID])
def filtrar_por_conector(tipo_conector: str):
    try:
        resultados = filtrar_estaciones_por_tipo_conector(tipo_conector)
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron estaciones con ese tipo de conector")
        return resultados
    except Exception as e:
        logger.error(f"Error al filtrar por conector {tipo_conector}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/estacion", response_model=EstacionConID)
def agregar_estacion(estacion: EstacionBase):
    try:
        return crear_estacion(estacion)
    except Exception as e:
        logger.error(f"Error al crear estación: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear: {str(e)}")

@app.put("/estacion/{estacion_id}", response_model=EstacionConID)
def actualizar_estacion(estacion_id: int, cambios: EstacionActualizada):
    try:
        actualizada = modificar_estacion(estacion_id, cambios.model_dump(exclude_unset=True))
        if not actualizada:
            raise HTTPException(status_code=404, detail="No se pudo actualizar la estación")
        return actualizada
    except Exception as e:
        logger.error(f"Error al actualizar estación {estacion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

@app.delete("/estacion/{estacion_id}", response_model=EstacionConID)
def eliminar_estacion(estacion_id: int):
    try:
        eliminada = borrar_estacion(estacion_id)
        if not eliminada:
            raise HTTPException(status_code=404, detail="No se encontró la estación a eliminar")
        return eliminada
    except Exception as e:
        logger.error(f"Error al eliminar estación {estacion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

# --------------------- EJECUCIÓN DEL SERVIDOR ---------------------

if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando servidor FastAPI...")
    uvicorn.run(app, host="127.0.0.1", port=5050)