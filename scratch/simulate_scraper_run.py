import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import urllib3
urllib3.disable_warnings()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

exclusions = [
    "duckduckgo.com", "bing.com", "google.com", "wikipedia.org", "yelp.com",
    "facebook.com", "tripadvisor.com", "instagram.com", "linkedin.com",
    "youtube.com", "twitter.com", "yellowpages.com", "foursquare.com",
    "mapquest.com", "groupon.com", "reddit.com", "pinterest.com", "bbb.org",
    "zocdoc.com", "superpages.com", "expertise.com", "threebestrated.com",
    "usnews.com", "houzeo.com", "listwithclever.com", "redsucursalesve.com",
    "wanderlog.com", "dentistadental.com", "dentispot.com", "liquorfind.com"
]

def simulate(query):
    print(f"=== SIMULANDO BÚSQUEDA PARA: {query} ===")
    
    # 1. DDG Lite
    try:
        r = requests.post("https://lite.duckduckgo.com/lite/", data={"q": query}, headers=headers, timeout=10, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all('a', class_='result-link')
        print(f"DDG Lite encontró {len(links)} enlaces totales.")
        for idx, link in enumerate(links):
            href = link.get('href')
            text = link.get_text(strip=True)[:40]
            # Parse link
            parsed = urlparse(href)
            domain = parsed.netloc.lower()
            is_ex = any(ex in domain for ex in exclusions)
            print(f"  [{idx+1}] Text: {text} | Domain: {domain} | Excluded: {is_ex}")
    except Exception as e:
        print(f"Error en DDG: {e}")

if __name__ == "__main__":
    simulate("Home Buyers in Denver")
    simulate("Liquor Stores in Colorado")
