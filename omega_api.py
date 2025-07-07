import requests

OMEGA_API_KEY = "KuC5w0GstEQf9Gj82uVVFtbdvnKiPHa3"
OMEGA_BASE_URL = "https://public.omega.page"

def vin_simple_search(vin_code: str):
    """
    Ищет по VIN-коду через Omega API.
    Возвращает JSON с результатом или None.
    """
    url = f"{OMEGA_BASE_URL}/publicsearch/simplesearch"
    headers = {
        "Authorization": f"Bearer {OMEGA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": vin_code
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.ok:
            return resp.json()
        else:
            print(f"Omega API error: {resp.status_code} {resp.text}")
            return None
    except Exception as e:
        print("Omega API exception:", e)
        return None
