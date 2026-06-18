import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

def check_bing():
    url = "https://www.bing.com/search?q=Dentists+in+Denver"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. Imprimir las etiquetas h2
        h2s = soup.find_all('h2')
        print(f"Total H2 tags found: {len(h2s)}")
        for idx, h2 in enumerate(h2s[:10]):
            print(f"  H2 [{idx+1}]: {h2.get_text(strip=True)[:50]} | classes={h2.get('class')}")
            
        # 2. Imprimir todas las etiquetas a
        print("\n--- ALL A TAGS ---")
        a_tags = soup.find_all('a')
        print(f"Total A tags: {len(a_tags)}")
        
        # Buscar enlaces orgánicos
        count = 0
        for idx, a in enumerate(a_tags):
            href = a.get('href', '')
            if href.startswith('http') and not any(ex in href for ex in ["bing.com", "microsoft.com", "passport.net"]):
                parent_info = f"parent={a.parent.name} (class={a.parent.get('class')})"
                grandparent_info = f"grandparent={a.parent.parent.name} (class={a.parent.parent.get('class')})" if a.parent else ""
                print(f"  Link: {href[:60]} | text={a.get_text(strip=True)[:30]} | {parent_info} | {grandparent_info}")
                count += 1
                if count >= 20:
                    break
    except Exception as e:
        print(f"Error checking Bing: {e}")

if __name__ == "__main__":
    check_bing()
