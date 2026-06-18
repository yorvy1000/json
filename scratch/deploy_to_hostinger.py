import os
import sys
import paramiko

# Detalles de SSH de Hostinger
hostname = "82.197.80.115"
port = 65002
username = "u114856156"
password = ")(*&^%$#rRe34S$%^&"

# Directorio local (raíz del proyecto)
local_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Directorio remoto en Hostinger
remote_dir = "/home/u114856156/agente_dominio"

# Archivos necesarios para el scraper (backend)
files_to_upload = [
    "main.py",
    "search_helper.py",
    "contact_hunter.py",
    "db_helper.py",
    "llm_helper.py",
    "config.py",
    "requirements.txt",
    ".env"
]

print(f"Iniciando despliegue de archivos locales a {username}@{hostname}:{port}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port=port, username=username, password=password, timeout=15)
    print("Conexión SSH establecida.")
    
    # Crear directorio remoto
    ssh.exec_command(f"mkdir -p {remote_dir}")
    print(f"Directorio remoto creado o verificado en: {remote_dir}")
    
    # Iniciar SFTP para subir archivos
    sftp = ssh.open_sftp()
    
    for filename in files_to_upload:
        local_path = os.path.join(local_dir, filename)
        remote_path = f"{remote_dir}/{filename}"
        
        if os.path.exists(local_path):
            print(f"Subiendo {filename} -> {remote_path}...")
            sftp.put(local_path, remote_path)
        else:
            print(f"Advertencia: Archivo local no encontrado {local_path}")
            
    sftp.close()
    print("Todos los archivos se subieron correctamente.")
    
    # Instalar dependencias compatibles con Python 3.6 en Hostinger
    pip_cmd = "/home/u114856156/.local/bin/pip install --user requests==2.27.1 beautifulsoup4==4.9.3 python-dotenv==0.19.2 urllib3==1.26.18"
    print(f"Instalando dependencias compatibles en Hostinger: {pip_cmd}")
    stdin, stdout, stderr = ssh.exec_command(pip_cmd)
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    
    # Ejecutar una prueba del scraper en Hostinger
    test_cmd = f"cd {remote_dir} && python3 main.py --domain dentistadenver.com --limit 2"
    print(f"Ejecutando prueba del scraper: {test_cmd}")
    stdin, stdout, stderr = ssh.exec_command(test_cmd)
    
    print("=== Salida del Scraper en Hostinger ===")
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    
    ssh.close()
    print("¡Proceso de despliegue completado con éxito!")
except Exception as e:
    print(f"Error durante el despliegue: {e}")
