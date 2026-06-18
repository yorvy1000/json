import os
import sys
from dotenv import load_dotenv

# Cargar .env
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, ".env"))

SSH_HOST = os.environ.get("SSH_HOST", "82.197.80.115")
SSH_PORT = int(os.environ.get("SSH_PORT", "65002"))
SSH_USER = os.environ.get("SSH_USER", "u114856156")
SSH_PASSWORD = os.environ.get("SSH_PASSWORD", ")(*&^%$#rRe34S$%^&")

try:
    import paramiko
except ImportError:
    print("Paramiko not installed. Installing paramiko...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD, timeout=15)
        
        # Subir el script
        sftp = ssh.open_sftp()
        local_path = os.path.join(base_dir, "scratch", "print_bing_links.py")
        remote_path = "/home/u114856156/agente_dominio/print_bing_links.py"
        print(f"Subiendo {local_path} a {remote_path}...")
        sftp.put(local_path, remote_path)
        sftp.close()
        
        # Ejecutar el script
        print("Ejecutando script de prueba en Hostinger...")
        cmd = "/usr/bin/python3 /home/u114856156/agente_dominio/print_bing_links.py"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        print("\n--- Salida del script de prueba ---")
        print(output)
        if error:
            print("--- Errores ---")
            print(error)
            
        ssh.close()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
