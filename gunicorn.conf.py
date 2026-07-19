# Gunicorn configuration file for production streaming support
import multiprocessing

# Bind to the port provided by Render environment
bind = "0.0.0.0:" + "8000"  # Render overrides this using the $PORT environment variable automatically

# Use threaded workers to handle infinite video streaming and status API calls concurrently
worker_class = 'gthread'
workers = 1
threads = 8

# Disable timeout (0) to prevent Gunicorn from killing workers handling the infinite video feed
timeout = 0
