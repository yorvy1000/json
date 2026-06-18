import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Simular headers del scraper
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

def test_ddg():
    url = "https://lite.duckduckgo.com/lite/"
    payload = {"q": "Dentists in Denver"}
    print("Probando DuckDuckGo Lite...")
    try:
        r = requests.post(url, data=payload, headers=headers, timeout=10)
        print(f"  Status: {r.status_code}")
        print(f"  Length: {len(r.text)}")
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all('a', class_='result-link')
        print(f"  Links encontrados en DDG: {len(links)}")
        if len(links) > 0:
            for idx, link in enumerate(links[:3]):
                print(f"    [{idx+1}] {link.get_text(strip=True)} -> {link.get('href')}")
    except Exception as e:
        print(f"  Error en DDG: {e}")

def test_bing():
    url = "https://www.bing.com/search"
    params = {"q": "Dentists in Denver"}
    print("\nProbando Bing...")
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"  Status: {r.status_code}")
        print(f"  Length: {len(r.text)}")
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all('h2')
        a_tags = []
        for h2 in links:
            a = h2.find('a')
            if a and a.get('href') and a.get('href').startswith('http'):
                a_tags.append(a)
        print(f"  Links encontrados en Bing: {len(a_tags)}")
        if len(a_tags) > 0:
            for idx, a in enumerate(a_tags[:3]):
                print(f"    [{idx+1}] {a.get_text(strip=True)} -> {a.get('href')}")
    except Exception as e:
        print(f"  Error en Bing: {e}")

def test_yahoo():
    url = "https://search.yahoo.com/search"
    params = {"p": "Dentists in Denver"}
    print("\nProbando Yahoo...")
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"  Status: {r.status_code}")
        print(f"  Length: {len(r.text)}")
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all('h3')
        a_tags = []
        for h3 in links:
            a = h3.find('a')
            if a and a.get('href') and a.get('href').startswith('http'):
                a_tags.append(a)
        print(f"  Links encontrados en Yahoo: {len(a_tags)}")
        if len(a_tags) > 0:
            for idx, a in enumerate(a_tags[:3]):
                print(f"    [{idx+1}] {a.get_text(strip=True)} -> {a.get('href')}")
    except Exception as e:
        print(f"  Error en Yahoo: {e}")

if __name__ == "__main__":
    test_ddg()
    test_bing()
    test_yahoo()
