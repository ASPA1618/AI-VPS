import json
from aiogram import types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# 1. Основной бот
MAIN_BOT_ID = 7717263680  # user_id бота (информационно)

# 2. Группа операторов/админов
ADMINS_GROUP_ID = -1002804535488  # для заявок и работы с клиентами

# 3. Лог-группа для логирования всех действий
LOG_CHAT_ID = -1002528385675      # только для технических логов

# Telegram ID всех админов, кто может управлять источниками через админку
ADMIN_IDS = [8102776356, 7717263680]  # добавь свои

CONFIG_PATH = "handlers/config.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

SOURCE_LABELS = {
    "gai": "База ДАІ",
    "omega": "Omega API",
    "ae": "AE Market"
}

router = Router()

def build_admin_keyboard(active_sources):
    kb = InlineKeyboardMarkup(row_width=1)
    for src, active in active_sources.items():
        label = SOURCE_LABELS.get(src, src.upper())
        status = "✅" if active else "❌"
        kb.add(InlineKeyboardButton(
            text=f"{status} {label}",
            callback_data=f"toggle_{src}"
        ))
    return kb

from aiogram.filters import Command

@router.message(Command("admin"))

async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔️ Нет доступа.")
        return
    config = load_config()
    kb = build_admin_keyboard(config['ACTIVE_SOURCES'])
    await message.answer("Панель управління джерелами:", reply_markup=kb)

@router.callback_query()
async def toggle_source(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("⛔️ Нет доступа.", show_alert=True)
        return
    src = call.data.replace("toggle_", "")
    config = load_config()
    if src not in config['ACTIVE_SOURCES']:
        await call.answer("⛔️ Джерело не знайдено.", show_alert=True)
        return

    config['ACTIVE_SOURCES'][src] = not config['ACTIVE_SOURCES'][src]
    save_config(config)
    label = SOURCE_LABELS.get(src, src.upper())
    status_text = "включено" if config['ACTIVE_SOURCES'][src] else "відключено"
    await call.answer(f"{label} {status_text}")

    admin_name = call.from_user.full_name
    log_message = (
        f"🛠️ *{admin_name}* ({call.from_user.id}) змінив статус джерела *{label}* на *{status_text}*."
    )
    await call.bot.send_message(LOG_CHAT_ID, log_message, parse_mode="Markdown")

    kb = build_admin_keyboard(config['ACTIVE_SOURCES'])
    try:
        await call.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        await call.message.answer("Панель оновлена.", reply_markup=kb)
