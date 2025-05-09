# =======================
# BLOQUE 1: autos_electricos
# =======================

import csv
from typing import List, Optional
from modelos import AutoElectrico, AutoElectricoConID
from modelos import CargaBase, CargaConID
from modelos import EstacionBase, EstacionConID

# ----- Configuración de autos -----
ARCHIVO_AUTOS = "datos/autos_electricos.csv"
ARCHIVO_AUTOS_ELIMINADOS = "eliminados/autos_eliminados.csv"
CAMPOS_AUTOS = ["id", "marca", "modelo", "anio", "capacidad_bateria_kwh", "autonomia_km", "disponible"]

def leer_autos() -> List[AutoElectricoConID]:
    try:
        with open(ARCHIVO_AUTOS, newline="") as archivo:
            lector = csv.DictReader(archivo)
            return [AutoElectricoConID(**convertir_tipos_auto(fila)) for fila in lector]
    except FileNotFoundError:
        return []

def leer_auto_por_id(auto_id: int) -> Optional[AutoElectricoConID]:
    return next((auto for auto in leer_autos() if auto.id == auto_id), None)

def obtener_siguiente_id_auto() -> int:
    autos = leer_autos()
    return max([auto.id for auto in autos], default=0) + 1

def crear_auto(auto: AutoElectrico) -> AutoElectricoConID:
    nuevo_auto = AutoElectricoConID(id=obtener_siguiente_id_auto(), **auto.model_dump())
    with open(ARCHIVO_AUTOS, "a", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS_AUTOS)
        if archivo.tell() == 0:
            escritor.writeheader()
        escritor.writerow(nuevo_auto.model_dump())
    return nuevo_auto

def actualizar_auto(auto_id: int, cambios: dict) -> Optional[AutoElectricoConID]:
    autos = leer_autos()
    actualizado = None
    for i, auto in enumerate(autos):
        if auto.id == auto_id:
            for campo, valor in cambios.items():
                if hasattr(autos[i], campo):
                    setattr(autos[i], campo, valor)
            actualizado = autos[i]
            break
    if actualizado:
        with open(ARCHIVO_AUTOS, "w", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=CAMPOS_AUTOS)
            escritor.writeheader()
            for auto in autos:
                escritor.writerow(auto.model_dump())
        return actualizado
    return None

def eliminar_auto(auto_id: int) -> Optional[AutoElectrico]:
    autos = leer_autos()
    eliminado = None
    with open(ARCHIVO_AUTOS, "w", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS_AUTOS)
        escritor.writeheader()
        for auto in autos:
            if auto.id == auto_id:
                eliminado = auto
                guardar_auto_eliminado(auto)
                continue
            escritor.writerow(auto.model_dump())
    if eliminado:
        datos = eliminado.model_dump()
        del datos["id"]
        return AutoElectrico(**datos)
    return None

def guardar_auto_eliminado(auto: AutoElectricoConID):
    with open(ARCHIVO_AUTOS_ELIMINADOS, "a", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS_AUTOS)
        if archivo.tell() == 0:
            escritor.writeheader()
        escritor.writerow(auto.model_dump())

def autos_eliminados() -> List[AutoElectricoConID]:
    try:
        with open(ARCHIVO_AUTOS_ELIMINADOS, newline="") as archivo:
            lector = csv.DictReader(archivo)
            return [AutoElectricoConID(**convertir_tipos_auto(fila)) for fila in lector]
    except FileNotFoundError:
        return []

def filtrar_por_marca(marca: str) -> List[AutoElectricoConID]:
    return [auto for auto in leer_autos() if auto.marca.lower() == marca.lower()]

def convertir_tipos_auto(fila: dict) -> dict:
    return {
        "id": int(fila["id"]),
        "marca": fila["marca"],
        "modelo": fila["modelo"],
        "anio": int(fila["anio"]),
        "capacidad_bateria_kwh": float(fila["capacidad_bateria_kwh"]),
        "autonomia_km": float(fila["autonomia_km"]),
        "disponible": fila["disponible"].lower() == "true"
    }

# =======================
# BLOQUE 2: dificultad_carga
# =======================

ARCHIVO_CARGA = "datos/dificultad_carga.csv"
ARCHIVO_CARGA_ELIMINADOS = "eliminados/dificultad_carga_eliminados.csv"
CAMPOS_CARGA = [
    "id", "modelo", "tipo_autonomia", "autonomia_km",
    "consumo_kwh_100km", "tiempo_carga_horas",
    "dificultad_carga", "requiere_instalacion_domestica"
]

def leer_csv(path):
    try:
        with open(path, mode="r", newline="") as archivo:
            lector = csv.DictReader(archivo)
            return [CargaConID(
                id=int(f["id"]),
                modelo=f["modelo"],
                tipo_autonomia=f["tipo_autonomia"],
                autonomia_km=float(f["autonomia_km"]),
                consumo_kwh_100km=float(f["consumo_kwh_100km"]),
                tiempo_carga_horas=float(f["tiempo_carga_horas"]),
                dificultad_carga=f["dificultad_carga"],
                requiere_instalacion_domestica=f["requiere_instalacion_domestica"].lower() == "true"
            ) for f in lector]
    except FileNotFoundError:
        return []

def leer_cargas():
    return leer_csv(ARCHIVO_CARGA)

def leer_eliminados():
    return leer_csv(ARCHIVO_CARGA_ELIMINADOS)

def siguiente_id():
    cargas = leer_cargas()
    return max([c.id for c in cargas], default=0) + 1

def guardar_csv(path, cargas):
    with open(path, mode="w", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=CAMPOS_CARGA)
        writer.writeheader()
        for c in cargas:
            writer.writerow(c.model_dump())

def guardar_carga(carga: CargaConID):
    with open(ARCHIVO_CARGA, mode="a", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=CAMPOS_CARGA)
        if archivo.tell() == 0:
            writer.writeheader()
        writer.writerow(carga.model_dump())

def crear_carga(carga: CargaBase) -> CargaConID:
    nueva = CargaConID(id=siguiente_id(), **carga.model_dump())
    guardar_carga(nueva)
    return nueva

def obtener_carga_por_id(carga_id: int) -> Optional[CargaConID]:
    return next((c for c in leer_cargas() if c.id == carga_id), None)

def actualizar_dato_carga(carga_id: int, cambios: dict) -> Optional[CargaConID]:
    cargas = leer_cargas()
    actualizada = None
    for i, c in enumerate(cargas):
        if c.id == carga_id:
            for campo, valor in cambios.items():
                setattr(cargas[i], campo, valor)
            actualizada = cargas[i]
            break
    if actualizada:
        guardar_csv(ARCHIVO_CARGA, cargas)
        return actualizada
    return None

def eliminar_dato_carga(carga_id: int) -> Optional[CargaConID]:
    cargas = leer_cargas()
    eliminada = None
    nuevas = []
    for c in cargas:
        if c.id == carga_id:
            eliminada = c
        else:
            nuevas.append(c)
    if eliminada:
        guardar_csv(ARCHIVO_CARGA, nuevas)
        with open(ARCHIVO_CARGA_ELIMINADOS, mode="a", newline="") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=CAMPOS_CARGA)
            if archivo.tell() == 0:
                writer.writeheader()
            writer.writerow(eliminada.model_dump())
        return eliminada
    return None

def filtrar_por_dificultad(nivel: str):
    return [c for c in leer_cargas() if c.dificultad_carga.lower() == nivel.lower()]

def filtrar_por_modelo(modelo: str):
    return [c for c in leer_cargas() if modelo.lower() in c.modelo.lower()]

# =======================
# BLOQUE 3: estaciones_carga
# =======================

ARCHIVO_ESTACIONES = "datos/estaciones_carga.csv"
ARCHIVO_ESTACIONES_ELIMINADAS = "eliminados/estaciones_eliminadas.csv"
CAMPOS_ESTACIONES = ["id", "nombre", "ubicacion", "tipo_conector", "potencia_kw", "num_conectores",
                     "acceso_publico", "horario_apertura", "coste_por_kwh", "operador"]

def leer_estaciones():
    try:
        with open(ARCHIVO_ESTACIONES, mode="r", newline="") as archivo:
            lector = csv.DictReader(archivo)
            return [EstacionConID(
                id=int(f["id"]),
                nombre=f["nombre"],
                ubicacion=f["ubicacion"],
                tipo_conector=f["tipo_conector"],
                potencia_kw=float(f["potencia_kw"]),
                num_conectores=int(f["num_conectores"]),
                acceso_publico=f["acceso_publico"].lower() == "true",
                horario_apertura=f["horario_apertura"],
                coste_por_kwh=float(f["coste_por_kwh"]),
                operador=f["operador"]
            ) for f in lector]
    except FileNotFoundError:
        return []

def obtener_siguiente_id_estacion():
    estaciones = leer_estaciones()
    return max([e.id for e in estaciones], default=0) + 1

def guardar_estacion(estacion: EstacionConID):
    with open(ARCHIVO_ESTACIONES, mode="a", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=CAMPOS_ESTACIONES)
        if archivo.tell() == 0:
            writer.writeheader()
        writer.writerow(estacion.model_dump())

def crear_estacion(estacion: EstacionBase) -> EstacionConID:
    nueva = EstacionConID(id=obtener_siguiente_id_estacion(), **estacion.model_dump())
    guardar_estacion(nueva)
    return nueva

def obtener_estacion_por_id(estacion_id: int) -> Optional[EstacionConID]:
    estaciones = leer_estaciones()
    return next((e for e in estaciones if e.id == estacion_id), None)

def modificar_estacion(estacion_id: int, cambios: dict) -> Optional[EstacionConID]:
    estaciones = leer_estaciones()
    actualizada = None
    for i, e in enumerate(estaciones):
        if e.id == estacion_id:
            for campo, valor in cambios.items():
                setattr(estaciones[i], campo, valor)
            actualizada = estaciones[i]
            break
    if actualizada:
        with open(ARCHIVO_ESTACIONES, mode="w", newline="") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=CAMPOS_ESTACIONES)
            writer.writeheader()
            for e in estaciones:
                writer.writerow(e.model_dump())
        return actualizada
    return None

def borrar_estacion(estacion_id: int) -> Optional[EstacionConID]:
    estaciones = leer_estaciones()
    eliminada = None
    with open(ARCHIVO_ESTACIONES, mode="w", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=CAMPOS_ESTACIONES)
        writer.writeheader()
        for e in estaciones:
            if e.id == estacion_id:
                eliminada = e
                guardar_en_eliminadas_estacion(e)
                continue
            writer.writerow(e.model_dump())
    return eliminada

def guardar_en_eliminadas_estacion(estacion: EstacionConID):
    with open(ARCHIVO_ESTACIONES_ELIMINADAS, mode="a", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=CAMPOS_ESTACIONES)
        if archivo.tell() == 0:
            writer.writeheader()
        writer.writerow(estacion.model_dump())

def obtener_estaciones_eliminadas():
    try:
        with open(ARCHIVO_ESTACIONES_ELIMINADAS, mode="r", newline="") as archivo:
            lector = csv.DictReader(archivo)
            return [EstacionConID(
                id=int(f["id"]),
                nombre=f["nombre"],
                ubicacion=f["ubicacion"],
                tipo_conector=f["tipo_conector"],
                potencia_kw=float(f["potencia_kw"]),
                num_conectores=int(f["num_conectores"]),
                acceso_publico=f["acceso_publico"].lower() == "true",
                horario_apertura=f["horario_apertura"],
                coste_por_kwh=float(f["coste_por_kwh"]),
                operador=f["operador"]
            ) for f in lector]
    except FileNotFoundError:
        return []

def filtrar_estaciones_por_operador(operador: str):
    estaciones = leer_estaciones()
    return [e for e in estaciones if operador.lower() in e.operador.lower()]

def filtrar_estaciones_por_tipo_conector(tipo_conector: str):
    estaciones = leer_estaciones()
    return [e for e in estaciones if e.tipo_conector.lower() == tipo_conector.lower()]