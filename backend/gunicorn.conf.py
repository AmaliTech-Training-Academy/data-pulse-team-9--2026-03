import multiprocessing
import os

# The socket to bind
bind = "0.0.0.0:8000"

# Number of worker processes (dynamically calculated based on CPU cores)
# Recommended formula is usually (cores * 2) + 1
cores = multiprocessing.cpu_count()
workers = int(os.environ.get("GUNICORN_WORKERS", (cores * 2) + 1))

# Worker class and threads (since Django is synchronous by default, threads > 1 helps concurrency)
worker_class = "gthread"
threads = int(os.environ.get("GUNICORN_THREADS", 4))

# Restart workers automatically after they hit a certain number of requests (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Maximum amount of time a worker can spend on an individual request before being killed
timeout = 120

# Access logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
