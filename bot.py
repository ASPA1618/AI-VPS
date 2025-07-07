import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv
from loguru import logger

from handlers.admin import router as admin_router
from ocr_utils import extract_vin_from_image
from voice_to_text import recognize_speech
from welcome import make_welcome_text, get_profile_fields
from car_card import create_car_card
from product_menu import get_base_products
from omega_api import vin_simple_search
from baza_gai_api import gai_vin_search
from nova_poshta_api import get_warehouses, get_cities

# Переменные пользователя
user_lang = {}
user_name = {}

load_dotenv()
TOKEN = os.getenv("BOT_TG_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(admin_router)

MAIN_BOT_ID = 7717263680
ADMINS_GROUP_ID = -1002804535488
LOG_CHAT_ID = -1002528385675
ADMIN_IDS = [8102776356]

logger.add("bot.log", rotation="10 MB", compression="zip", enqueue=True)

async def log_to_tg(bot, message):
    try:
        await bot.send_message(LOG_CHAT_ID, message)
    except Exception as e:
        logger.error(f"Ошибка при отправке лога в Telegram: {e}")

@dp.message(CommandStart())
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    for k, (title, code) in {
        "uk": ("🇺🇦 Українська", "uk"),
        "ru": ("🇷🇺 Русский", "ru"),
        "en": ("🇬🇧 English", "en")
    }.items():
        kb.button(text=title)
    kb.adjust(3)
    await message.answer(
        make_welcome_text(),
        reply_markup=kb.as_markup(resize_keyboard=True)
    )
    logger.info(f"User {message.from_user.id} started bot.")
    await log_to_tg(bot, f"🟢 Користувач {message.from_user.id} стартував бота.")

@dp.message(F.text.in_([v[0] for v in {
    "uk": ("🇺🇦 Українська", "uk"),
    "ru": ("🇷🇺 Русский", "ru"),
    "en": ("🇬🇧 English", "en")
}.values()]))
async def choose_lang(message: types.Message):
    lang_code = [k for k, v in {
        "uk": ("🇺🇦 Українська", "uk"),
        "ru": ("🇷🇺 Русский", "ru"),
        "en": ("🇬🇧 English", "en")
    }.items() if v[0] == message.text][0]
    user_lang[message.from_user.id] = lang_code
    suggest_name = (
        f"Як до вас звертатись? (наприклад, {message.from_user.username or message.from_user.id})"
    )
    await message.answer(suggest_name)
    logger.info(f"User {message.from_user.id} chose language: {lang_code}")

@dp.message(lambda message: message.from_user.id not in user_name and not message.text.startswith('/'))
async def set_name(message: types.Message):
    name = message.text.strip()
    user_name[message.from_user.id] = name
    await message.answer(f"Дякуємо, {name}! Тепер надішліть VIN-код або фото техпаспорта.")
    logger.info(f"User {message.from_user.id} set name: {name}")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    if message.from_user.id not in user_name:
        await message.answer("Спочатку вкажіть, як до вас звертатись (введіть ім'я).")
        return
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    local_path = f"vin_{message.from_user.id}.jpg"
    await bot.download_file(file_path, local_path)
    logger.info(f"Фото от {message.from_user.id} сохранено: {local_path}")
    await log_to_tg(bot, f"📷 Користувач {message.from_user.id} надіслав фото.")

    vin_code = extract_vin_from_image(local_path)
    if vin_code:
        await message.answer(f"Розпізнано VIN: {vin_code}\nПробиваємо у базах...")
        await process_vin(message, vin_code)
    else:
        await message.answer("Не вдалося розпізнати VIN-код. Спробуйте ще раз або надішліть текстом.")
        await bot.send_photo(
            ADMINS_GROUP_ID,
            photo=photo.file_id,
            caption=f"❗ Не удалось распознать VIN з фото @{message.from_user.username or '-'} | ID: {message.from_user.id}"
        )
        await log_to_tg(bot, f"❗ Фото без VIN від користувача {message.from_user.id}")

@dp.message()
async def handle_user_message(message: types.Message):
    if message.text and message.text.startswith('/'):
        return
    if message.from_user.id not in user_name:
        await message.answer("Вкажіть, як до вас звертатись (введіть ім'я).")
        return
    text = message.text.strip() if message.text else ""
    is_vin = len(text) == 17 and all(c.isalnum() for c in text)

    if is_vin:
        await process_vin(message, text)
    else:
        answer = "Ваше повідомлення прийнято. Оператор зв'яжеться з вами найближчим часом."
        await message.answer(answer)
        user_info = (
            f"🔔 *Нова заявка від {user_name[message.from_user.id]}:*\n"
            f"👤 @{message.from_user.username or '-'} | ID: {message.from_user.id}\n"
            f"Текст:\n{text}\n"
        )
        await message.bot.send_message(ADMINS_GROUP_ID, user_info, parse_mode="Markdown")
        logger.info(f"Заявка від {message.from_user.id}: {text}")
        await log_to_tg(bot, f"Заявка від {message.from_user.id} (текст)")

async def process_vin(message, vin_code):
    responses = []
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
    logger.info(f"Відповідь користувачу {message.from_user.id} по VIN {vin_code}: {responses}")
    await log_to_tg(bot, f"🔍 Пробив по VIN {vin_code} для {message.from_user.id}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
