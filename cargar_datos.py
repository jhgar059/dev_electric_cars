import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from modelos import Base, ElectricCar

# Crea las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Lee el archivo CSV
df = pd.read_csv('datos/tu_archivo.csv')  # Reemplaza con el nombre correcto

# Inserta los datos en la base de datos
def cargar_datos():
    session = SessionLocal()
    for _, row in df.iterrows():
        carro = ElectricCar(
            marca=row['marca'],
            modelo=row['modelo'],
            año=row['año'],
            capacidad_bateria_kwh=row['capacidad_bateria_kwh'],
            autonomia_km=row['autonomia_km'],
            disponible=row['disponible']
        )
        session.add(carro)
    session.commit()
    session.close()

if __name__ == "__main__":
    cargar_datos()
