import requests

url = "http://localhost:8000/api/analyze"
data = {"password": "test123"}
resp = requests.post(url, json=data)
print(resp.json())
