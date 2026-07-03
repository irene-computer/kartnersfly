# test_booking.py
import sqlite3
import requests
import json

# Tester l'API directement
data = {
    "destination_id": 1,
    "destination_name": "Paris",
    "fullname": "Jean Test",
    "email": "test@test.com",
    "phone": "691234567",
    "departure_date": "2024-12-25",
    "travelers": 2,
    "message": "Test message"
}

response = requests.post('http://localhost:5000/api/booking', 
                        json=data,
                        headers={'Content-Type': 'application/json'})
print("Response:", response.status_code)
print("Result:", response.json())

# Verifier la base
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('SELECT id, fullname, departure_date, created_at FROM bookings ORDER BY id DESC LIMIT 5')
print("\nDernieres reservations dans la base:")
for row in cursor.fetchall():
    print(f"  ID:{row[0]} | Nom:{row[1]} | Date depart:{row[2]} | Cree le:{row[3]}")
conn.close()