import sqlite3
import logging
from config import DB_PATH

logger = logging.getLogger("DomainAgent")

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos creando las tablas necesarias si no existen."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla de dominios a vender (cargados del CSV)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dominios (
            dominio TEXT PRIMARY KEY,
            categoria TEXT,
            ano_registro INTEGER,
            score INTEGER,
            idioma TEXT,
            pais_region TEXT,
            estado TEXT DEFAULT 'PENDIENTE',
            ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Migraciones para bases de datos existentes que no tienen idioma ni pais_region
    try:
        cursor.execute("ALTER TABLE dominios ADD COLUMN idioma TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE dominios ADD COLUMN pais_region TEXT")
    except sqlite3.OperationalError:
        pass
    
    # Tabla de prospectos (clientes/candidatos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dominio_venta TEXT NOT NULL,
            empresa_nombre TEXT,
            sitio_web_actual TEXT,
            correo TEXT,
            telefono TEXT,
            propuesta_texto TEXT,
            estado TEXT DEFAULT 'PENDIENTE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dominio_venta) REFERENCES dominios (dominio) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Base de datos SQLite inicializada correctamente con relación de dominios y leads.")

def add_domain_metadata(dominio, categoria, ano_registro, score, estado="PENDIENTE", idioma=None, pais_region=None):
    """Inserta o actualiza metadatos de un dominio."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO dominios (dominio, categoria, ano_registro, score, estado, idioma, pais_region, ultima_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(dominio) DO UPDATE SET 
                categoria = COALESCE(excluded.categoria, dominios.categoria),
                ano_registro = COALESCE(excluded.ano_registro, dominios.ano_registro),
                score = COALESCE(excluded.score, dominios.score),
                estado = COALESCE(excluded.estado, dominios.estado),
                idioma = COALESCE(excluded.idioma, dominios.idioma),
                pais_region = COALESCE(excluded.pais_region, dominios.pais_region),
                ultima_actualizacion = CURRENT_TIMESTAMP
        ''', (dominio, categoria, ano_registro, score, estado, idioma, pais_region))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error al guardar metadatos de dominio {dominio}: {e}")
        return False
    finally:
        conn.close()

def add_client(dominio_venta, empresa_nombre, sitio_web_actual, correo, telefono, propuesta_texto):
    """Inserta un nuevo prospecto en la base de datos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO clientes (dominio_venta, empresa_nombre, sitio_web_actual, correo, telefono, propuesta_texto)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (dominio_venta, empresa_nombre, sitio_web_actual, correo, telefono, propuesta_texto))
        conn.commit()
        logger.info(f"Prospecto guardado: {empresa_nombre} ({sitio_web_actual}) para dominio {dominio_venta}")
        return True
    except Exception as e:
        logger.error(f"Error al guardar prospecto {empresa_nombre}: {e}")
        return False
    finally:
        conn.close()

def client_exists(dominio_venta, sitio_web_actual):
    """Verifica si un sitio web ya fue prospectado para un dominio específico."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM clientes 
        WHERE dominio_venta = ? AND sitio_web_actual = ?
    ''', (dominio_venta, sitio_web_actual))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def mark_domain_processed(dominio, estado="COMPLETADO"):
    """Registra que un dominio ha sido completamente analizado."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE dominios 
            SET estado = ?, ultima_actualizacion = CURRENT_TIMESTAMP
            WHERE dominio = ?
        ''', (estado, dominio))
        conn.commit()
        logger.info(f"Dominio {dominio} marcado como {estado}")
        return True
    except Exception as e:
        logger.error(f"Error al marcar dominio {dominio} como procesado: {e}")
        return False
    finally:
        conn.close()

def is_domain_processed(dominio):
    """Verifica si un dominio ya ha sido procesado con éxito."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT estado FROM dominios 
        WHERE dominio = ? AND estado = 'COMPLETADO'
    ''', (dominio,))
    row = cursor.fetchone()
    conn.close()
    return row is not None
