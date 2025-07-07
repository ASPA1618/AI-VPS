import os
import requests

N8N_BASE_URL = os.getenv("N8N_BASE_URL")  # добавь в .env
N8N_API_KEY = os.getenv("N8N_API_KEY")    # если используется авторизация

def notify_n8n(event_name, data):
    try:
        res = requests.post(f"{N8N_BASE_URL}/{event_name}", json=data, timeout=5)
        return res.ok
    except Exception as e:
        print("N8N error:", e)
        return False
