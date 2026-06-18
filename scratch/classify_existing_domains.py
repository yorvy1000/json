import sqlite3
import sys
import os

# Ajustar path para importar llm_helper desde el directorio padre
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import llm_helper

db_path = "domain_leads.db"
if not os.path.exists(db_path):
    print("Database not found in the current directory.")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT dominio, categoria FROM dominios WHERE idioma IS NULL")
rows = cursor.fetchall()
print(f"Encontrados {len(rows)} dominios sin idioma clasificado en la base de datos.")

for row in rows:
    dom = row[0]
    existing_cat = row[1]
    
    # Usar el analizador local de fallback para clasificar el dominio de forma rápida
    analysis = llm_helper.fallback_domain_analysis(dom)
    idioma = analysis.get("idioma", "en")
    pais_region = analysis.get("pais_region", "US")
    # Si no tiene categoría guardada, usar la identificada
    categoria = existing_cat if existing_cat else analysis.get("categoria", "Nicho General")
    
    print(f"Clasificando: {dom} -> Idioma: {idioma} | Región: {pais_region} | Categoría: {categoria}")
    cursor.execute("""
        UPDATE dominios 
        SET idioma = ?, pais_region = ?, categoria = ?
        WHERE dominio = ?
    """, (idioma, pais_region, categoria, dom))

conn.commit()
conn.close()
print("¡Clasificación e inicio de metadatos de dominios completados con éxito!")
