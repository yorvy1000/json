import os
import json
import re
import logging
import requests
from config import OPENAI_API_KEY, GEMINI_API_KEY

logger = logging.getLogger("DomainAgent")

# Datos comerciales estáticos de la firma del vendedor (Vibra Deals)
SELLER_NAME = "Vibra Deals"
SELLER_EMAIL = "vibradeals@gmail.com"
SELLER_PHONE = "(813) 842-5302"
SELLER_WEBSITE = "https://mysmartdomains.com/"

def fallback_domain_analysis(domain):
    """
    Analizador heurístico local para cuando no hay API Keys.
    Divide el dominio e intenta identificar la ciudad o nicho.
    """
    # Eliminar extensión
    name = re.sub(r'\.(com|net|org|biz|info|us|co|es)$', '', domain.lower())
    # Reemplazar guiones por espacios
    name_clean = name.replace('-', ' ')
    
    # Lista de ciudades comunes o localizaciones a buscar en el dominio
    locations = [
        "denver", "colorado", "miami", "newyork", "ny", "la", "losangeles", "chicago", 
        "houston", "phoenix", "philadelphia", "sanantonio", "sandiego", "dallas", "austin",
        "orlando", "boston", "atlanta", "seattle", "madrid", "barcelona", "zulia", "caracas"
    ]
    
    found_location = ""
    for loc in locations:
        if loc in name_clean:
            found_location = loc.capitalize()
            # Remover de la cadena para aislar el nicho
            name_clean = name_clean.replace(loc, '').strip()
            break
            
    # Mapear palabras clave a nichos en español/inglés
    niche_map = {
        "heladeria": "Heladerías",
        "heladerias": "Heladerías",
        "icecream": "Ice Cream Shops",
        "roof": "Roofing Contractors",
        "roofing": "Roofing Contractors",
        "contractors": "Contractors",
        "liquor": "Liquor Stores",
        "liquorstore": "Liquor Stores",
        "buyhouse": "Home Buyers",
        "realestate": "Real Estate Agencies",
        "dentista": "Dentistas",
        "dentist": "Dentists",
        "taco": "Tacos",
        "tacos": "Tacos",
        "pizza": "Pizzerías",
        "legal": "Servicios Legales",
        "lawyer": "Lawyers",
        "app": "App Developers",
        "digitalagency": "Digital Agency",
        "agency": "Agency",
        "clean": "Cleaning Services",
        "cleaning": "Cleaning Services",
        "electric": "Electricians",
        "plumbing": "Plumbers"
    }
    
    found_niche = ""
    words = name_clean.split()
    for w in words:
        if w in niche_map:
            found_niche = niche_map[w]
            break
            
    if not found_niche:
        # Intento de búsqueda de subcadenas si no hay coincidencia exacta de palabra
        for k, v in niche_map.items():
            if k in name_clean:
                found_niche = v
                break
                
    if not found_niche:
        found_niche = name_clean.capitalize()
        
    # Detectar idioma para el conector y clasificación
    es_keywords = [
        "heladeria", "heladerias", "dentista", "dentistas", "abogado", "abogados", "taco", "tacos",
        "licor", "licores", "licoreria", "plomeria", "plomero", "clinica", "ropa", "tienda", "casa", 
        "apartamento", "comida", "inmobiliaria", "aplicacion", "tuforro"
    ]
    is_spanish = any(kw in domain.lower() for kw in es_keywords) or domain.lower().endswith(('.es', '.co', '.cl', '.ar', '.mx', '.pe', '.ve'))
    idioma = "es" if is_spanish else "en"
    
    # Determinar pais_region aproximado
    if idioma == "es":
        if found_location and found_location.lower() in ["madrid", "barcelona", "sevilla", "valencia"]:
            pais_region = "ES"
        else:
            pais_region = "Latam"
    else:
        if found_location and found_location.lower() in ["london", "manchester", "birmingham", "leeds", "liverpool", "londres"]:
            pais_region = "UK"
        else:
            pais_region = "US"

    if found_location:
        connector = "en" if is_spanish else "in"
        search_term = f"{found_niche} {connector} {found_location}"
    else:
        search_term = f"{found_niche}"
        if not is_spanish:
            search_term += " businesses"
            
    search_terms = generate_query_variations(found_niche, found_location, idioma)
        
    return {
        "categoria": found_niche,
        "ciudad": found_location,
        "idioma": idioma,
        "pais_region": pais_region,
        "termino_busqueda": search_term,
        "terminos_busqueda": search_terms,
        "dominios_competencia": [f"{name}.net", f"{name}.org", f"{name}.biz", f"{name}.co", f"{name}.info"]
    }

def generate_query_variations(categoria, ciudad, idioma):
    """
    Genera heurísticamente una lista de 3-4 variaciones de términos de búsqueda.
    """
    variations = []
    if idioma == "es":
        if ciudad:
            variations.append(f"{categoria} en {ciudad}")
            variations.append(f"Mejores {categoria} {ciudad}")
            variations.append(f"Servicios de {categoria} {ciudad}")
            variations.append(f"Clínica de {categoria} {ciudad}" if "dentista" in categoria.lower() or "odontolog" in categoria.lower() else f"Negocios de {categoria} {ciudad}")
        else:
            variations.append(f"{categoria}")
            variations.append(f"Mejores {categoria}")
            variations.append(f"Empresas de {categoria}")
            variations.append(f"Servicios de {categoria}")
    else:
        if ciudad:
            variations.append(f"{categoria} in {ciudad}")
            variations.append(f"Best {categoria} {ciudad}")
            variations.append(f"{categoria} services in {ciudad}")
            variations.append(f"Local {categoria} {ciudad}")
        else:
            variations.append(f"{categoria} businesses")
            variations.append(f"Best {categoria}")
            variations.append(f"Local {categoria}")
            variations.append(f"{categoria} services")
    return list(dict.fromkeys(variations)) # de-duplicar manteniendo orden

def analyze_domain(domain):
    """
    Analiza un dominio usando el LLM para extraer la categoría, la ciudad, el idioma, la región, los términos de búsqueda
    y los dominios de la competencia. Si falla, usa el fallback heurístico.
    """
    prompt = (
        f"Analiza el siguiente dominio web que está a la venta: '{domain}'.\n"
        "Debes deducir el nicho de mercado, el idioma predominante del dominio y la localización geográfica implícita.\n"
        "Devuelve un objeto JSON estrictamente formateado con siete campos:\n"
        "1. 'categoria': El nicho o categoría del dominio (Ejemplo: 'Heladerías', 'Dentistas', 'Roofing', 'Real Estate').\n"
        "2. 'ciudad': La ciudad o localización geográfica deducida (Ejemplo: 'Denver', 'Miami', 'Madrid', 'Caracas'). Si no tiene, pon null o vacío.\n"
        "3. 'idioma': El idioma del dominio, 'es' para español o 'en' para inglés.\n"
        "4. 'pais_region': El país o región de mercado implícito ('US', 'UK', 'ES', 'Latam'). Si no se deduce, usa 'US' si el idioma es 'en', o 'Latam' si es 'es'.\n"
        "5. 'termino_busqueda': Una frase concisa principal para buscar negocios competidores (Ejemplo: 'Heladerías en Denver' o 'Roofing Contractors in Denver').\n"
        "6. 'terminos_busqueda': Una lista (array de strings) de 3 a 4 variaciones de búsqueda para buscar negocios competidores. Deben ser variadas (por ejemplo: ['Heladerías en Denver', 'Helados artesanos Denver', 'Mejor heladería Denver', 'Comprar helados Denver'] o para inglés: ['Roofing Contractors in Denver', 'Roof Repair Denver', 'Local Roofers Denver', 'Best Roofing Denver']).\n"
        "7. 'dominios_competencia': Una lista de 3 a 5 dominios alternativos similares que estas empresas podrían usar si no tienen el .com (Ejemplo: ['.net', '.org', '.biz', '.co'] aplicados al nombre base del dominio).\n"
        "Devuelve ÚNICAMENTE el JSON, sin texto explicativo antes ni después."
    )
    
    if OPENAI_API_KEY and OPENAI_API_KEY != "tu_clave_openai_aqui":
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Eres un asistente experto en prospección de dominios y análisis de nichos que responde únicamente en formato JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                res_content = response.json()["choices"][0]["message"]["content"].strip()
                data = json.loads(res_content)
                
                # Asegurar compatibilidad si terminos_busqueda no viene o está vacío
                if "terminos_busqueda" not in data or not data["terminos_busqueda"]:
                    cat = data.get("categoria", "Nicho General")
                    cit = data.get("ciudad")
                    lang = data.get("idioma", "en")
                    data["terminos_busqueda"] = generate_query_variations(cat, cit, lang)
                    
                logger.info(f"Análisis de LLM exitoso para '{domain}': {data}")
                return data
            else:
                logger.warning(f"Respuesta de OpenAI con código {response.status_code}: {response.text}")
        except Exception as e:
            logger.warning(f"Error al llamar a OpenAI para analizar dominio: {e}. Usando fallback local...")
            
    # Fallback si no hay cliente o falló la llamada
    data = fallback_domain_analysis(domain)
    logger.info(f"Análisis heurístico local para '{domain}': {data}")
    return data

def generate_pitch(domain_venta, empresa_nombre, sitio_web_actual):
    """
    Genera un correo persuasivo para ofrecer el dominio en venta al prospecto.
    Incorpora los datos dinámicos/reales del vendedor 'Vibra Deals'.
    """
    prompt = (
        f"Redacta un correo electrónico persuasivo, profesional y corto para ofrecer en venta el dominio '{domain_venta}'.\n"
        f"La empresa destinataria se llama '{empresa_nombre}' y su sitio web actual es '{sitio_web_actual}'.\n"
        "El objetivo es explicarles de forma amigable cómo adquirir este dominio premium .com "
        "mejorará su credibilidad, facilitará que sus clientes los recuerden, impulsará su SEO "
        "y protegerá su marca frente a competidores.\n"
        f"Debes firmar el correo en representación de la empresa '{SELLER_NAME}'.\n"
        f"Incluye la firma comercial con los siguientes datos del vendedor:\n"
        f"- Nombre: {SELLER_NAME}\n"
        f"- Teléfono de contacto: {SELLER_PHONE}\n"
        f"- Correo electrónico: {SELLER_EMAIL}\n"
        f"- Sitio Web de Portafolio: {SELLER_WEBSITE}\n"
        "El tono debe ser profesional, consultivo y no spammer.\n"
        "Escribe el correo en el idioma que corresponda al nombre del dominio o la empresa (inglés o español)."
    )
    
    if OPENAI_API_KEY and OPENAI_API_KEY != "tu_clave_openai_aqui":
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Eres un redactor comercial experto en ventas de dominios premium y marketing digital."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                pitch = response.json()["choices"][0]["message"]["content"].strip()
                return pitch
            else:
                logger.warning(f"Respuesta de OpenAI con código {response.status_code}: {response.text}")
        except Exception as e:
            logger.warning(f"Error al llamar a OpenAI para generar propuesta: {e}. Usando propuesta predefinida...")
            
    # Fallback local predefinido si no hay API Key
    lang = "es" if any(w in domain_venta.lower() for w in ["heladeri", "dentista", "tuforro", "aplicacion", "tacos"]) else "en"
    if lang == "es":
        pitch = (
            f"Asunto: Oportunidad de marca e incremento de ventas para {empresa_nombre}\n\n"
            f"Estimado equipo de {empresa_nombre},\n\n"
            f"Espero que se encuentren muy bien. Me pongo en contacto con ustedes porque he notado que son uno de los "
            f"negocios líderes en su nicho y actualmente operan bajo el sitio web '{sitio_web_actual}'.\n\n"
            f"Recientemente en {SELLER_NAME} hemos puesto a la venta el dominio premium '{domain_venta}'. Como sabrán, poseer la versión exacta "
            f".com de su sector ofrece ventajas competitivas enormes: genera una confianza instantánea en el cliente, "
            f"mejora el posicionamiento en buscadores (SEO) y evita que sus correos corporativos se confundan con otros.\n\n"
            f"Dado que este dominio se adapta perfectamente a su marca, queríamos darles la prioridad antes de listarlo en plataformas "
            f"de subasta pública. Si están interesados o desean discutir los detalles, por favor respondan a este correo o contáctennos directamente.\n\n"
            f"Atentamente,\n"
            f"Equipo de Ventas de {SELLER_NAME}\n"
            f"Teléfono: {SELLER_PHONE}\n"
            f"Email: {SELLER_EMAIL}\n"
            f"Portafolio: {SELLER_WEBSITE}"
        )
    else:
        pitch = (
            f"Subject: Premium Domain Acquisition Opportunity for {empresa_nombre} - {domain_venta}\n\n"
            f"Hello team at {empresa_nombre},\n\n"
            f"I hope you are doing well. I am reaching out to you because you are a standout business in your niche, "
            f"currently operating on '{sitio_web_actual}'.\n\n"
            f"At {SELLER_NAME}, we have recently made the premium domain '{domain_venta}' available for acquisition. Acquiring the exact-match .com domain "
            f"for your brand is one of the most effective ways to boost your online authority, prevent customer confusion, "
            f"and secure a highly valuable digital asset that appreciates over time.\n\n"
            f"Since this domain is a perfect upgrade for your business, we wanted to offer it to you first before it goes to public auction.\n"
            f"Please let me know if you would be interested in discussing this opportunity.\n\n"
            f"Best regards,\n"
            f"Domain Brokerage Team\n"
            f"Company: {SELLER_NAME}\n"
            f"Phone: {SELLER_PHONE}\n"
            f"Email: {SELLER_EMAIL}\n"
            f"Portfolio: {SELLER_WEBSITE}"
        )
    return pitch
