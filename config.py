import os
import random
from dotenv import load_dotenv

# Cargar variables de entorno si existe un archivo .env
load_dotenv()

# Rutas de Archivos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CSV_NAME = "Yorvis - Lou - Domain process June 2026(Sheet1).csv"
local_csv = os.path.join(BASE_DIR, CSV_NAME)
if os.path.exists(local_csv):
    CSV_PATH = local_csv
else:
    CSV_PATH = r"C:\Users\Yorvis\Desktop\HACK\IMAGNES RAUL\AGENTE DOMINIO\Yorvis - Lou - Domain process June 2026(Sheet1).csv"
DB_PATH = os.path.join(BASE_DIR, "domain_leads.db")

# API Keys y Modelos
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Seguridad y Autenticación del Administrador
SECRET_KEY = os.environ.get("SECRET_KEY", "vibra-deals-secret-12345")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# Lista de User-Agents realistas para evitar bloqueos
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edge/119.0.0.0"
]

def get_random_headers():
    """Genera cabeceras HTTP realistas para simular navegación humana."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0"
    }

# Retrasos de cortesía (en segundos)
MIN_DELAY = 2.0
MAX_DELAY = 5.0
