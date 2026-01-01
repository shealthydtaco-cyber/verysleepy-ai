# tools.py

import os
import subprocess
from config import ALLOWED_PATHS, ALLOWED_APPS

def open_file(path):
    for allowed in ALLOWED_PATHS:
        if path.startswith(allowed):
            os.startfile(path)
            return f"Opened file: {path}"
    return "Access denied."

def open_app(app):
    if app in ALLOWED_APPS:
        subprocess.Popen(app)
        return f"Opened app: {app}"
    return "App not allowed."
# tools.py (add this)

def load_adult_movies():
    try:
        with open("data_adult_movies.txt", "r", encoding="utf-8") as f:
            movies = [line.strip() for line in f if line.strip()]
        return movies
    except FileNotFoundError:
        return []
