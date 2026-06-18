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
    
    # Ruta del archivo .htaccess
    htaccess_path = "/home/u114856156/domains/mysmartdomains.com/public_html/.htaccess"
    
    sftp = ssh.open_sftp()
    
    # Verificar si existe y leerlo
    exists = False
    try:
        sftp.stat(htaccess_path)
        exists = True
        print(f"El archivo .htaccess existe.")
    except FileNotFoundError:
        print(f"El archivo .htaccess NO existe. Se creará uno nuevo.")
        
    content = ""
    if exists:
        with sftp.open(htaccess_path, 'r') as f:
            content = f.read().decode('utf-8')
            print("Contenido actual de .htaccess:")
            print(content)
            
    # Añadir directivas de CGI al .htaccess
    cgi_directives = "\n# Habilitar ejecucion de scripts CGI Python\nOptions +ExecCGI\nAddHandler cgi-script .cgi\n"
    
    if "AddHandler cgi-script .cgi" not in content:
        new_content = content + cgi_directives
        with sftp.open(htaccess_path, 'w') as f:
            f.write(new_content)
        print("Se añadieron las directivas de CGI a .htaccess.")
    else:
        print("Las directivas de CGI ya están configuradas en .htaccess.")
        
    sftp.close()
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
