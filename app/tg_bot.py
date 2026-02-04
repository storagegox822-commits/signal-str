import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import sys
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

# Config
load_dotenv()
TOKEN = os.getenv("TG_TOKEN", "YOUR_TOKEN_HERE")
API_URL = "http://localhost:8000"

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "⚽ **Signalizer 3.5 Bot**\n\n"
        "Commands:\n"
        "/signals - Get top signals\n"
        "/backtest - View ROI stats\n"
        "/kelly - Kelly Criterion Calc\n"
        "/id - Get Chat ID",
        parse_mode="Markdown"
    )

@dp.message(Command("id"))
async def cmd_get_id(message: types.Message):
    """Получить свой Chat ID"""
    chat_id = message.chat.id
    await message.answer(f"🆔 **Ваш Chat ID:** `{chat_id}`\n\n"
                        f"📱 Username: @{message.from_user.username}\n"
                        f"👤 First name: {message.from_user.first_name}",
                        parse_mode="Markdown")

@dp.message(Command("signals"))
async def cmd_signals(message: types.Message):
    try:
        res = requests.get(f"{API_URL}/signals")
        signals = res.json()
        
        if not signals:
            await message.answer("No signals found. Run a scan on dashboard.")
            return

        response = "🔥 **Top Signals:**\n\n"
        for s in signals[:10]:
            response += f"🏆 {s['League']}\n⚽ {s['Home']} vs {s['Away']}\n📅 {s['Date']} | 📉 < 3.5 Opp\n\n"
        
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Error fetching signals: {e}")

@dp.message(Command("backtest"))
async def cmd_backtest(message: types.Message):
    try:
        res = requests.get(f"{API_URL}/backtest").json()
        text = "📈 **League Performance:**\n\n"
        for league, stats in res.items():
            text += f"**{league}**: ROI {stats['ROI']} | WR {stats['WinRate']}\n"
        await message.answer(text, parse_mode="Markdown")
    except:
        await message.answer("Error fetching backtest data.")

@dp.message(Command("kelly"))
async def cmd_kelly(message: types.Message):
    await message.answer(
        "To use Kelly Calc, send format:\n"
        "`kelly ODDS PROB BANKROLL`\n"
        "Example: `kelly 1.85 0.65 1000`",
        parse_mode="Markdown"
    )

@dp.message(lambda msg: msg.text.lower().startswith('kelly '))
async def process_kelly(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) != 4:
            raise ValueError
        
        odds = float(parts[1])
        prob = float(parts[2])
        bank = float(parts[3])
        
        payload = {"odds": odds, "win_prob": prob, "bankroll": bank}
        res = requests.post(f"{API_URL}/kelly", json=payload).json()
        
        await message.answer(
            f"💰 **Kelly Advice:**\n\n"
            f"Action: {res['action']}\n"
            f"Size: {res['amount']} ({res['fraction']*100:.1f}%)",
            parse_mode="Markdown"
        )
    except:
        await message.answer("Invalid format. Use: `kelly 1.85 0.65 1000`")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    if TOKEN == "YOUR_TOKEN_HERE":
        print("Error: TG_TOKEN not set in env vars.")
    else:
        asyncio.run(main())
