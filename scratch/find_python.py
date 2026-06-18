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
    
    # Listar archivos ejecutables de python
    stdin, stdout, stderr = ssh.exec_command("ls -1 /usr/bin/python* /usr/local/bin/python* 2>/dev/null")
    out = stdout.read().decode('utf-8').strip()
    
    print("Ejecutables de Python encontrados:")
    print(out)
    
    # También probar ejecutar python3.8, python3.9, python3.10
    for cmd in ["python3.8 --version", "python3.9 --version", "python3.10 --version", "python3.11 --version", "python3.12 --version"]:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        ver = stdout.read().decode('utf-8').strip()
        err = stderr.read().decode('utf-8').strip()
        if ver:
            print(f"Coincidencia: {cmd} -> {ver}")
            
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
