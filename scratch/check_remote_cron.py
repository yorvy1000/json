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
        # Conectar por SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD, timeout=15)
        
        print("--- Verificando Log de Cron en Hostinger ---")
        
        # Ejecutar comando para ver la fecha y el estado del archivo log
        cmd_check = "ls -lh /home/u114856156/agente_dominio/cron_output.log"
        stdin, stdout, stderr = ssh.exec_command(cmd_check)
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        
        if "No such file or directory" in error or not output:
            print("El archivo 'cron_output.log' aún NO se ha creado.")
            print("Esto significa que la tarea programada (Cron Job) aún no se ha ejecutado por primera vez en Hostinger.")
            print("Sugerencia: Espera a la hora programada en Hostinger, o verifica en el hPanel si guardaste el Cron Job correctamente.")
        else:
            print(f"Log encontrado: {output}")
            print("\nÚltimas 15 líneas del archivo de log:")
            # Mostrar el contenido del archivo
            cmd_read = "tail -n 15 /home/u114856156/agente_dominio/cron_output.log"
            stdin, stdout, stderr = ssh.exec_command(cmd_read)
            log_content = stdout.read().decode('utf-8')
            print(log_content if log_content.strip() else "[El archivo está vacío]")
            
        ssh.close()
    except Exception as e:
        print(f"Error al conectar por SSH: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
