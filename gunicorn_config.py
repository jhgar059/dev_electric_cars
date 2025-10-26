import os

# 🚨 CORRECCIÓN CRÍTICA: 1 worker es el MÁXIMO seguro para 512MB de RAM
workers = 1

# Clase de worker recomendada para FastAPI con Uvicorn
worker_class = "uvicorn.workers.UvicornWorker"

# Enlazar al puerto definido por Render ($PORT)
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Timeout: 120 segundos es suficiente
timeout = 120

# Log nivel
loglevel = "info"

# Salida de logs al stream estándar
accesslog = "-"
errorlog = "-"

print("INFO: Gunicorn configurado para 1 worker, en modo Uvicorn. OOM Prevenido.")