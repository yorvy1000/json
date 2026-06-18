import os
import sys
import argparse
import sqlite3
import smtplib
import json
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
from dotenv import load_dotenv

# Configurar logs básicos
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EmailCLI")

# Cargar variables de entorno del archivo .env local
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, ".env"))

# Importar ruta de base de datos desde config.py
sys.path.append(base_dir)
import config
DB_PATH = config.DB_PATH

import subprocess

def send_email_via_local_sendmail(msg, to_email):
    """Envía el correo usando el comando local sendmail del servidor (fallback sin SMTP)."""
    # Intentar buscar el ejecutable en rutas comunes
    sendmail_paths = ["/usr/sbin/sendmail", "/usr/lib/sendmail", "sendmail"]
    for path in sendmail_paths:
        try:
            p = subprocess.Popen([path, "-t", "-oi"], stdin=subprocess.PIPE, universal_newlines=True)
            p.communicate(msg.as_string())
            if p.returncode == 0:
                logger.info(f"Correo enviado exitosamente usando sendmail local ({path}).")
                return True
        except Exception as e:
            logger.warning(f"Fallo al intentar usar sendmail en la ruta {path}: {e}")
    return False

def send_html_email_via_smtp(lead, smtp_server, smtp_port, smtp_user, smtp_password, custom_subject=None, custom_body=None, test_recipient_email=None):
    """Redacta y envía el correo HTML con logo en línea (CID) mediante SMTP."""
    body = custom_body if custom_body is not None else lead['propuesta_texto']
    subject = custom_subject if custom_subject is not None else f"Oportunidad de adquisición de marca - {lead['dominio_venta']}"
    
    # Intentar extraer el asunto automático si está estructurado
    if custom_subject is None:
        lines = body.split('\n')
        for line in lines:
            if line.startswith("Asunto:") or line.startswith("Subject:"):
                subject = line.replace("Asunto:", "").replace("Subject:", "").strip()
                body = "\n".join(lines[lines.index(line)+1:]).strip()
                break
                
    # Convertir saltos de línea dobles del cuerpo en párrafos HTML
    paragraphs = body.split('\n\n')
    body_html = ""
    for p in paragraphs:
        if p.strip():
            p_clean = p.strip().replace('\n', '<br>')
            body_html += f"<p style='margin-bottom: 15px; color: #374151; font-size: 15px; line-height: 1.6;'>{p_clean}</p>"
            
    # Plantilla HTML con cabecera corporativa y pie con logo
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #374151;
                background-color: #f3f4f6;
                margin: 0;
                padding: 0;
            }}
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                border: 1px solid #e5e7eb;
            }}
            .email-header {{
                background: linear-gradient(135deg, #0b0f19, #111827);
                padding: 25px 20px;
                text-align: center;
                border-bottom: 3px solid #8b5cf6;
            }}
            .email-body {{
                padding: 35px 30px;
                line-height: 1.6;
            }}
            .domain-badge-box {{
                text-align: center;
                margin: 25px 0;
            }}
            .domain-badge {{
                display: inline-block;
                background-color: rgba(139, 92, 246, 0.08);
                color: #6d28d9;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 18px;
                border: 1px solid rgba(139, 92, 246, 0.15);
                letter-spacing: 0.5px;
            }}
            .email-footer {{
                background-color: #f9fafb;
                padding: 25px 30px;
                border-top: 1px solid #e5e7eb;
                font-size: 13px;
                color: #6b7280;
            }}
            .footer-title {{
                font-weight: bold;
                color: #1f2937;
                margin-bottom: 5px;
            }}
            .footer-info {{
                margin-top: 10px;
                line-height: 1.5;
            }}
            .footer-info a {{
                color: #6366f1;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <img src="cid:logo_img" alt="MySmartDomains.com" style="max-height: 60px; border-radius: 4px; display: block; margin: 0 auto;">
            </div>
            <div class="email-body">
                {body_html}
                <div class="domain-badge-box">
                    <div class="domain-badge">{lead['dominio_venta']}</div>
                </div>
            </div>
            <div class="email-footer">
                <div class="footer-title">Vibra Deals Brokerage Services</div>
                <div>Aviso informativo sobre activos de marca digital y adquisición de dominios.</div>
                <div class="footer-info">
                    Teléfono comercial: <strong>(813) 842-5302</strong><br>
                    Email: <a href="mailto:vibradeals@gmail.com">vibradeals@gmail.com</a><br>
                    Catálogo oficial: <a href="https://mysmartdomains.com/" target="_blank">mysmartdomains.com</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    to_email = test_recipient_email if test_recipient_email else (lead['correo'].split(', ')[0] if lead['correo'] else "")
    if not to_email:
        raise ValueError("El lead no tiene correo de contacto registrado.")

    # Configurar MIME con soporte para adjuntos en línea (relacionados)
    msg = MIMEMultipart('related')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = f"Vibra Deals <{smtp_user}>"
    msg['To'] = to_email
    
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)
    
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg_alternative.attach(html_part)
    
    # Adjuntar logo.png localmente usando CID
    logo_path = os.path.join(base_dir, 'static', 'logo.png')
    # Intentar buscar logo alternativamente en la raíz de cgi-bin o public_html si se ejecuta desde web
    if not os.path.exists(logo_path):
        logo_path = os.path.join(base_dir, 'logo.png') # fallbacks
        
    if os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                img_data = f.read()
            msg_image = MIMEImage(img_data)
            msg_image.add_header('Content-ID', '<logo_img>')
            msg_image.add_header('Content-Disposition', 'inline', filename='logo.png')
            msg.attach(msg_image)
        except Exception as img_err:
            logger.warning(f"Error al adjuntar logo: {img_err}")
            
    # Determinar si tenemos credenciales SMTP válidas configuradas
    has_smtp = (smtp_server and smtp_port and smtp_user and smtp_password and 
                "tu_contrase" not in smtp_password and 
                "tu_clave" not in smtp_password and 
                smtp_password != "tu_password_aqui")
    
    if not has_smtp:
        logger.info("Credenciales SMTP no configuradas o con valores por defecto. Intentando enviar vía sendmail nativo del servidor...")
        if send_email_via_local_sendmail(msg, to_email):
            logger.info("Envío nativo sendmail exitoso.")
            return
        else:
            raise ValueError("Las credenciales SMTP en el archivo .env no están configuradas y el envío nativo a través de sendmail falló. Por favor edita tu archivo .env.")
            
    # Enviar por SMTP (soporta SSL en 465, TLS/STARTTLS en 587 u otros)
    try:
        port = int(smtp_port)
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_server, port)
        else:
            server = smtplib.SMTP(smtp_server, port)
            server.starttls()
            
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [to_email], msg.as_string())
        server.quit()
        logger.info("Correo enviado exitosamente vía SMTP.")
    except Exception as smtp_err:
        logger.warning(f"Fallo al enviar vía SMTP ({smtp_err}). Intentando fallback con sendmail nativo del servidor...")
        if send_email_via_local_sendmail(msg, to_email):
            logger.info("Envío nativo sendmail exitoso (fallback).")
            return
            
        # Si también falla sendmail, levantar el error original de SMTP formateado de manera amigable
        if isinstance(smtp_err, UnicodeEncodeError):
            raise ValueError("Error de codificación en las credenciales SMTP. Asegúrate de que tu contraseña en el archivo .env no contenga caracteres especiales (como la 'ñ' en 'contraseña').")
        elif isinstance(smtp_err, smtplib.SMTPAuthenticationError):
            raise ValueError("Error de autenticación SMTP: Usuario o contraseña de aplicación incorrectos. Verifica tu configuración en el archivo .env.")
        else:
            raise ValueError(f"Error al conectar/enviar vía SMTP: {str(smtp_err)} (y también falló el fallback nativo de sendmail).")

def main():
    parser = argparse.ArgumentParser(description="Envío de correos por SMTP desde consola (PHP Hybrid Helper)")
    parser.add_argument("--lead_id", type=int, required=True, help="ID del lead a procesar")
    parser.add_argument("--subject", type=str, default=None, help="Asunto personalizado del correo")
    parser.add_argument("--body", type=str, default=None, help="Cuerpo personalizado del correo")
    parser.add_argument("--test_recipient", type=str, default=None, help="Recipient email for testing purposes (overrides lead's email)")
    args = parser.parse_args()

    # Cargar datos SMTP desde variables de entorno
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_user = os.environ.get("SMTP_USER") or os.environ.get("SMTP_EMAIL")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    # Las comprobaciones y fallbacks se realizan dentro de send_html_email_via_smtp

    try:
        # Abrir base de datos SQLite con timeout de 30s para evitar bloqueos
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener datos del lead
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (args.lead_id,))
        row = cursor.fetchone()
        
        if not row:
            print(json.dumps({"success": False, "error": f"Lead con ID {args.lead_id} no encontrado."}))
            sys.exit(1)
            
        lead = dict(row)
        
        if not lead.get("correo"):
            print(json.dumps({"success": False, "error": "El lead no tiene correo de contacto registrado."}))
            sys.exit(1)
            
        # Enviar correo
        send_html_email_via_smtp(
            lead=lead,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            custom_subject=args.subject,
            custom_body=args.body,
            test_recipient_email=args.test_recipient
        )
        
        # Actualizar estado a CONTACTADO en SQLite solo si no es un correo de prueba
        if not args.test_recipient:
            cursor.execute("UPDATE clientes SET estado = 'CONTACTADO' WHERE id = ?", (args.lead_id,))
            conn.commit()
        conn.close()
        
        print(json.dumps({"success": True, "message": f"Correo enviado correctamente a {lead['correo']}."}))
        
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        print(json.dumps({"success": False, "error": str(e), "traceback": tb_str}))
        sys.exit(1)

if __name__ == "__main__":
    main()
