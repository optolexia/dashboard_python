# gunicorn.conf.py

bind = "0.0.0.0:8000"

workers = 2
threads = 4

timeout = 120
keepalive = 5

preload_app = True

loglevel = "info"

accesslog = "-"
errorlog = "-"
