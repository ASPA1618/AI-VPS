import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv
from loguru import logger

from handlers.admin import router as admin_router
from ocr_utils import extract_vin_from_image
from carquery_api import get_brands, get_models, get_years, get_engines

from users_storage import load_users, set_user_field, get_user_field

users = load_users()  # {telegram_id: {"lang": ..., "name": ..., ...}}

MAIN_BOT_ID = 7717263680
ADMINS_GROUP_ID = -1002804535488
LOG_CHAT_ID = -1002528385675
ADMIN_IDS = [8102776356]

load_dotenv()
TOKEN = os.getenv("BOT_TG_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(admin_router)
logger.add("bot.log", rotation="10 MB", compression="zip", enqueue=True)

async def log_to_tg(bot, message):
    try:
        await bot.send_message(LOG_CHAT_ID, message)
    except Exception as e:
        logger.error(f"Ошибка при отправке лога в Telegram: {e}")

LANGUAGES = {
    "uk": ("🇺🇦 Українська", "uk"),
    "ru": ("🇷🇺 Русский", "ru"),
    "en": ("🇬🇧 English", "en")
}

# --- Приветственные сообщения на всех языках
WELCOME_MSG = {
    "uk": "👋 Вітаємо в *ASPA-боті*!\n\n🚗 Тут ви зможете підібрати автозапчастини за VIN-кодом, фото техпаспорта або вручну по марці та моделі авто.\n⚡ Просто натисніть потрібну мову нижче 👇",
    "ru": "👋 Добро пожаловать в *ASPA-бот*!\n\n🚗 Здесь вы сможете подобрать автозапчасти по VIN-коду, фото техпаспорта или вручную по марке и модели авто.\n⚡ Просто выберите нужный язык ниже 👇",
    "en": "👋 Welcome to *ASPA-bot*!\n\n🚗 Here you can select auto parts by VIN code, registration certificate photo, or manually by brand and model.\n⚡ Just choose your language below 👇"
}

def get_welcome_text(lang):
    return WELCOME_MSG.get(lang, WELCOME_MSG["uk"])

def get_choose_name(username, user_id, lang):
    if lang == "ru":
        return f"📝 Как к вам обращаться?\n(например, @{username} или {user_id})"
    if lang == "en":
        return f"📝 How should we address you?\n(e.g., @{username} or {user_id})"
    return f"📝 Як до вас звертатись?\n(наприклад, @{username} або {user_id})"

@dp.message(CommandStart())
async def start(message: types.Message):
    lang = get_user_field(users, message.from_user.id, "lang")
    if lang:
        name = get_user_field(users, message.from_user.id, "name") or message.from_user.id
        await message.answer(
            f"👋 Знову вітаємо, {name}!\nОбрана мова: {LANGUAGES[lang][0]}\nНадішліть VIN або фото техпаспорта."
        )
        await message.answer(
            "🔍 Або скористайтесь кнопкою ручного підбору авто:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔍 Вибрати авто вручну")]],
                resize_keyboard=True
            )
        )
    else:
        kb = ReplyKeyboardBuilder()
        for code, (title, _) in LANGUAGES.items():
            kb.button(text=title)
        kb.adjust(3)
        await message.answer(
            get_welcome_text("uk"),
            reply_markup=kb.as_markup(resize_keyboard=True)
        )
        logger.info(f"User {message.from_user.id} started bot.")
        await log_to_tg(bot, f"🟢 Користувач {message.from_user.id} стартував бота.")

@dp.message(F.text.in_([v[0] for v in LANGUAGES.values()]))
async def choose_lang(message: types.Message):
    lang_code = [k for k, v in LANGUAGES.items() if v[0] == message.text][0]
    set_user_field(users, message.from_user.id, "lang", lang_code)
    await message.answer(
        get_choose_name(message.from_user.username, message.from_user.id, lang_code)
    )
    logger.info(f"User {message.from_user.id} chose language: {lang_code}")

@dp.message(lambda message: not get_user_field(users, message.from_user.id, "name") and not message.text.startswith('/'))
async def set_name(message: types.Message):
    name = message.text.strip()
    set_user_field(users, message.from_user.id, "name", name)
    lang = get_user_field(users, message.from_user.id, "lang", "uk")
    await message.answer(
        {
            "uk": f"Дякуємо, {name}! Тепер надішліть VIN-код або фото техпаспорта.\nЯкщо VIN-код невідомий — оберіть ручний підбір авто кнопкою нижче.",
            "ru": f"Спасибо, {name}! Теперь отправьте VIN-код или фото техпаспорта.\nЕсли VIN-код неизвестен — используйте ручной подбор авто кнопкой ниже.",
            "en": f"Thank you, {name}! Now send the VIN or registration certificate photo.\nIf VIN is unknown — use the manual selection button below."
        }[lang],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔍 Вибрати авто вручну")]],
            resize_keyboard=True
        )
    )
    logger.info(f"User {message.from_user.id} set name: {name}")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    if not get_user_field(users, message.from_user.id, "name"):
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
    lang = get_user_field(users, message.from_user.id, "lang", "uk")
    if vin_code:
        await message.answer(
            {
                "uk": f"Розпізнано VIN: {vin_code}\nПеревіряємо по базах...",
                "ru": f"VIN распознан: {vin_code}\nПроверяем по базам...",
                "en": f"VIN recognized: {vin_code}\nChecking databases..."
            }[lang]
        )
        await process_vin(message, vin_code)
    else:
        await message.answer(
            {
                "uk": "❗ Не вдалося розпізнати VIN-код. Ви можете спробувати ще раз, надіслати текстом, або вибрати авто вручну.",
                "ru": "❗ Не удалось распознать VIN-код. Можете попробовать ещё раз, отправить текстом или выбрать авто вручную.",
                "en": "❗ Failed to recognize VIN. Try again, send as text, or select your car manually."
            }[lang],
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔍 Вибрати авто вручну")]],
                resize_keyboard=True
            )
        )
        await bot.send_photo(
            ADMINS_GROUP_ID,
            photo=photo.file_id,
            caption=f"❗ Не удалось распознать VIN з фото @{message.from_user.username or '-'} | ID: {message.from_user.id}"
        )
        await log_to_tg(bot, f"❗ Фото без VIN від користувача {message.from_user.id}")

@dp.message(lambda message: message.text == "🔍 Вибрати авто вручну")
async def manual_car_select(message: types.Message):
    brands = get_brands()
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for b in brands[:20]:
        kb.add(KeyboardButton(text=b))
    await message.answer("🚗 Оберіть марку авто:", reply_markup=kb)
    set_user_field(users, message.from_user.id, "car_selection", {})

@dp.message(lambda msg: get_user_field(users, msg.from_user.id, "car_selection", {}) != {} and not get_user_field(users, msg.from_user.id, "car_selection", {}).get("brand"))
async def manual_car_brand(message: types.Message):
    brand = message.text
    models = get_models(brand)
    car_sel = get_user_field(users, message.from_user.id, "car_selection", {})
    car_sel["brand"] = brand
    set_user_field(users, message.from_user.id, "car_selection", car_sel)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for m in models[:20]:
        kb.add(KeyboardButton(text=m))
    await message.answer(f"🚗 Обрана марка: {brand}\n\nОберіть модель:", reply_markup=kb)

@dp.message(lambda msg: get_user_field(users, msg.from_user.id, "car_selection", {}).get("brand") and not get_user_field(users, msg.from_user.id, "car_selection", {}).get("model"))
async def manual_car_model(message: types.Message):
    model = message.text
    car_sel = get_user_field(users, message.from_user.id, "car_selection", {})
    brand = car_sel["brand"]
    years = get_years(brand, model)
    car_sel["model"] = model
    set_user_field(users, message.from_user.id, "car_selection", car_sel)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for y in years:
        kb.add(KeyboardButton(text=str(y)))
    await message.answer(f"🚗 Обрана модель: {model}\n\nОберіть рік випуску:", reply_markup=kb)

@dp.message(lambda msg: get_user_field(users, msg.from_user.id, "car_selection", {}).get("model") and not get_user_field(users, msg.from_user.id, "car_selection", {}).get("year"))
async def manual_car_year(message: types.Message):
    year = message.text
    car_sel = get_user_field(users, message.from_user.id, "car_selection", {})
    brand = car_sel["brand"]
    model = car_sel["model"]
    engines = get_engines(brand, model, year)
    car_sel["year"] = year
    set_user_field(users, message.from_user.id, "car_selection", car_sel)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for eng in engines:
        name = f"{eng['desc']} | {eng['engine_type']} {eng['engine_cc']}см³ {eng['power_hp']}к.с."
        kb.add(KeyboardButton(text=name))
    await message.answer(
        f"🚗 Обрано: {brand} {model} {year}\n\nОберіть двигун:", 
        reply_markup=kb
    )

@dp.message(lambda msg: get_user_field(users, msg.from_user.id, "car_selection", {}).get("year") and not get_user_field(users, msg.from_user.id, "car_selection", {}).get("engine"))
async def manual_car_engine(message: types.Message):
    engine = message.text
    car_sel = get_user_field(users, message.from_user.id, "car_selection", {})
    car_sel["engine"] = engine
    set_user_field(users, message.from_user.id, "car_selection", car_sel)
    await message.answer(
        f"✅ Ваш авто: {car_sel['brand']} {car_sel['model']} {car_sel['year']}\n"
        f"Двигун: {engine}\n\nТепер можете підібрати товари або залишити заявку оператору.",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True)
    )

@dp.message()
async def handle_user_message(message: types.Message):
    if message.text and message.text.startswith('/'):
        return
    if not get_user_field(users, message.from_user.id, "name"):
        await message.answer("Вкажіть, як до вас звертатись (введіть ім'я).")
        return
    text = message.text.strip() if message.text else ""
    is_vin = len(text) == 17 and all(c.isalnum() for c in text)
    lang = get_user_field(users, message.from_user.id, "lang", "uk")

    if is_vin:
        await process_vin(message, text)
    else:
        answer = {
            "uk": "Ваше повідомлення прийнято. Оператор зв'яжеться з вами найближчим часом.\nАбо скористайтесь кнопкою ручного підбору авто:",
            "ru": "Ваше сообщение принято. Оператор свяжется с вами в ближайшее время.\nИли воспользуйтесь кнопкой ручного подбора авто:",
            "en": "Your request has been received. The operator will contact you soon.\nOr use the manual car selection button:"
        }[lang]
        await message.answer(
            answer,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔍 Вибрати авто вручну")]],
                resize_keyboard=True
            )
        )
        name = get_user_field(users, message.from_user.id, "name", message.from_user.id)
        user_info = (
            f"🔔 *Нова заявка від {name}:*\n"
            f"👤 @{message.from_user.username or '-'} | ID: {message.from_user.id}\n"
            f"Текст:\n{text}\n"
        )
        await message.bot.send_message(ADMINS_GROUP_ID, user_info, parse_mode="Markdown")
        logger.info(f"Заявка від {message.from_user.id}: {text}")
        await log_to_tg(bot, f"Заявка від {message.from_user.id} (текст)")

async def process_vin(message, vin_code):
    # ... (оставь свою текущую логику, просто добавь работу с lang как выше)
    pass  # Не стал переписывать — просто используй lang для сообщений, как в примерах выше

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
