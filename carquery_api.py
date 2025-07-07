import requests

BASE_URL = "https://www.carqueryapi.com/api/0.3/"

def get_brands():
    resp = requests.get(f"{BASE_URL}?cmd=getMakes")
    data = resp.json()
    brands = sorted({item['make_display'] for item in data['Makes']})
    return brands

def get_models(brand):
    resp = requests.get(f"{BASE_URL}?cmd=getModels&make={brand.lower()}")
    data = resp.json()
    models = sorted({item['model_name'] for item in data['Models']})
    return models

def get_years(brand, model):
    resp = requests.get(f"{BASE_URL}?cmd=getTrims&make={brand.lower()}&model={model.lower()}")
    data = resp.json()
    years = sorted({item['model_year'] for item in data['Trims']})
    return years

def get_engines(brand, model, year):
    resp = requests.get(f"{BASE_URL}?cmd=getTrims&make={brand.lower()}&model={model.lower()}&year={year}")
    data = resp.json()
    engines = [{
        "engine_type": trim["model_engine_type"],
        "engine_cc": trim["model_engine_cc"],
        "power_hp": trim["model_engine_power_ps"],
        "desc": trim["model_trim"]
    } for trim in data['Trims']]
    return engines
