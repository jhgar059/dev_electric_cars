import multiprocessing

# Número de workers. Una buena regla general es (número de CPUs * 2) + 1
workers = multiprocessing.cpu_count() * 2 + 1
# La clase de worker para FastAPI con Uvicorn
worker_class = "uvicorn.workers.UvicornWorker"
# Enlazar a todas las interfaces disponibles en el puerto definido por la variable de entorno PORT
# Render establece la variable de entorno PORT para tu aplicación
bind = "0.0.0.0:$PORT"
# Tiempo máximo que un worker puede tardar en procesar una solicitud (en segundos)
# Aumentar si tienes operaciones de larga duración para evitar timeouts
timeout = 120
# Log nivel para Gunicorn. INFO es un buen punto de partida.
loglevel = "info"
# Archivo de log de acceso (opcional, útil para depuración)
accesslog = "-" # Salida estándar
# Archivo de log de errores (opcional)
errorlog = "-" # Salida estándar