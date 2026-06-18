import os
import sys
import getpass
from dotenv import load_dotenv

# Cargar .env
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, ".env"))

# SSH details from .env
SSH_HOST = os.environ.get("SSH_HOST", "82.197.80.115")
SSH_PORT = int(os.environ.get("SSH_PORT", "65002"))
SSH_USER = os.environ.get("SSH_USER", "u114856156")
SSH_PASSWORD = os.environ.get("SSH_PASSWORD", ")(*&^%$#rRe34S$%^&")

# Check if paramiko is installed
try:
    import paramiko
except ImportError:
    print("Paramiko not installed. Installing paramiko...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

def main():
    print(f"Iniciando despliegue hacia {SSH_USER}@{SSH_HOST}:{SSH_PORT}...")
    
    # Archivos a transferir
    # (Ruta local, Ruta remota)
    files_to_transfer = [
        (
            os.path.join(base_dir, "panel", "index.php"),
            "/home/u114856156/domains/mysmartdomains.com/public_html/panel/index.php"
        ),
        (
            os.path.join(base_dir, "panel", "api.php"),
            "/home/u114856156/domains/mysmartdomains.com/public_html/panel/api.php"
        ),
        (
            os.path.join(base_dir, "send_email_cli.py"),
            "/home/u114856156/agente_dominio/send_email_cli.py"
        ),
        (
            os.path.join(base_dir, "config.py"),
            "/home/u114856156/agente_dominio/config.py"
        ),
        (
            os.path.join(base_dir, "Yorvis - Lou - Domain process June 2026(Sheet1).csv"),
            "/home/u114856156/agente_dominio/Yorvis - Lou - Domain process June 2026(Sheet1).csv"
        ),
        (
            os.path.join(base_dir, "static", "logo.png"),
            "/home/u114856156/domains/mysmartdomains.com/public_html/static/logo.png"
        ),
        (
            os.path.join(base_dir, "static", "logo.png"),
            "/home/u114856156/agente_dominio/static/logo.png"
        )
    ]
    
    try:
        # Conectar por SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD, timeout=15)
        print("Conexión SSH establecida con éxito.")
        
        # Abrir SFTP
        sftp = ssh.open_sftp()
        print("Sesión SFTP abierta.")
        
        # Crear directorios remotos si no existen
        remote_dirs = [
            "/home/u114856156/domains/mysmartdomains.com/public_html/panel",
            "/home/u114856156/domains/mysmartdomains.com/public_html/static",
            "/home/u114856156/agente_dominio",
            "/home/u114856156/agente_dominio/static"
        ]
        
        for rdir in remote_dirs:
            try:
                sftp.stat(rdir)
                print(f"El directorio remoto ya existe: {rdir}")
            except FileNotFoundError:
                print(f"Creando directorio remoto: {rdir}")
                # mkdir recursivo simple
                parts = rdir.strip("/").split("/")
                current_path = ""
                for part in parts:
                    current_path += "/" + part
                    try:
                        sftp.stat(current_path)
                    except FileNotFoundError:
                        sftp.mkdir(current_path)
        
        # Transferir archivos
        for local, remote in files_to_transfer:
            if not os.path.exists(local):
                print(f"Error: El archivo local no existe: {local}")
                continue
            print(f"Subiendo {os.path.basename(local)} a {remote}...")
            sftp.put(local, remote)
            
        # Dar permisos de ejecución a send_email_cli.py
        try:
            sftp.chmod("/home/u114856156/agente_dominio/send_email_cli.py", 0o755)
            print("Permisos cambiados para send_email_cli.py (755).")
        except Exception as chmod_err:
            print(f"No se pudieron cambiar permisos del script: {chmod_err}")
            
        sftp.close()
        ssh.close()
        print("\n¡Despliegue completado con éxito!")
        
    except Exception as e:
        print(f"\nError durante el despliegue: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
