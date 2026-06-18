import os
import sys
import time
import random
import logging
import argparse
import urllib3

# Desactivar advertencias de SSL no válidos/auto-firmados para scraping
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Importar configuraciones y helpers
from config import CSV_PATH
import db_helper
import llm_helper
import search_helper
import contact_hunter

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DomainAgent")

# Crear manejador de archivo para los logs persistentes
file_handler = logging.FileHandler("agent_activity.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def read_domains_from_csv(csv_path):
    """
    Lee la lista de dominios y sus metadatos (año de antigüedad y score) desde el CSV.
    Retorna una lista de diccionarios: [{'domain': '...', 'year': 2016, 'score': 1164}]
    """
    domain_records = []
    if not os.path.exists(csv_path):
        logger.error(f"El archivo CSV no existe en la ruta especificada: {csv_path}")
        return domain_records
        
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Separar por ';'
                parts = line.split(';')
                domain = parts[0].strip()
                
                # Ignorar encabezados comunes o nombres vacíos
                if domain.lower() in ["domains", "domain", "dominio", "dominios"] or not domain:
                    continue
                # Validar estructura básica de dominio
                if '.' in domain and not domain.startswith(';'):
                    year = None
                    score = None
                    
                    if len(parts) > 1 and parts[1].strip().isdigit():
                        year = int(parts[1].strip())
                    if len(parts) > 2 and parts[2].strip().isdigit():
                        score = int(parts[2].strip())
                        
                    domain_records.append({
                        "domain": domain,
                        "year": year,
                        "score": score
                    })
        logger.info(f"Se cargaron {len(domain_records)} dominios con metadatos desde el CSV.")
    except Exception as e:
        logger.error(f"Error al leer el CSV: {e}")
    return domain_records

def process_single_domain(domain, max_candidates=10):
    """
    Realiza el flujo completo para un solo dominio premium.
    """
    logger.info(f"\n=== PROCESANDO DOMINIO: {domain} ===")
    
    # 1. Análisis Dinámico (LLM o heurística local)
    analysis = llm_helper.analyze_domain(domain)
    search_query = analysis.get("termino_busqueda")
    categoria = analysis.get("categoria", "Nicho General")
    ciudad = analysis.get("ciudad")
    idioma = analysis.get("idioma", "en")
    pais_region = analysis.get("pais_region", "US")
    
    # Si no tiene ciudad deducida, rotar una de la lista según el idioma/región
    if not ciudad:
        spanish_cities = ["Madrid", "Barcelona", "Bogota", "Ciudad de Mexico", "Buenos Aires", "Caracas", "Santiago", "Lima", "Sevilla", "Valencia"]
        english_cities = ["London", "New York", "Denver", "Miami", "Los Angeles", "Chicago", "Manchester", "Birmingham", "Leeds", "Liverpool"]
        
        if idioma == "es":
            ciudad = random.choice(spanish_cities)
            pais_region = "Latam" if random.random() > 0.3 else "ES" # Probabilidad
        else:
            if pais_region == "UK":
                ciudad = random.choice(["London", "Manchester", "Birmingham", "Leeds", "Liverpool"])
            else:
                ciudad = random.choice(["New York", "Denver", "Miami", "Los Angeles", "Chicago"])
        
    # Generar la lista de queries variadas
    if not analysis.get("ciudad") and ciudad:
        search_queries = llm_helper.generate_query_variations(categoria, ciudad, idioma)
    else:
        search_queries = analysis.get("terminos_busqueda")
        if not search_queries:
            search_queries = llm_helper.generate_query_variations(categoria, ciudad, idioma)
            
    logger.info(f"Términos de búsqueda variados a ejecutar: {search_queries}")
    
    # Actualizar los metadatos del dominio en la base de datos (con idioma y región)
    db_helper.add_domain_metadata(domain, categoria, None, None, estado="PENDIENTE", idioma=idioma, pais_region=pais_region)
    logger.info(f"Categoría identificada para {domain}: '{categoria}' ({idioma}/{pais_region}) en '{ciudad}'")
        
    # 2. Búsqueda de empresas candidatas
    candidates = []
    existing_webs = set()
    
    # Método A: Búsqueda tradicional en DuckDuckGo Lite con fallbacks Bing/Yahoo
    for q in search_queries:
        logger.info(f"Ejecutando búsqueda para opción de consulta: '{q}'")
        try:
            q_results = search_helper.search_businesses(q, max_results=5)
            for r in q_results:
                if r["web"] not in existing_webs:
                    candidates.append(r)
                    existing_webs.add(r["web"])
        except Exception as e:
            logger.error(f"Error en búsqueda de la consulta '{q}': {e}")
        # Pausa breve entre variaciones para evitar bloqueos
        time.sleep(random.uniform(2.0, 3.5))
    
    # Método B: Búsqueda en OpenStreetMap (Overpass API) para encontrar negocios locales (incluidos los que no tienen web)
    if ciudad and categoria:
        try:
            osm_candidates = search_helper.search_osm_businesses(categoria, ciudad, max_results=max_candidates)
            # Combinar resultados evitando duplicados en la URL
            for osm_cand in osm_candidates:
                if osm_cand["web"] not in existing_webs:
                    candidates.append(osm_cand)
                    existing_webs.add(osm_cand["web"])
        except Exception as e:
            logger.warning(f"Error integrando candidatos de OSM: {e}")
            
    # Limitar la lista final de candidatos al número solicitado
    candidates = candidates[:max_candidates]
    logger.info(f"Lista consolidada de candidatos ({len(candidates)} empresas): {[c['nombre'] for c in candidates]}")
            
    if not candidates:
        logger.warning(f"No se encontraron empresas candidatas para {domain}.")
        return False
        
    prospects_found = 0
    for idx, candidate in enumerate(candidates):
        web = candidate["web"]
        name = candidate["nombre"]
        osm_phone = candidate.get("telefono_osm")
        
        logger.info(f"[{idx+1}/{len(candidates)}] Evaluando candidato: {name} ({web})")
        
        # Verificar si ya existe en la base de datos para este dominio (evitar duplicados)
        if db_helper.client_exists(domain, web) or (osm_phone and db_helper.client_exists(domain, "Sin sitio web")):
            logger.info(f"  El candidato ya fue prospectado anteriormente para {domain}. Saltando.")
            continue
            
        email_str = None
        phone_str = None
        pitch = None
        
        # Caso A: Negocio sin sitio web registrado en OpenStreetMap (simulado con temp)
        if "prospecto.temp" in web:
            if not osm_phone:
                logger.info(f"  El negocio sin web '{name}' no tiene teléfono en OSM. Saltando.")
                continue
            phone_str = osm_phone
            web_display = "Sin sitio web registrado"
            logger.info(f"  ¡Negocio sin web encontrado! Teléfono de OSM: {phone_str}")
            logger.info("  Generando propuesta de venta de dominio para negocio sin web...")
            pitch = llm_helper.generate_pitch(domain, name, web_display)
            
            # Guardar en SQLite
            success = db_helper.add_client(
                dominio_venta=domain,
                empresa_nombre=name,
                sitio_web_actual=web_display,
                correo=None,
                telefono=phone_str,
                propuesta_texto=pitch
            )
            if success:
                prospects_found += 1
            continue
            
        # Caso B: Negocio con sitio web (crawling tradicional)
        contacts = contact_hunter.hunt_contact_details(web, domain)
        
        if not contacts:
            # Fue descartado (ej. coincide con el dominio en venta o error de red)
            continue
            
        emails = contacts.get("emails", [])
        phones = contacts.get("phones", [])
        whatsapp = contacts.get("whatsapp", [])
        
        # Si OSM nos dió un teléfono pero el crawler no encontró ninguno, lo agregamos
        if osm_phone and not phones and not whatsapp:
            phones.append(osm_phone)
            
        # Combinar teléfonos y whatsapp para almacenamiento
        all_phones = list(set(phones + whatsapp))
        
        email_str = ", ".join(emails) if emails else None
        phone_str = ", ".join(all_phones) if all_phones else None
        
        # Requisito: Guardar solo si encontramos al menos un medio de contacto directo
        if not email_str and not phone_str:
            logger.info(f"  No se encontraron emails ni teléfonos para {name}. Saltando.")
            continue
            
        # 4. Redacción de propuesta y almacenamiento en SQLite
        logger.info(f"  ¡Contactos encontrados! Emails: {email_str} | Teléfonos: {phone_str}")
        logger.info("  Generando propuesta de correo comercial personalizada...")
        
        pitch = llm_helper.generate_pitch(domain, name, web)
        
        # Guardar en SQLite
        success = db_helper.add_client(
            dominio_venta=domain,
            empresa_nombre=name,
            sitio_web_actual=web,
            correo=email_str,
            telefono=phone_str,
            propuesta_texto=pitch
        )
        if success:
            prospects_found += 1
            
        # Pausa aleatoria entre rastreos para evitar baneos de IPs
        time.sleep(random.uniform(2.0, 5.0))
        
    logger.info(f"Análisis del dominio '{domain}' completado. Se agregaron {prospects_found} nuevos leads.")
    return True

def print_stats():
    """Muestra estadísticas actuales del agente almacenadas en la base de datos."""
    conn = db_helper.get_db_connection()
    cursor = conn.cursor()
    
    # Dominios procesados
    cursor.execute("SELECT COUNT(*), estado FROM dominios GROUP BY estado")
    dominios = cursor.fetchall()
    
    # Clientes encontrados
    cursor.execute("SELECT COUNT(*), estado FROM clientes GROUP BY estado")
    leads = cursor.fetchall()
    
    print("\n" + "="*40)
    print("ESTADÍSTICAS DEL AGENTE DE DOMINIOS")
    print("="*40)
    print("Dominios Analizados:")
    if dominios:
        for row in dominios:
            print(f"  - {row[1]}: {row[0]}")
    else:
        print("  - Ninguno procesado aún.")
        
    print("\nLeads Calificados Encontrados:")
    if leads:
        for row in leads:
            print(f"  - Estado '{row[1]}': {row[0]}")
    else:
        print("  - Ningún lead guardado aún.")
    print("="*40 + "\n")
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Agente de Prospección Inteligente de Domain Flipping (24/7)")
    parser.add_argument("--domain", type=str, help="Procesa un único dominio premium específico para pruebas.")
    parser.add_argument("--limit", type=int, default=8, help="Límite máximo de empresas competidoras a evaluar por dominio (por defecto 8).")
    parser.add_argument("--stats", action="store_true", help="Muestra estadísticas de la base de datos SQLite y sale.")
    args = parser.parse_args()

    # Inicializar Base de Datos
    db_helper.init_db()

    if args.stats:
        print_stats()
        return

    # Si se especificó un dominio particular
    if args.domain:
        # Registrar metadatos básicos por seguridad
        analysis_temp = llm_helper.fallback_domain_analysis(args.domain)
        idioma = analysis_temp.get("idioma", "en")
        pais_region = analysis_temp.get("pais_region", "US")
        db_helper.add_domain_metadata(args.domain, "Prueba Individual", 2026, 999, estado="PENDIENTE", idioma=idioma, pais_region=pais_region)
        process_single_domain(args.domain, max_candidates=args.limit)
        return

    # Si no, procedemos con la lista del CSV
    logger.info(f"Iniciando prospección masiva desde el archivo CSV: {CSV_PATH}")
    domain_records = read_domains_from_csv(CSV_PATH)
    
    if not domain_records:
        logger.error("No hay dominios que procesar. Verifica el archivo CSV.")
        sys.exit(1)
        
    processed_count = 0
    for record in domain_records:
        dom = record["domain"]
        year = record["year"]
        score = record["score"]
        
        # Registrar/actualizar metadatos básicos en SQLite antes de procesar con idioma y región preliminares
        analysis_temp = llm_helper.fallback_domain_analysis(dom)
        idioma = analysis_temp.get("idioma", "en")
        pais_region = analysis_temp.get("pais_region", "US")
        db_helper.add_domain_metadata(dom, None, year, score, estado="PENDIENTE", idioma=idioma, pais_region=pais_region)
        
        # Verificar si ya fue procesado con éxito anteriormente
        if db_helper.is_domain_processed(dom):
            logger.info(f"El dominio {dom} ya está marcado como COMPLETADO. Saltando.")
            continue
            
        try:
            success = process_single_domain(dom, max_candidates=args.limit)
            if success:
                db_helper.mark_domain_processed(dom, "COMPLETADO")
                processed_count += 1
            else:
                db_helper.mark_domain_processed(dom, "ERROR_SIN_RESULTADOS")
        except KeyboardInterrupt:
            logger.info("Proceso interrumpido por el usuario. Guardando estado y saliendo...")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error crítico al procesar dominio {dom}: {e}")
            db_helper.mark_domain_processed(dom, "ERROR")
            
        # Pausa entre dominios
        time.sleep(random.uniform(5.0, 10.0))
        
    logger.info(f"Ciclo terminado. Se procesaron {processed_count} nuevos dominios en esta sesión.")
    print_stats()

if __name__ == "__main__":
    main()
