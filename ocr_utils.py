from PIL import Image, ImageOps
import pytesseract
import re
from loguru import logger

def extract_vin_from_image(photo_path):
    try:
        img = Image.open(photo_path)
        img = img.convert('L')
        img = ImageOps.autocontrast(img)
        text = pytesseract.image_to_string(img)
        text = text.upper().replace(' ', '')
        for _from, _to in [("O", "0"), ("I", "1"), ("Q", "0"), ("S", "5"), ("B", "8")]:
            text = text.replace(_from, _to)
        matches = re.findall(r'\b[A-HJ-NPR-Z0-9]{17}\b', text)
        if matches:
            logger.info(f"🔍 VIN распізнано: {matches[0]}")
            return matches[0]
    except Exception as e:
        logger.error(f"🛑 OCR error: {e}")
    return None
