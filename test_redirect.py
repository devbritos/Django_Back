from decouple import config
import requests

BASE = "http://127.0.0.1:8000"
TEST_USERNAME = config("TEST_USERNAME")
TEST_PASSWORD = config("TEST_PASSWORD")
session = requests.Session()

# 1. Obtener el CSRF token de la página de login
login_page = session.get(f"{BASE}/accounts/login/")
csrf_token = session.cookies.get('csrftoken')

# 2. Hacer login
resp = session.post(
    f"{BASE}/accounts/login/",
    data={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "csrfmiddlewaretoken": csrf_token,
    },
    headers={"Referer": f"{BASE}/accounts/login/"},
    allow_redirects=False,
)
print("Login status:", resp.status_code)
print("Login Location:", resp.headers.get('Location'))

# 3. Seguir manualmente cada redirección, imprimiendo el destino
url = f"{BASE}/dashboard/admin/"
for i in range(5):
    resp = session.get(url, allow_redirects=False)
    location = resp.headers.get('Location')
    print(f"[{i}] {url} -> status {resp.status_code} -> Location: {location}")
    if resp.status_code != 302:
        break
    url = location if location.startswith('http') else BASE + location