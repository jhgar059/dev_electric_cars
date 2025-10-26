import multiprocessing

# REDUCCIÓN CRÍTICA: 1 worker es el máximo seguro para 512MB.
workers = 1

# La clase de worker para FastAPI con Uvicorn
worker_class = "uvicorn.workers.UvicornWorker"
# Enlazar al puerto de Render
bind = "0.0.0.0:$PORT"
# Aumentar el timeout
timeout = 120
loglevel = "info"
accesslog = "-"
errorlog = "-"