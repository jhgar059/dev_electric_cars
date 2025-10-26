import multiprocessing

workers = 1


worker_class = "uvicorn.workers.UvicornWorker"


bind = "0.0.0.0:$PORT"


timeout = 120


loglevel = "info"

accesslog = "-"

errorlog = "-"