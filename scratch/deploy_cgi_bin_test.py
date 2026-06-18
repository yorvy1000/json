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
    
    # Crear directorio cgi-bin
    cgi_bin_dir = "/home/u114856156/domains/mysmartdomains.com/public_html/cgi-bin"
    ssh.exec_command(f"mkdir -p {cgi_bin_dir}")
    print(f"Directorio remoto cgi-bin verificado en: {cgi_bin_dir}")
    
    # Ruta del archivo CGI
    cgi_path = f"{cgi_bin_dir}/test.cgi"
    
    # Contenido del CGI
    cgi_content = """#!/usr/bin/python3
print("Content-Type: text/html\\n")
print("<html><head><title>Test CGI</title></head><body>")
print("<h1>¡Prueba CGI de Python en cgi-bin Exitosa!</h1>")
import sys
print("<p>Versión de Python en el servidor: " + sys.version + "</p>")
print("</body></html>")
"""
    
    # Escribir el archivo
    sftp = ssh.open_sftp()
    with sftp.file(cgi_path, 'w') as f:
        f.write(cgi_content)
    sftp.close()
    print(f"Archivo de prueba creado en cgi-bin: {cgi_path}")
    
    # Dar permisos
    ssh.exec_command(f"chmod 755 {cgi_path}")
    print("Permisos de ejecución (755) asignados.")
    
    # Eliminar el test.cgi anterior fuera de cgi-bin para no dejar basura
    ssh.exec_command("rm -f /home/u114856156/domains/mysmartdomains.com/public_html/test.cgi")
    print("Se eliminó el archivo test.cgi antiguo fuera de cgi-bin.")
    
    ssh.close()
    print("¡Despliegue en cgi-bin completado!")
except Exception as e:
    print(f"Error: {e}")
