import os
import sys
import time
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
        
        print("--- Iniciando Scraper en segundo plano vía SSH ---")
        
        # Comando para correr en segundo plano usando nohup
        cmd_trigger = "nohup /usr/bin/python3 /home/u114856156/agente_dominio/main.py >> /home/u114856156/agente_dominio/cron_output.log 2>&1 &"
        ssh.exec_command(cmd_trigger)
        print("Comando de ejecución enviado al servidor.")
        
        print("Esperando 5 segundos para que se generen los primeros logs...")
        time.sleep(5)
        
        # Leer el log
        cmd_read = "cat /home/u114856156/agente_dominio/cron_output.log"
        stdin, stdout, stderr = ssh.exec_command(cmd_read)
        log_content = stdout.read().decode('utf-8')
        
        print("\n--- Contenido actual de 'cron_output.log' ---")
        if log_content.strip():
            print(log_content)
        else:
            print("[El archivo de log aún está vacío o no se ha creado. Intenta ejecutar de nuevo en unos segundos.]")
            
        ssh.close()
    except Exception as e:
        print(f"Error al conectar por SSH: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
