import os
from omega_api import vin_simple_search
from baza_gai_api import gai_vin_search
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TG_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

LANGUAGES = {
    "uk": "🇺🇦 Українська",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English"
}

@dp.message(CommandStart())
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text=LANGUAGES['uk'])
    kb.button(text=LANGUAGES['ru'])
    kb.button(text=LANGUAGES['en'])
    kb.adjust(3)
    await message.answer(
        "Вітаємо! Надішліть, будь ласка, ваш VIN-код текстом або фото техпаспорта (через скрепку 📎).\n\nОберіть мову:",
        reply_markup=kb.as_markup(resize_keyboard=True)
    )

@dp.message(F.text.in_([LANGUAGES['uk'], LANGUAGES['ru'], LANGUAGES['en']]))
async def choose_lang(message: types.Message):
    lang = [k for k, v in LANGUAGES.items() if v == message.text][0]
    # Сохраняем выбор пользователя — здесь можно добавить сохранение в БД/session
    await message.answer(f"Обрана мова: {LANGUAGES[lang]}. Продовжуємо...")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
