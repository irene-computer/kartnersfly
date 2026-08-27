# email_utils.py
from flask_mail import Mail, Message
from flask import render_template_string
import datetime
import os

mail = Mail()

def init_mail(app):
    """Initialise l'extension mail avec les variables d'environnement"""
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', '')
    mail.init_app(app)

def send_booking_confirmation_email(booking_data):
    """Envoie un email de confirmation au client"""
    try:
        if not os.getenv('MAIL_USERNAME') or not os.getenv('MAIL_PASSWORD'):
            print("[ERREUR] Email non configuré")
            return False
        
        email_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Confirmation de reservation</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #8B5CF6, #3B82F6); color: white; padding: 30px; text-align: center; }
                .header h1 { margin: 0; font-size: 24px; }
                .content { padding: 30px; }
                .info-block { background: #f8f9fa; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
                .info-block h3 { margin: 0 0 10px; color: #6B3FA0; }
                .info-row { display: flex; padding: 8px 0; border-bottom: 1px solid #e9ecef; }
                .info-label { width: 120px; font-weight: bold; color: #495057; }
                .info-value { flex: 1; color: #212529; }
                .status { display: inline-block; background: #10B981; color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; }
                .footer { background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #6c757d; }
                .btn { display: inline-block; background: linear-gradient(135deg, #8B5CF6, #3B82F6); color: white; text-decoration: none; padding: 10px 25px; border-radius: 25px; margin-top: 15px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>KARTNERS TRAVEL AGENCY</h1>
                    <p>Votre reservation a ete confirmee</p>
                </div>
                <div class="content">
                    <p>Bonjour <strong>{{ fullname }}</strong>,</p>
                    <p>Nous avons le plaisir de vous confirmer votre reservation de voyage.</p>
                    
                    <div class="info-block">
                        <h3>Details de votre voyage</h3>
                        <div class="info-row">
                            <div class="info-label">Destination :</div>
                            <div class="info-value">{{ destination_name }}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Date de depart :</div>
                            <div class="info-value">{{ departure_date }}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Voyageurs :</div>
                            <div class="info-value">{{ travelers }}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Reference :</div>
                            <div class="info-value">KTA-{{ booking_id }}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Statut :</div>
                            <div class="info-value"><span class="status">Confirmee</span></div>
                        </div>
                    </div>
                    
                    <p>Notre equipe vous contactera prochainement.</p>
                    
                    <div style="text-align: center;">
                        <a href="https://www.kartnersagency.com/contact" class="btn">Nous contacter</a>
                    </div>
                </div>
                <div class="footer">
                    <p>&copy; 2026 Kartners Travel Agency</p>
                    <p>Tel: +237 676 268 350 | Email: {{ os.getenv('MAIL_USERNAME', 'kta2k23@gmail.com') }}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = Message(
            subject=f"Confirmation de reservation - KTA-{booking_data['booking_id']}",
            recipients=[booking_data['email']],
            html=render_template_string(email_template, **booking_data)
        )
        
        mail.send(msg)
        print(f"[INFO] Email de confirmation envoye a {booking_data['email']}")
        return True
        
    except Exception as e:
        print(f"[ERREUR] Envoi email: {str(e)}")
        return False

def send_admin_notification_email(booking_data):
    """Envoie un email de notification a l'admin"""
    try:
        admin_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Nouvelle reservation</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #8B5CF6, #3B82F6); color: white; padding: 20px; text-align: center; }
                .content { padding: 25px; }
                .info-row { display: flex; padding: 8px 0; border-bottom: 1px solid #e9ecef; }
                .info-label { width: 130px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Nouvelle reservation</h2>
                </div>
                <div class="content">
                    <p>Une nouvelle reservation a ete effectuee :</p>
                    <div class="info-row">
                        <div class="info-label">Client :</div>
                        <div>{{ fullname }}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Destination :</div>
                        <div>{{ destination_name }}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Date depart :</div>
                        <div>{{ departure_date }}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Email :</div>
                        <div>{{ email }}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Telephone :</div>
                        <div>{{ phone }}</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        admin_email = os.getenv('MAIL_USERNAME', 'kta2k23@gmail.com')
        
        msg = Message(
            subject=f"[ADMIN] Nouvelle reservation - {booking_data['fullname']}",
            recipients=[admin_email],
            html=render_template_string(admin_template, **booking_data)
        )
        
        mail.send(msg)
        print(f"[INFO] Email admin envoye a {admin_email}")
        return True
    except Exception as e:
        print(f"[ERREUR] Envoi email admin: {str(e)}")
        return False