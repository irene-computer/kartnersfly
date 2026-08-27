# test_newsletter.py
import os
import datetime
from dotenv import load_dotenv
from app import app, send_bulk_email

load_dotenv()

def test_newsletter():
    """Test d'envoi de newsletter à un seul destinataire"""
    with app.app_context():
        recipients = ['kta2k23@gmail.com']
        subject = "TEST - Newsletter Kartners"
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Test Newsletter</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #8B5CF6, #3B82F6); color: white; padding: 30px; text-align: center; }
                .header h1 { margin: 0; font-size: 24px; }
                .content { padding: 30px; }
                .footer { background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>KARTNERS TRAVEL AGENCY</h1>
                    <p>Test de newsletter</p>
                </div>
                <div class="content">
                    <h2>Ceci est un test de la newsletter</h2>
                    <p>Si vous recevez cet email, la configuration fonctionne !</p>
                    <p>Date du test: {}</p>
                </div>
                <div class="footer">
                    <p>&copy; 2026 Kartners Travel Agency</p>
                    <p>Tel: +237 676 268 350</p>
                </div>
            </div>
        </body>
        </html>
        """.format(datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
        
        success, fail = send_bulk_email(recipients, subject, html_content)
        print(f"Résultat: {success} succès, {fail} échecs")

if __name__ == '__main__':
    test_newsletter()