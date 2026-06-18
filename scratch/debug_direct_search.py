import sys
import os
import logging

# Configurar logs para consola
logging.basicConfig(level=logging.INFO)

# Añadir directorio actual
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from search_helper import search_businesses

def test():
    print("Ejecutando search_businesses('Home Buyers in Denver')...")
    res = search_businesses("Home Buyers in Denver")
    print(f"\nResultado final ({len(res)} empresas):")
    for idx, r in enumerate(res):
        print(f"  [{idx+1}] {r['nombre']} -> {r['web']}")

if __name__ == "__main__":
    test()
