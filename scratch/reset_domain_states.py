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
        
        print("--- Reiniciando estados de dominios en SQLite de Hostinger ---")
        
        # Ejecutar update
        sql_update = (
            "sqlite3 /home/u114856156/agente_dominio/domain_leads.db "
            "\"UPDATE dominios SET estado = 'PENDIENTE' WHERE estado = 'ERROR_SIN_RESULTADOS';\""
        )
        stdin, stdout, stderr = ssh.exec_command(sql_update)
        print("Estados actualizados de 'ERROR_SIN_RESULTADOS' a 'PENDIENTE'.")
        
        # Verificar estados
        sql_check = (
            "sqlite3 /home/u114856156/agente_dominio/domain_leads.db "
            "\"SELECT estado, COUNT(*) FROM dominios GROUP BY estado;\""
        )
        stdin, stdout, stderr = ssh.exec_command(sql_check)
        print("\nNuevos conteos de estado en SQLite:")
        print(stdout.read().decode('utf-8'))
        
        ssh.close()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
