import sys
import os
import subprocess

# Instalar paramiko si no está instalado
try:
    import paramiko
except ImportError:
    print("Paramiko no está instalado. Instalándolo...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

# Detalles de SSH de Hostinger
hostname = "82.197.80.115"
port = 65002
username = "u114856156"
password = ")(*&^%$#rRe34S$%^&"

print(f"Intentando conectar a {username}@{hostname}:{port}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port=port, username=username, password=password, timeout=15)
    
    print("¡Conexión SSH exitosa!")
    
    # Verificar versión de Python
    stdin, stdout, stderr = ssh.exec_command("python3 --version")
    out = stdout.read().decode('utf-8').strip()
    err = stderr.read().decode('utf-8').strip()
    
    if out:
        print(f"Versión de Python en Hostinger: {out}")
    elif err:
        print(f"Error al verificar Python: {err}")
    else:
        print("No se recibió respuesta de python3 --version")
        
    ssh.close()
except Exception as e:
    print(f"Error en la conexión SSH: {e}")
