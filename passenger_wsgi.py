import sys
import os

# Agregar el directorio de la aplicación al path del sistema
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Importar la app de Flask y exponerla como 'application' (requerido por Passenger en cPanel)
from app import app as application
