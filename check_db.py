# check_db.py
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Verifier la structure de la table services
cursor.execute("PRAGMA table_info(services)")
columns = cursor.fetchall()

print("Structure de la table 'services':")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

conn.close()
