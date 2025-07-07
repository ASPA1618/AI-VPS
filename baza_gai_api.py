import requests

GAI_API_KEY = "553b2a548f885c1ded8c60588d3e8fe8"
GAI_BASE_URL = "https://baza-gai.com.ua/api/vin/"

def gai_vin_search(vin_code: str):
    """
    Пробивает VIN-код через API Базы ДАІ.
    Возвращает JSON или None.
    """
    params = {
        "api_key": GAI_API_KEY,
        "vin": vin_code
    }
    try:
        resp = requests.get(GAI_BASE_URL, params=params, timeout=10)
        if resp.ok:
            return resp.json()
        else:
            print(f"ГАИ API error: {resp.status_code} {resp.text}")
            return None
    except Exception as e:
        print("ГАИ API exception:", e)
        return None
