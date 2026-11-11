import os

# Project root (parent of scripts/)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "searchy.db")
PORT = 8080
HOST = "127.0.0.1"
