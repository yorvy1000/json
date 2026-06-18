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
    
    # Buscar carpetas public_html en el servidor
    cmd = "find $HOME -maxdepth 4 -type d -name 'public_html'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8').strip()
    
    print("Carpetas public_html encontradas:")
    print(out)
    
    # También listar el contenido de la carpeta home principal
    stdin, stdout, stderr = ssh.exec_command("ls -la $HOME")
    out_home = stdout.read().decode('utf-8').strip()
    print("\nContenido del directorio $HOME:")
    print(out_home)
    
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
