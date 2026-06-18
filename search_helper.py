import re
import time
import random
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from config import get_random_headers

logger = logging.getLogger("DomainAgent")

def clean_url(url):
    """
    Limpia y extrae la URL real si DuckDuckGo devuelve un enlace de redirección.
    """
    if "duckduckgo.com/y.js" in url or "duckduckgo.com/r.html" in url:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        if "uddg" in query_params:
            return query_params["uddg"][0]
        if "u3" in query_params:
            return query_params["u3"][0]
    return url

def geocode_city(city_name):
    """
    Geocodifica el nombre de la ciudad usando la API gratuita de Nominatim (OpenStreetMap).
    Soporta búsquedas tanto de EE. UU. como de Latinoamérica y España.
    """
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "VibraDealsDomainProspector/1.0 (vibradeals@gmail.com)"}
    params = {"q": city_name, "format": "json", "limit": 1}
    try:
        # Pausa breve de cortesía para Nominatim
        time.sleep(1.0)
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200 and len(response.json()) > 0:
            data = response.json()[0]
            logger.info(f"Geocodificación de '{city_name}': Lat={data['lat']}, Lon={data['lon']}")
            return float(data["lat"]), float(data["lon"])
    except Exception as e:
        logger.warning(f"Error geocodificando ciudad '{city_name}': {e}")
    return None

def search_osm_businesses(niche, city_name, max_results=8):
    """
    Busca negocios locales en OpenStreetMap (Overpass API) dentro de una ciudad.
    Filtra y devuelve sus nombres, teléfonos y páginas web si están registrados.
    Si no tienen web registrada, se marcan como prospectos idóneos (sin web).
    """
    coords = geocode_city(city_name)
    if not coords:
        return []
        
    lat, lon = coords
    niche_lower = niche.lower()
    
    # Mapear nicho a etiquetas comunes de OSM
    osm_tag = ""
    if "heladeri" in niche_lower or "ice cream" in niche_lower:
        osm_tag = 'node["amenity"="ice_cream"]'
    elif "dentist" in niche_lower or "odontolog" in niche_lower or "dentista" in niche_lower:
        osm_tag = 'node["amenity"="dentist"]'
    elif "roof" in niche_lower or "techo" in niche_lower:
        osm_tag = 'node["craft"="roofer"]'
    elif "liquor" in niche_lower or "licor" in niche_lower:
        osm_tag = 'node["shop"="alcohol"]'
    elif "taco" in niche_lower or "restaurant" in niche_lower or "restaurante" in niche_lower:
        osm_tag = 'node["amenity"="restaurant"]'
    else:
        osm_tag = 'node["amenity"="restaurant"]' # Fallback a restaurantes
        
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Consulta Overpass (Radio de 20 km alrededor de las coordenadas de la ciudad)
    query = f"""
    [out:json][timeout:15];
    (
      {osm_tag}(around:20000,{lat},{lon});
      way["amenity"="restaurant"](around:20000,{lat},{lon});
    );
    out tags;
    """
    
    logger.info(f"Buscando en OSM Overpass: '{niche}' en '{city_name}'...")
    try:
        response = requests.post(overpass_url, data={"data": query}, timeout=15)
        if response.status_code != 200:
            return []
            
        data = response.json()
        elements = data.get("elements", [])
        results = []
        
        for elem in elements:
            tags = elem.get("tags", {})
            name = tags.get("name")
            if not name:
                continue
                
            website = tags.get("website")
            phone = tags.get("phone") or tags.get("contact:phone") or tags.get("contact:mobile")
            
            # Si no tiene website, generamos una URL simulada única para identificarlo en contact_hunter
            if not website:
                clean_name = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
                website = f"http://{clean_name}-prospecto.temp"
                
            results.append({
                "nombre": name,
                "web": website,
                "telefono_osm": phone
            })
            
            if len(results) >= max_results:
                break
                
        logger.info(f"Se encontraron {len(results)} empresas locales en OSM Overpass.")
        return results
    except Exception as e:
        logger.warning(f"Error consultando Overpass API: {e}")
        return []

def search_fallback_bing(query_term, max_results=15):
    """
    Realiza una búsqueda alternativa en Bing para encontrar sitios web de empresas.
    Sirve como fallback si DuckDuckGo Lite se bloquea.
    """
    url = "https://www.bing.com/search"
    headers = get_random_headers()
    params = {"q": query_term}
    
    logger.info(f"Buscando en Fallback Bing: '{query_term}'...")
    try:
        time.sleep(random.uniform(2.0, 4.0))
        response = requests.get(url, params=params, headers=headers, timeout=12)
        if response.status_code != 200:
            logger.warning(f"Bing Fallback devolvió código de estado {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        links = soup.find_all('h2')
        exclusions = [
            "duckduckgo.com", "bing.com", "google.com", "wikipedia.org", "yelp.com",
            "facebook.com", "tripadvisor.com", "instagram.com", "linkedin.com",
            "youtube.com", "twitter.com", "yellowpages.com", "foursquare.com",
            "mapquest.com", "groupon.com", "reddit.com", "pinterest.com", "bbb.org",
            "zocdoc.com", "superpages.com", "expertise.com", "threebestrated.com",
            "usnews.com", "houzeo.com", "listwithclever.com", "redsucursalesve.com",
            "wanderlog.com", "dentistadental.com", "dentispot.com", "liquorfind.com",
            "microsoft.com"
        ]
        
        for h2 in links:
            a_tag = h2.find('a')
            if not a_tag:
                continue
                
            name = a_tag.get_text(strip=True)
            raw_url = a_tag.get('href')
            if not raw_url or not raw_url.startswith("http"):
                continue
                
            web_url = clean_url(raw_url)
            parsed_url = urlparse(web_url)
            domain = parsed_url.netloc.lower()
            
            if any(ex in domain for ex in exclusions) or not parsed_url.scheme:
                continue
                
            if not any(r['web'] == web_url for r in results):
                results.append({
                    "nombre": name,
                    "web": f"{parsed_url.scheme}://{parsed_url.netloc}",
                    "telefono_osm": None
                })
                
            if len(results) >= max_results:
                break
                
        logger.info(f"Se encontraron {len(results)} empresas en Fallback Bing.")
        return results
    except Exception as e:
        logger.error(f"Error en el buscador Fallback Bing: {e}")
        return []

def search_fallback_yahoo(query_term, max_results=15):
    """
    Realiza una búsqueda alternativa en Yahoo para encontrar sitios web de empresas.
    Sirve como fallback secundario si DuckDuckGo Lite y Bing fallan.
    """
    url = "https://search.yahoo.com/search"
    headers = get_random_headers()
    params = {"p": query_term}
    
    logger.info(f"Buscando en Fallback Yahoo: '{query_term}'...")
    try:
        time.sleep(random.uniform(2.0, 4.0))
        response = requests.get(url, params=params, headers=headers, timeout=12)
        if response.status_code != 200:
            logger.warning(f"Yahoo Fallback devolvió código de estado {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        links = soup.find_all('h3', class_='title')
        if not links:
            links = soup.find_all('h3')
            
        exclusions = [
            "duckduckgo.com", "bing.com", "google.com", "wikipedia.org", "yelp.com",
            "facebook.com", "tripadvisor.com", "instagram.com", "linkedin.com",
            "youtube.com", "twitter.com", "yellowpages.com", "foursquare.com",
            "mapquest.com", "groupon.com", "reddit.com", "pinterest.com", "bbb.org",
            "zocdoc.com", "superpages.com", "expertise.com", "threebestrated.com",
            "usnews.com", "houzeo.com", "listwithclever.com", "redsucursalesve.com",
            "wanderlog.com", "dentistadental.com", "dentispot.com", "liquorfind.com",
            "yahoo.com", "yahoo.co.jp"
        ]
        
        for h3 in links:
            a_tag = h3.find('a')
            if not a_tag:
                continue
                
            name = a_tag.get_text(strip=True)
            raw_url = a_tag.get('href')
            if not raw_url or not raw_url.startswith("http"):
                continue
                
            web_url = clean_url(raw_url)
            parsed_url = urlparse(web_url)
            domain = parsed_url.netloc.lower()
            
            if any(ex in domain for ex in exclusions) or not parsed_url.scheme:
                continue
                
            if not any(r['web'] == web_url for r in results):
                results.append({
                    "nombre": name,
                    "web": f"{parsed_url.scheme}://{parsed_url.netloc}",
                    "telefono_osm": None
                })
                
            if len(results) >= max_results:
                break
                
        logger.info(f"Se encontraron {len(results)} empresas en Fallback Yahoo.")
        return results
    except Exception as e:
        logger.error(f"Error en el buscador Fallback Yahoo: {e}")
        return []

def search_businesses(query_term, max_results=15):
    """
    Realiza una búsqueda tradicional en DuckDuckGo Lite para encontrar sitios web de empresas.
    Si DDG falla o es bloqueado, utiliza Bing y Yahoo como fallbacks ordenados.
    """
    url = "https://lite.duckduckgo.com/lite/"
    headers = get_random_headers()
    payload = {"q": query_term}
    
    logger.info(f"Buscando en DDG Lite: '{query_term}'...")
    results = []
    try:
        time.sleep(random.uniform(2.0, 4.0))
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', class_='result-link')
            
            exclusions = [
                "duckduckgo.com", "bing.com", "google.com", "wikipedia.org", "yelp.com",
                "facebook.com", "tripadvisor.com", "instagram.com", "linkedin.com",
                "youtube.com", "twitter.com", "yellowpages.com", "foursquare.com",
                "mapquest.com", "groupon.com", "reddit.com", "pinterest.com", "bbb.org",
                "zocdoc.com", "superpages.com", "expertise.com", "threebestrated.com",
                "usnews.com", "houzeo.com", "listwithclever.com", "redsucursalesve.com",
                "wanderlog.com", "dentistadental.com", "dentispot.com", "liquorfind.com"
            ]
            
            for link in links:
                name = link.get_text(strip=True)
                raw_url = link.get('href')
                if not raw_url:
                    continue
                    
                web_url = clean_url(raw_url)
                parsed_url = urlparse(web_url)
                domain = parsed_url.netloc.lower()
                
                if any(ex in domain for ex in exclusions) or not parsed_url.scheme:
                    continue
                    
                if not any(r['web'] == web_url for r in results):
                    results.append({
                        "nombre": name,
                        "web": f"{parsed_url.scheme}://{parsed_url.netloc}",
                        "telefono_osm": None
                    })
                    
                if len(results) >= max_results:
                    break
            
            logger.info(f"Se encontraron {len(results)} empresas en DDG.")
        else:
            logger.warning(f"DDG Lite devolvió código de estado {response.status_code}. Activando fallbacks...")
            
    except Exception as e:
        logger.error(f"Error en el buscador DuckDuckGo: {e}. Activando fallbacks...")
        
    # Si DDG falló o no devolvió resultados orgánicos (bloqueo / captcha)
    if not results:
        results = search_fallback_bing(query_term, max_results)
        if not results:
            results = search_fallback_yahoo(query_term, max_results)
            
    return results
