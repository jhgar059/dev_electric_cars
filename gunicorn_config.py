import multiprocessing

# REDUCCIÓN CRÍTICA: 1 worker es el MÁXIMO seguro para 512MB de RAM.
# Esto garantiza que solo se inicie un proceso de Python para servir la app.
workers = 1

# Clase de worker recomendada para FastAPI con Uvicorn
worker_class = "uvicorn.workers.UvicornWorker"

# Enlazar a todas las interfaces disponibles en el puerto definido por Render
# Render establece la variable de entorno $PORT automáticamente
bind = "0.0.0.0:$PORT"

# Timeout: 120 segundos es suficiente
timeout = 120

# Log nivel
loglevel = "info"

# Salida de logs al stream estándar
accesslog = "-"
errorlog = "-"