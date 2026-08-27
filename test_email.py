# test_email.py
import os
from dotenv import load_dotenv
import smtplib
import ssl
from email.message import EmailMessage

load_dotenv()

def test_email():
    """Test l'envoi d'email avec la configuration actuelle"""
    try:
        smtp_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('MAIL_PORT', 587))
        sender_email = os.getenv('MAIL_USERNAME', '')
        sender_password = os.getenv('MAIL_PASSWORD', '')
        
        if not sender_email or not sender_password:
            print("Email ou mot de passe non configuré dans .env")
            print("   Vérifiez MAIL_USERNAME et MAIL_PASSWORD")
            return False
        
        print(f" Configuration email:")
        print(f"   Serveur: {smtp_server}")
        print(f"   Port: {smtp_port}")
        print(f"   Expéditeur: {sender_email}")
        print(f"   Mot de passe: {'*' * len(sender_password)}")
        print()
        
        msg = EmailMessage()
        msg['Subject'] = "Test Kartners Newsletter"
        msg['From'] = sender_email
        msg['To'] = sender_email
        
        msg.set_content("""
Bonjour,

Ceci est un test de configuration email pour Kartners Travel Agency.

Si vous recevez cet email, votre configuration fonctionne parfaitement !

Cordialement,
Kartners Travel Agency
""")
        
        print("Envoi de l'email de test...")
        
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        print("Email de test envoyé avec succès !")
        print(f"   Vérifiez votre boîte mail: {sender_email}")
        return True
        
    except Exception as e:
        print(f"Erreur: {str(e)}")
        print()
        print("Solutions possibles:")
        print("1. Vérifiez votre mot de passe (utilisez un mot de passe d'application Gmail)")
        print("2. Activez 'Accès aux applications moins sécurisées' dans Google")
        print("3. Vérifiez votre connexion internet")
        return False

if __name__ == '__main__':
    test_email()