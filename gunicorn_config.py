import multiprocessing
import os

# REDUCCIÓN CRÍTICA: 1 worker es el MÁXIMO seguro para 512MB de RAM
workers = 1

# Clase de worker recomendada para FastAPI con Uvicorn
worker_class = "uvicorn.workers.UvicornWorker"

# Enlazar al puerto definido por Render ($PORT)
bind = "0.0.0.0:$PORT"

# Timeout: 120 segundos es suficiente
timeout = 120

# Log nivel
loglevel = "info"

# Salida de logs al stream estándar
accesslog = "-"
errorlog = "-"

# Si necesitas usar un archivo de configuración, Render solo lo ve si la ruta es correcta.
# Revisa que tu comando de inicio apunte a este archivo.
print("INFO: Gunicorn configurado para 1 worker, en modo Uvicorn.")