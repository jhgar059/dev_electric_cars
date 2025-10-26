import multiprocessing

# Número de workers. Redúcelo para ahorrar memoria.
# 1 o 2 workers son ideales para el nivel gratuito de 512MB.
# Prueba con 2, si falla, reduce a 1.
workers = 2

# La clase de worker para FastAPI con Uvicorn
worker_class = "uvicorn.workers.UvicornWorker"
# Enlazar a todas las interfaces disponibles en el puerto definido por la variable de entorno PORT
bind = "0.0.0.0:$PORT"
# Aumentar el timeout (ya lo tienes en 120s, lo cual está bien)
timeout = 120
# Log nivel para Gunicorn. INFO es un buen punto de partida.
loglevel = "info"
# Archivo de log de acceso (opcional, útil para depuración)
accesslog = "-" # Salida estándar
# Archivo de log de errores (opcional)
errorlog = "-" # Salida estándar