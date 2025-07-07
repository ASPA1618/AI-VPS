import os
import pytesseract
from PIL import Image
import re
from omega_api import vin_simple_search
from baza_gai_api import gai_vin_search
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv
from loguru import logger
from gtts import gTTS
from pydub import AudioSegment

# FSM не нужен — просто словарь для хранения языка пользователя
user_lang = {}

# Языки
LANGUAGES = {
    "uk": ("🇺🇦 Українська", "uk"),
    "ru": ("🇷🇺 Русский", "ru"),
    "en": ("🇬🇧 English", "en")
}

load_dotenv()
TOKEN = os.getenv("BOT_TG_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключаем админ-панель
from handlers.admin import router as admin_router
dp.include_router(admin_router)

MAIN_BOT_ID = 7717263680
ADMINS_GROUP_ID = -1002804535488
LOG_CHAT_ID = -1002528385675

logger.add("bot.log", rotation="10 MB", compression="zip", enqueue=True)

async def log_to_tg(bot, message):
    try:
        await bot.send_message(LOG_CHAT_ID, message)
    except Exception as e:
        logger.error(f"Ошибка при отправке лога в Telegram: {e}")

def extract_vin_from_image(photo_path):
    try:
        text = pytesseract.image_to_string(Image.open(photo_path))
        match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', text)
        logger.info(f"OCR text: {text}")
        if match:
            vin = match.group(0)
            logger.info(f"VIN распознан: {vin}")
            return vin
        logger.warning("VIN не найден в распознанном тексте.")
    except Exception as e:
        logger.error(f"OCR error: {e}")
    return None

async def send_voice(bot, chat_id, text, lang_code):
    # Сохраняем в mp3, конвертируем в ogg через pydub (требует ffmpeg)
    tts = gTTS(text, lang=lang_code)
    tts.save("answer.mp3")
    sound = AudioSegment.from_file("answer.mp3")
    sound.export("answer.ogg", format="ogg", codec="libopus")
    voice_file = FSInputFile("answer.ogg")
    await bot.send_voice(chat_id, voice_file)
    # Удаляем временные файлы
    os.remove("answer.mp3")
    os.remove("answer.ogg")

@dp.message(CommandStart())
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    for k, (title, code) in LANGUAGES.items():
        kb.button(text=title)
    kb.adjust(3)
    await message.answer(
        "Вітаємо! Надішліть, будь ласка, ваш VIN-код текстом або фото техпаспорта (через скрепку 📎).\n\nОберіть мову:",
        reply_markup=kb.as_markup(resize_keyboard=True)
    )
    logger.info(f"User {message.from_user.id} started bot.")
    await log_to_tg(bot, f"🟢 Користувач {message.from_user.id} стартував бота.")

@dp.message(F.text.in_([v[0] for v in LANGUAGES.values()]))
async def choose_lang(message: types.Message):
    # Сохраняем язык для пользователя
    lang_code = [k for k, v in LANGUAGES.items() if v[0] == message.text][0]
    user_lang[message.from_user.id] = lang_code
    await message.answer(f"Обрана мова: {LANGUAGES[lang_code][0]}. Продовжуємо...")
    logger.info(f"User {message.from_user.id} chose language: {lang_code}")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    local_path = f"vin_{message.from_user.id}.jpg"
    await bot.download_file(file_path, local_path)
    logger.info(f"Фото от {message.from_user.id} сохранено: {local_path}")
    await log_to_tg(bot, f"📷 Користувач {message.from_user.id} надіслав фото.")

    vin_code = extract_vin_from_image(local_path)
    lang_code = user_lang.get(message.from_user.id, "uk")
    if vin_code:
        answer = f"Розпізнано VIN: {vin_code}\nПробиваємо у базах..."
        await message.answer(answer)
        await send_voice(bot, message.chat.id, answer, LANGUAGES[lang_code][1])
        logger.info(f"VIN из фото: {vin_code}")
        await process_vin(message, vin_code)
    else:
        answer = "Не вдалося розпізнати VIN-код. Спробуйте ще раз або надішліть текстом."
        await message.answer(answer)
        await send_voice(bot, message.chat.id, answer, LANGUAGES[lang_code][1])
        await bot.send_photo(
            ADMINS_GROUP_ID,
            photo=photo.file_id,
            caption=f"❗ Не удалось распознать VIN с фото пользователя @{message.from_user.username or '-'} | ID: {message.from_user.id}"
        )
        await log_to_tg(bot, f"❗ Фото без VIN від користувача {message.from_user.id}")

@dp.message()
async def handle_user_message(message: types.Message):
    text = message.text.strip() if message.text else ""
    is_vin = len(text) == 17 and all(c.isalnum() for c in text)
    lang_code = user_lang.get(message.from_user.id, "uk")

    if is_vin:
        logger.info(f"VIN від тексту {text} від {message.from_user.id}")
        await process_vin(message, text)
    else:
        answer = "Ваше повідомлення прийнято. Оператор зв'яжеться з вами найближчим часом."
        await message.answer(answer)
        await send_voice(bot, message.chat.id, answer, LANGUAGES[lang_code][1])

        user_info = (
            f"🔔 *Нова заявка від користувача:*\n"
            f"👤 @{message.from_user.username or '-'} | ID: {message.from_user.id}\n"
            f"Текст:\n{text}\n"
        )
        await message.bot.send_message(ADMINS_GROUP_ID, user_info, parse_mode="Markdown")
        logger.info(f"Заявка від {message.from_user.id}: {text}")
        await log_to_tg(bot, f"Заявка від {message.from_user.id} (текст)")

async def process_vin(message, vin_code):
    responses = []
    lang_code = user_lang.get(message.from_user.id, "uk")

    gai_info = gai_vin_search(vin_code)
    if gai_info and gai_info.get('result'):
        car = gai_info['result']
        responses.append(
            f"База ДАІ:\n"
            f"Марка: {car.get('marka', '—')}\n"
            f"Модель: {car.get('model', '—')}\n"
            f"Рік: {car.get('year', '—')}\n"
            f"Двигун: {car.get('engine', '—')}"
        )
    else:
        responses.append("База ДАІ: Немає даних або ліміт вичерпано.")

    omega_info = vin_simple_search(vin_code)
    if omega_info:
        brand = omega_info.get("brand") or omega_info.get("mark") or ""
        model = omega_info.get("model", "")
        if brand or model:
            responses.append(f"Omega:\nМарка: {brand}\nМодель: {model}")
        else:
            responses.append("Omega: Даних мало.")
    else:
        responses.append("Omega: Немає даних.")

    answer = '\n\n'.join(responses)
    await message.answer(answer)
    await send_voice(bot, message.chat.id, answer, LANGUAGES[lang_code][1])
    logger.info(f"Відповідь користувачу {message.from_user.id} по VIN {vin_code}: {responses}")
    await log_to_tg(bot, f"🔍 Пробив по VIN {vin_code} для {message.from_user.id}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
