# cron_job.py
from app import app
from models import get_db, get_all_user_emails, get_scholarships_ending_soon
from app import send_scholarship_notification
import datetime

def check_and_notify():
    """Vérifie les bourses arrivant à expiration et envoie des notifications"""
    with app.app_context():
        # Récupérer les bourses qui expirent bientôt
        scholarships = get_scholarships_ending_soon(days=5)
        
        if scholarships:
            recipients = get_all_user_emails()
            
            for scholarship in scholarships:
                scholarship_data = {
                    'country': scholarship['country'],
                    'study_level': scholarship['study_level'],
                    'field_of_study': scholarship['field_of_study'],
                    'deadline': scholarship.get('deadline', 'Date limite proche')
                }
                
                success, fail = send_scholarship_notification(recipients, scholarship_data)
                print(f"[CRON] Notifications envoyées pour la bourse {scholarship['id']}: {success} succès, {fail} échecs")

if __name__ == '__main__':
    check_and_notify()