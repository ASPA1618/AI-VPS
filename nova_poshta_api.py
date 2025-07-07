import os
import requests

NOVA_POSHTA_API_KEY = os.getenv("NOVA_POSHTA_API_KEY")

def get_warehouses(city_name, warehouse_type="Branch", limit=5):
    url = "https://api.novaposhta.ua/v2.0/json/"
    payload = {
        "apiKey": NOVA_POSHTA_API_KEY,
        "modelName": "Address",
        "calledMethod": "getWarehouses",
        "methodProperties": {
            "CityName": city_name,
            "Limit": limit
        }
    }
    if warehouse_type == "Postomat":
        payload["methodProperties"]["TypeOfWarehouseRef"] = "f9316480-5f2d-425d-bc2c-ac7cd29decf5"
    resp = requests.post(url, json=payload)
    data = resp.json()
    if data.get("success") and data.get("data"):
        return data["data"]
    return []

def get_cities(partial_name):
    url = "https://api.novaposhta.ua/v2.0/json/"
    payload = {
        "apiKey": NOVA_POSHTA_API_KEY,
        "modelName": "Address",
        "calledMethod": "getCities",
        "methodProperties": {
            "FindByString": partial_name,
            "Limit": 5
        }
    }
    resp = requests.post(url, json=payload)
    data = resp.json()
    if data.get("success") and data.get("data"):
        return data["data"]
    return []
