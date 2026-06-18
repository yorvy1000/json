import re
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from config import get_random_headers

logger = logging.getLogger("DomainAgent")

# Expresiones regulares para búsqueda de correos y teléfonos
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# Regex flexible para números telefónicos (evitando números de código de barras o dimensiones de imagen)
PHONE_REGEX = r'(?:\+?\d{1,3}[ -.]?)?\(?\d{3}\)?[ -.]?\d{3}[ -.]?\d{4}'

def get_base_domain(url):
    """Extrae el dominio base limpio (ej: 'heladeriadenver.com') de una URL o cadena de dominio."""
    if not url:
        return ""
    url = url.lower().strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""

def extract_whatsapp_from_href(href):
    """Extrae el número de teléfono de un enlace de WhatsApp si existe."""
    if not href:
        return None
    # Patrones wa.me o api.whatsapp.com/send?phone=
    match = re.search(r'(?:wa\.me|api\.whatsapp\.com/send.*?phone=)([+\d]+)', href)
    if match:
        return match.group(1)
    return None

def extract_contacts_from_html(html, base_url):
    """Analiza el HTML y extrae correos, teléfonos y enlaces de WhatsApp."""
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    
    # Extraer correos
    emails = set(re.findall(EMAIL_REGEX, text))
    
    # Filtrar correos que sean falsos positivos o extensiones de imagen comunes
    valid_emails = set()
    for email in emails:
        if not email.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
            valid_emails.add(email.lower())
            
    # Extraer teléfonos del texto
    phones = set(re.findall(PHONE_REGEX, text))
    
    # Buscar enlaces href: 'tel:', 'mailto:', o whatsapp
    whatsapp_numbers = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Emails por mailto
        if href.startswith('mailto:'):
            email = href.replace('mailto:', '').split('?')[0].strip()
            if re.match(EMAIL_REGEX, email):
                valid_emails.add(email.lower())
        # Teléfonos por tel:
        elif href.startswith('tel:'):
            phone = href.replace('tel:', '').strip()
            if len(phone) >= 7:
                phones.add(phone)
        # WhatsApp
        elif 'wa.me' in href or 'whatsapp.com' in href:
            num = extract_whatsapp_from_href(href)
            if num:
                whatsapp_numbers.add(num)
                
    return {
        "emails": list(valid_emails),
        "phones": list(phones),
        "whatsapp": list(whatsapp_numbers)
    }

def find_contact_pages(html, base_url):
    """Encuentra enlaces a páginas de contacto o nosotros en la web principal."""
    soup = BeautifulSoup(html, 'html.parser')
    contact_keywords = ["contact", "contacto", "nosotros", "about", "dirección", "address", "about-us", "sobre-nosotros", "donde-estamos"]
    contact_urls = set()
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text().lower()
        
        # Unir enlace relativo
        full_url = urljoin(base_url, href)
        
        # Verificar que pertenezca al mismo dominio
        if get_base_domain(full_url) != get_base_domain(base_url):
            continue
            
        # Revisar si coincide con palabras clave en el href o en el texto del botón
        if any(kw in href.lower() or kw in text for kw in contact_keywords):
            contact_urls.add(full_url)
            
    return list(contact_urls)[:3]  # Limitar a máximo 3 páginas adicionales para velocidad

def hunt_contact_details(target_url, domain_to_sell):
    """
    Función principal para extraer contactos de una web.
    REQUISITO CRÍTICO: Si la empresa ya tiene el dominio en venta, la descarta automáticamente.
    """
    target_base = get_base_domain(target_url)
    sell_base = get_base_domain(domain_to_sell)
    
    if not target_base or not sell_base:
        return None
        
    if target_base == sell_base:
        logger.info(f"DESCARTADO: El sitio {target_url} ya posee el dominio en venta ({domain_to_sell}).")
        return None
        
    logger.info(f"Rastreando contactos en: {target_url}...")
    headers = get_random_headers()
    
    try:
        # Petición a la Homepage
        response = requests.get(target_url, headers=headers, timeout=12, verify=False)
        if response.status_code != 200:
            logger.warning(f"Error al cargar homepage ({response.status_code}): {target_url}")
            return None
            
        html = response.text
        contacts = extract_contacts_from_html(html, target_url)
        
        # Si faltan datos o queremos ampliar la búsqueda, buscamos páginas secundarias
        contact_pages = find_contact_pages(html, target_url)
        for page in contact_pages:
            try:
                logger.info(f"  Rastreando página de contacto secundaria: {page}")
                # Pausa breve antes de la siguiente petición
                import time, random
                time.sleep(random.uniform(1.0, 2.0))
                
                resp_page = requests.get(page, headers=headers, timeout=10, verify=False)
                if resp_page.status_code == 200:
                    page_contacts = extract_contacts_from_html(resp_page.text, page)
                    contacts["emails"].extend(page_contacts["emails"])
                    contacts["phones"].extend(page_contacts["phones"])
                    contacts["whatsapp"].extend(page_contacts["whatsapp"])
            except Exception as e:
                logger.debug(f"Error cargando página de contacto {page}: {e}")
                
        # Limpiar duplicados de las listas acumuladas
        contacts["emails"] = list(set(contacts["emails"]))
        contacts["phones"] = list(set(contacts["phones"]))
        contacts["whatsapp"] = list(set(contacts["whatsapp"]))
        
        return contacts
        
    except Exception as e:
        logger.error(f"Error rastreando contactos en {target_url}: {e}")
        return None
