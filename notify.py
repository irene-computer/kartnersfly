"""
Alerte de l'agence à chaque nouvelle demande (réservation, message, candidature).

- Email : envoyé à NOTIFY_EMAIL (par défaut l'adresse de contact du site),
  avec le compte SMTP déjà configuré (MAIL_USERNAME / MAIL_PASSWORD).
- WhatsApp (facultatif) : via le service gratuit CallMeBot, si CALLMEBOT_PHONE
  et CALLMEBOT_APIKEY sont définis. Activation : envoyez « I allow callmebot to
  send me messages » au +34 644 66 32 62 sur WhatsApp, vous recevez la clé.

Les envois partent en arrière-plan : le visiteur n'attend jamais l'email.
"""
import smtplib
import ssl
import threading
import urllib.parse
import urllib.request
from email.message import EmailMessage
from html import escape

from config import Config

TITLES = {
    'booking': 'Nouvelle demande de réservation',
    'contact': 'Nouveau message de contact',
    'scholarship': 'Nouvelle candidature bourse',
}
ADMIN_PAGES = {
    'booking': '/admin/bookings',
    'contact': '/admin/messages',
    'scholarship': '/admin/scholarships',
}
LABELS = {
    'ref': 'Référence', 'fullname': 'Nom', 'name': 'Nom', 'full_name': 'Nom', 'email': 'Email',
    'phone': 'Téléphone', 'destination_name': 'Destination', 'departure_date': 'Départ',
    'travelers': 'Voyageurs', 'service': 'Service', 'country': 'Pays', 'study_level': 'Niveau',
    'field_of_study': 'Domaine', 'message': 'Message', 'lang': 'Langue du visiteur',
}


def _lines(data):
    return [(LABELS.get(k, k), str(v)) for k, v in data.items() if v not in (None, '') and k in LABELS]


def _send_email(kind, data, site_url):
    to = Config.NOTIFY_EMAIL
    if not (to and Config.MAIL_USERNAME and Config.MAIL_PASSWORD):
        return
    title = TITLES.get(kind, 'Nouvelle demande')
    lines = _lines(data)
    msg = EmailMessage()
    msg['Subject'] = f"[Kartners] {title}" + (f" – {data.get('ref')}" if data.get('ref') else '')
    msg['From'] = Config.MAIL_USERNAME
    msg['To'] = to
    if data.get('email'):
        msg['Reply-To'] = data['email']  # « Répondre » écrit directement au client
    link = site_url.rstrip('/') + ADMIN_PAGES.get(kind, '/admin/dashboard')
    msg.set_content(f"{title}\n\n" + '\n'.join(f"{k} : {v}" for k, v in lines) + f"\n\nOuvrir l'administration : {link}\n")
    rows = ''.join(f"<tr><td style='padding:6px 12px;color:#6b6175'>{escape(k)}</td>"
                   f"<td style='padding:6px 12px;white-space:pre-wrap'>{escape(v)}</td></tr>" for k, v in lines)
    msg.add_alternative(f"""
        <div style="font-family:Arial,sans-serif;max-width:560px">
          <div style="background:#662581;border-bottom:6px solid #01AEF0;color:#fff;padding:18px 22px;border-radius:10px 10px 0 0">
            <strong style="font-size:18px">{escape(title)}</strong>
          </div>
          <table style="border-collapse:collapse;width:100%;background:#fff;border:1px solid #e7e2ea">{rows}</table>
          <p style="margin:18px 0"><a href="{escape(link)}" style="background:#662581;color:#fff;padding:10px 18px;border-radius:999px;text-decoration:none">Ouvrir l'administration</a></p>
        </div>""", subtype='html')
    context = ssl.create_default_context()
    with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=20) as server:
        server.starttls(context=context)
        server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
        server.send_message(msg)


def _send_whatsapp(kind, data):
    if not (Config.CALLMEBOT_PHONE and Config.CALLMEBOT_APIKEY):
        return
    who = data.get('fullname') or data.get('name') or data.get('full_name') or ''
    what = data.get('destination_name') or data.get('service') or data.get('country') or ''
    text = f"{TITLES.get(kind, 'Nouvelle demande')} {data.get('ref', '')}\n{who} – {data.get('phone', '')}\n{what}"
    query = urllib.parse.urlencode({'phone': Config.CALLMEBOT_PHONE, 'text': text[:900], 'apikey': Config.CALLMEBOT_APIKEY})
    urllib.request.urlopen(f"https://api.callmebot.com/whatsapp.php?{query}", timeout=20).read()


def _run(kind, data, site_url):
    for sender in (lambda: _send_email(kind, data, site_url), lambda: _send_whatsapp(kind, data)):
        try:
            sender()
        except Exception as e:  # une alerte ratée ne doit jamais bloquer le site
            print(f"[ALERTE] échec d'envoi ({kind}) : {e}")


def notify_agency(kind, data, site_url='https://www.kartnersagency.com'):
    threading.Thread(target=_run, args=(kind, dict(data), site_url), daemon=True).start()
