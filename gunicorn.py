# create a gunicorn config file
import multiprocessing
bind = "0.0.0.0:5000"
workers = (multiprocessing.cpu_count() * 2) + 1
threads = workers
worker_connections = 1000
timeout = 0