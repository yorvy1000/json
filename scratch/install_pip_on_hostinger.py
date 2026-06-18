import sys
import os
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
    
    # Descargar get-pip.py para Python 3.6 e instalarlo en espacio de usuario
    cmd = "curl -sS https://bootstrap.pypa.io/pip/3.6/get-pip.py -o get-pip.py && python3 get-pip.py --user"
    print(f"Ejecutando bootstrap de pip: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    out = stdout.read().decode('utf-8').strip()
    err = stderr.read().decode('utf-8').strip()
    
    if out:
        print("Resultado:")
        print(out)
    if err:
        print("Errores/Advertencias:")
        print(err)
        
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
