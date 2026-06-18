import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
}

def check_pages():
    # 1. DDG
    try:
        r = requests.post("https://lite.duckduckgo.com/lite/", data={"q": "Dentists in Denver"}, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.get_text(strip=True) if soup.title else "No Title"
        print(f"DDG Title: {title}")
        print(f"DDG snippet: {r.text[:300].strip()}\n")
    except Exception as e:
        print(f"DDG Error: {e}")

    # 2. Bing
    try:
        r = requests.get("https://www.bing.com/search?q=Dentists+in+Denver", headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.get_text(strip=True) if soup.title else "No Title"
        print(f"Bing Title: {title}")
        print(f"Bing snippet: {r.text[:300].strip()}\n")
    except Exception as e:
        print(f"Bing Error: {e}")

    # 3. Yahoo
    try:
        r = requests.get("https://search.yahoo.com/search?p=Dentists+in+Denver", headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.get_text(strip=True) if soup.title else "No Title"
        print(f"Yahoo Title: {title}")
        print(f"Yahoo snippet: {r.text[:300].strip()}\n")
    except Exception as e:
        print(f"Yahoo Error: {e}")

if __name__ == "__main__":
    check_pages()
