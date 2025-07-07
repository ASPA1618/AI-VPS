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

MAIN_BOT_ID = 7717263680  # user_id бота (только для информации)
ADMINS_GROUP_ID = -1002804535488  # ID группы операторов/админов
LOG_CHAT_ID = -1002528385675      # ID группы для логов

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
    await message.answer(f"Обрана мова: {LANGUAGES[lang]}. Продовжуємо...")

@dp.message()
async def handle_user_message(message: types.Message):
    text = message.text.strip() if message.text else ""
    is_vin = len(text) == 17 and all(c.isalnum() for c in text)

    if is_vin:
        responses = []

        gai_info = gai_vin_search(text)
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

        omega_info = vin_simple_search(text)
        if omega_info:
            brand = omega_info.get("brand") or omega_info.get("mark") or ""
            model = omega_info.get("model", "")
            if brand or model:
                responses.append(f"Omega:\nМарка: {brand}\nМодель: {model}")
            else:
                responses.append("Omega: Даних мало.")
        else:
            responses.append("Omega: Немає даних.")

        await message.answer('\n\n'.join(responses))
    else:
        # Это не VIN — отправляем заявку в группу операторов!
        await message.answer("Ваше повідомлення прийнято. Оператор зв'яжеться з вами найближчим часом.")

        user_info = (
            f"🔔 *Нова заявка від користувача:*\n"
            f"👤 @{message.from_user.username or '-'} | ID: {message.from_user.id}\n"
            f"Текст:\n{text}\n"
        )
        # Отправляем именно в группу операторов (ADMINS_GROUP_ID)
        await message.bot.send_message(ADMINS_GROUP_ID, user_info, parse_mode="Markdown")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
