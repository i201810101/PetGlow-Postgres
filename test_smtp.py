#!/usr/bin/env python3
"""
Script de prueba para verificar configuración SMTP de Gmail
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def test_smtp_connection():
    """Probar conexión SMTP con Gmail"""
    
    # Leer configuración
    mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = int(os.getenv('MAIL_PORT', 587))
    mail_username = os.getenv('MAIL_USERNAME')
    mail_password = os.getenv('MAIL_PASSWORD')
    admin_email = os.getenv('ADMIN_EMAIL')
    
    print("\n" + "="*60)
    print("🔍 PRUEBA DE CONEXIÓN SMTP - PETGLOW")
    print("="*60)
    print(f"\n📊 Configuración detectada:")
    print(f"   Servidor: {mail_server}:{mail_port}")
    print(f"   Usuario: {mail_username}")
    print(f"   Contraseña: {'*' * len(mail_password) if mail_password else 'NO CONFIGURADA'}")
    print(f"   Admin Email: {admin_email}")
    
    # Validar configuración
    if not all([mail_username, mail_password, admin_email]):
        print("\n❌ ERROR: Configuración incompleta en .env")
        print("\nVerifica que tengas:")
        print("  - MAIL_USERNAME=tu_correo@gmail.com")
        print("  - MAIL_PASSWORD=tu_contraseña_de_aplicacion")
        print("  - ADMIN_EMAIL=correo_destino@gmail.com")
        return False
    
    try:
        print(f"\n🔌 Conectando a {mail_server}:{mail_port}...")
        
        # Conectar con TLS (puerto 587)
        server = smtplib.SMTP(mail_server, mail_port, timeout=10)
        server.set_debuglevel(1)  # Activar debug para ver detalles
        
        print("\n📡 Iniciando STARTTLS...")
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        print(f"\n🔐 Autenticando con {mail_username}...")
        server.login(mail_username, mail_password)
        
        print("\n✅ ¡Autenticación exitosa!")
        
        # Enviar correo de prueba
        print(f"\n📧 Enviando correo de prueba a {admin_email}...")
        
        msg = MIMEMultipart()
        msg['From'] = mail_username
        msg['To'] = admin_email
        msg['Subject'] = '✅ Prueba SMTP PetGlow - Exitosa'
        
        body = """
¡Hola!

Este es un correo de prueba del sistema PetGlow.

Si recibiste este mensaje, significa que la configuración SMTP está funcionando correctamente.

✅ Configuración exitosa
📧 Servidor: smtp.gmail.com
🔐 Puerto: 587 (TLS)

--
Sistema PetGlow
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server.send_message(msg)
        server.quit()
        
        print("\n" + "="*60)
        print("✅ ¡PRUEBA EXITOSA!")
        print("="*60)
        print(f"\n📬 Revisa la bandeja de entrada de: {admin_email}")
        print("   (También revisa SPAM/Promociones si no lo ves)\n")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("\n" + "="*60)
        print("❌ ERROR DE AUTENTICACIÓN")
        print("="*60)
        print(f"\nDetalle: {e}")
        print("\n🔧 Soluciones:")
        print("   1. Verifica que la contraseña sea una 'Contraseña de Aplicación'")
        print("      (NO tu contraseña normal de Gmail)")
        print("\n   2. Genera una nueva en: https://myaccount.google.com/apppasswords")
        print("      - Necesitas tener Verificación en 2 pasos activada")
        print("      - Selecciona 'Correo' como aplicación")
        print("\n   3. Copia la contraseña de 16 caracteres (sin espacios)")
        print("      y actualiza MAIL_PASSWORD en tu .env\n")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ Error SMTP: {e}\n")
        return False
        
    except Exception as e:
        print(f"\n❌ Error general: {e}\n")
        return False

if __name__ == "__main__":
    test_smtp_connection()