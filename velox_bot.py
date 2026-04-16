import asyncio
import requests
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- НАСТРОЙКИ ---
TOKEN = "8754801899:AAGlSEFw46qJJM9EiLTWOHka7sTrk0yVwRo"
BASE_DB_URL = "https://nexus-app-6769e-default-rtdb.europe-west1.firebasedatabase.app/nodes"

# ВСТАВЬ СЮДА ТОКЕН (из VeloxSecurity или из логов майнера), чтобы бот мог читать закрытую базу
DB_AUTH_TOKEN = "ТВОЙ_АВТОРИЗАЦИОННЫЙ_ТОКЕН" 

bot = Bot(token=TOKEN)
dp = Dispatcher()

session = requests.Session()
session.trust_env = False 

# Хранилище привязанных ID
user_node_link = {}

async def get_report_text(node_id, data):
    """Формирует отчет в формате HTML, используя актуальные ключи из базы"""
    if not data:
        return "⚠️ Данные узла пусты."

    # Берем ключи mb_total и vlx_earned (как в майнере)
    mb = data.get('mb_total', 0)
    vlx = data.get('vlx_earned', 0)
    
    # Статус, кошелек и версия
    status_raw = str(data.get('status', 'offline')).upper()
    wallet = data.get('wallet', 'Не указан')
    version = data.get('version', '1.5.0')
    
    color = "🟢" if status_raw == "ONLINE" else "🔴"
    
    return (
        f"📊 <b>ОТЧЕТ ПО УЗЛУ: {node_id}</b>\n"
        f"🆔 <b>VELOX_ID:</b> <code>{node_id}</code>\n"
        f"----------------------------------\n"
        f"📡 Трафик: <code>{mb} MB</code>\n"
        f"💰 Заработано: <code>{vlx} VLX</code>\n"
        f"{color} Статус: <b>{status_raw}</b>\n"
        f"📦 Версия: <code>{version}</code>\n"
        f"----------------------------------\n"
        f"👛 Кошелек: <code>{wallet}</code>"
    )

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🚀 <b>VELOX DePIN Network Monitor</b>\n\n"
        "Пришли мне свой <b>VELOX_ID</b>, чтобы привязать узел.\n\n"
        "• /status — проверить узел\n"
        "• /help — помощь",
        parse_mode="HTML"
    )

@dp.message(Command("status"))
async def status_quick(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_node_link:
        await message.answer("⚠️ Сначала пришлите ваш <b>VELOX_ID</b>.")
        return

    node_id = user_node_link[user_id]
    msg = await message.answer(f"🔍 Запрашиваю данные <code>{node_id}</code>...")
    
    try:
        # Добавляем авторизацию в запрос бота
        url = f"{BASE_DB_URL}/{node_id}.json"
        params = {"auth": DB_AUTH_TOKEN}
        response = session.get(url, params=params, timeout=10)
        data = response.json()
        
        if data and isinstance(data, dict):
            report = await get_report_text(node_id, data)
            await msg.edit_text(report, parse_mode="HTML")
        else:
            await msg.edit_text(f"❌ Узел <b>{node_id}</b> не найден.")
    except Exception as e:
        logging.error(f"Error: {e}")
        await msg.edit_text("⚠️ Ошибка связи с базой.")

@dp.message()
async def handle_node_input(message: types.Message):
    node_id = message.text.strip()
    if not node_id.startswith("VELOX_"):
        return

    msg = await message.answer("🔎 Проверка в базе...")
    
    try:
        url = f"{BASE_DB_URL}/{node_id}.json"
        params = {"auth": DB_AUTH_TOKEN}
        response = session.get(url, params=params, timeout=10)
        data = response.json()
        
        if data and isinstance(data, dict):
            user_node_link[message.from_user.id] = node_id
            report = await get_report_text(node_id, data)
            await msg.edit_text(f"✅ Узел привязан!\n\n{report}", parse_mode="HTML")
        else:
            await msg.edit_text(f"❌ Узел <b>{node_id}</b> не найден в базе.")
    except Exception as e:
        await msg.edit_text("⚠️ Ошибка при поиске.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())