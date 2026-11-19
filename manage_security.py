"""
Outils de sécurité en ligne de commande.

    python manage_security.py hash      # empreinte d'un mot de passe -> ADMIN_PASSWORD_HASH
    python manage_security.py totp      # nouveau secret de double authentification -> ADMIN_TOTP_SECRET
    python manage_security.py backup    # sauvegarde immédiate de la base

Sur Fly.io : fly ssh console -C "python manage_security.py backup"
"""
import getpass
import sys


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'hash':
        from werkzeug.security import generate_password_hash
        pw = getpass.getpass('Nouveau mot de passe admin (12 caractères minimum) : ')
        if len(pw) < 12 or pw != getpass.getpass('Confirmez : '):
            sys.exit('Mot de passe trop court ou différent.')
        print(f"\nfly secrets set ADMIN_PASSWORD_HASH='{generate_password_hash(pw)}'\nfly secrets unset ADMIN_PASSWORD")
    elif cmd == 'totp':
        import security
        secret = security.new_totp_secret()
        print(f"Secret : {secret}\nLien pour l'application : {security.totp_uri(secret)}")
        print(f"\nfly secrets set ADMIN_TOTP_SECRET={secret}")
    elif cmd == 'backup':
        import security
        print('Sauvegarde :', security.make_backup())
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
