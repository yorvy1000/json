import requests

def test_remote():
    url_base = "https://mysmartdomains.com/panel"
    session = requests.Session()
    
    print("1. Intentando cargar página de inicio...")
    r = session.get(f"{url_base}/index.php", verify=True)
    print(f"   Status: {r.status_code}")
    
    print("\n2. Intentando iniciar sesión con admin/admin123...")
    r = session.post(f"{url_base}/index.php", data={
        "username": "admin",
        "password": "admin123"
    }, verify=True)
    print(f"   Status: {r.status_code}")
    
    # Comprobar si redirigió o tiene la sesión activa
    if "Domain Flipping Prospector" in r.text or "Vibra Deals" in r.text:
        print("   ¡Logueado exitosamente!")
    else:
        print("   No se detectó el título de la página interna del panel.")
        # Escribir fragmento para depuración
        print(r.text[:500])
        
    print("\n3. Intentando consultar estadísticas de api.php...")
    r = session.get(f"{url_base}/api.php?action=get_stats", verify=True)
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.text}")
    
    print("\n4. Intentando consultar listado de dominios de api.php...")
    r = session.get(f"{url_base}/api.php?action=get_domains", verify=True)
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.text[:200]}...")

if __name__ == "__main__":
    test_remote()
