import requests

url = "http://127.0.0.1:5000/admin/login"
data = {"username": "admin", "password": "Kartners2026!"}

response = requests.post(url, data=data)
print(f"Status: {response.status_code}")
print(f"Redirect: {response.history}")