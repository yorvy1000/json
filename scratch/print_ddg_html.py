import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
}

def analyze():
    # DDG
    try:
        r = requests.post("https://lite.duckduckgo.com/lite/", data={"q": "Dentists in Denver"}, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        print("--- DDG A-TAGS ---")
        a_tags = soup.find_all('a')
        print(f"Total a-tags: {len(a_tags)}")
        for idx, a in enumerate(a_tags[:15]):
            print(f"  [{idx+1}] class={a.get('class')} href={a.get('href')} text={a.get_text(strip=True)[:40]}")
    except Exception as e:
        print(f"DDG Error: {e}")

    # Bing
    try:
        r = requests.get("https://www.bing.com/search?q=Dentists+in+Denver", headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        print("\n--- BING H2-TAGS ---")
        h2s = soup.find_all('h2')
        print(f"Total h2-tags: {len(h2s)}")
        for idx, h2 in enumerate(h2s[:10]):
            a = h2.find('a')
            a_str = f"a-tag: href={a.get('href') if a else None} text={a.get_text(strip=True)[:30] if a else 'None'}"
            print(f"  [{idx+1}] {a_str}")
    except Exception as e:
        print(f"Bing Error: {e}")

if __name__ == "__main__":
    analyze()
