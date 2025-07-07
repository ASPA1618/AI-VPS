import json
import os

USERS_PATH = "users.json"

def load_users():
    if not os.path.exists(USERS_PATH):
        return {}
    with open(USERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
