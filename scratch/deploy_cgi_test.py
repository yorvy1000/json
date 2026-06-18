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
    
    # Ruta del archivo de prueba CGI en Hostinger
    cgi_path = "/home/u114856156/domains/mysmartdomains.com/public_html/test.cgi"
    
    # Contenido del CGI
    cgi_content = """#!/usr/bin/python3
print("Content-Type: text/html\\n")
print("<html><head><title>Test CGI</title></head><body>")
print("<h1>¡Prueba CGI de Python Exitosa!</h1>")
import sys
print("<p>Versión de Python en el servidor: " + sys.version + "</p>")
print("</body></html>")
"""
    
    # Crear y escribir el archivo remotamente
    sftp = ssh.open_sftp()
    with sftp.file(cgi_path, 'w') as f:
        f.write(cgi_content)
    sftp.close()
    print(f"Archivo de prueba creado en: {cgi_path}")
    
    # Dar permisos de ejecución (755) al script CGI
    ssh.exec_command(f"chmod 755 {cgi_path}")
    print("Permisos de ejecución (755) asignados al archivo.")
    
    ssh.close()
    print("¡Prueba de CGI desplegada correctamente!")
except Exception as e:
    print(f"Error: {e}")
