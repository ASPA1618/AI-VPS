import os
import pytesseract
import easyocr
from google.cloud import vision
import io
from PIL import Image

# выбираем движок для OCR
OCR_METHOD = os.getenv("OCR_METHOD", "tesseract")  # tesseract | easyocr | google
TESSERACT_PATH = os.getenv("TESSERACT_PATH", None)
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# EasyOCR reader создаётся один раз
_easyocr_reader = None
if OCR_METHOD == "easyocr":
    _easyocr_reader = easyocr.Reader(['en'])

def extract_vin_from_image(image_path: str) -> str:
    if OCR_METHOD == "tesseract":
        return _extract_tesseract(image_path)
    elif OCR_METHOD == "easyocr":
        return _extract_easyocr(image_path)
    elif OCR_METHOD == "google":
        return _extract_google(image_path)
    else:
        raise ValueError(f"Unknown OCR_METHOD: {OCR_METHOD}")

def _extract_tesseract(image_path: str) -> str:
    try:
        image = Image.open(image_path)
        return pytesseract.image_to_string(image).strip()
    except Exception as e:
        return f"[Tesseract OCR error] {e}"

def _extract_easyocr(image_path: str) -> str:
    try:
        results = _easyocr_reader.readtext(image_path)
        text = " ".join([r[1] for r in results])
        return text.strip()
    except Exception as e:
        return f"[EasyOCR error] {e}"

def _extract_google(image_path: str) -> str:
    try:
        client = vision.ImageAnnotatorClient()
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations
        if texts:
            return texts[0].description.strip()
        return ""
    except Exception as e:
        return f"[Google OCR error] {e}"

if __name__ == "__main__":
    path = "vin_sample.jpg"
    print(f"Using: {OCR_METHOD}")
    print(extract_vin_from_image(path))
