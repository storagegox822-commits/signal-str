import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from dotenv import load_dotenv

# Internal Imports
# Ensure we can import from app.main when running from root
import sys
sys.path.append(os.getcwd())

try:
    from app.main import load_signals, get_backtest
except ImportError:
    # Fallback if running from inside app/ or issues with path
    sys.path.append(os.path.join(os.getcwd(), '..'))
    from app.main import load_signals, get_backtest

# Configure logging
logging.basicConfig(level=logging.INFO)

# Config
load_dotenv()
TOKEN = os.getenv("TG_TOKEN") or os.getenv("TG_BOT_TOKEN")

# Initialize bot and dispatcher
if not TOKEN:
    print("Error: TG_TOKEN or TG_BOT_TOKEN not set in env vars.")
    sys.exit(1)

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
    username = message.from_user.username or "NoUsername"
    await message.answer(f"🆔 **Ваш Chat ID:** `{chat_id}`\n\n"
                        f"📱 Username: @{username}\n"
                        f"👤 First name: {message.from_user.first_name}",
                        parse_mode="Markdown")

@dp.message(Command("signals"))
async def cmd_signals(message: types.Message):
    try:
        # Direct call to backend logic
        signals = load_signals()
        
        if not signals:
            await message.answer("No signals found. Use Dashboard to Run Scan.")
            return

        response = "🔥 **Top Signals:**\n\n"
        # Sort by Confidence if available, else take top
        # Assuming load_signals returns list of dicts
        
        # Simple Sort by Confidence if key exists
        try:
             signals.sort(key=lambda x: float(x.get('Confidence', 0)), reverse=True)
        except: pass

        for s in signals[:10]:
            conf = s.get('Confidence', 'N/A')
            response += f"🏆 {s['League']}\n⚽ {s['Home']} vs {s['Away']}\n📅 {s['Date']} | 📉 < 3.5 Opp | 🛡 {conf}\n\n"
        
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Signal Error: {e}")
        await message.answer(f"Error fetching signals: {e}")

@dp.message(Command("backtest"))
async def cmd_backtest(message: types.Message):
    try:
        # Direct call
        res = get_backtest()
        text = "📈 **League Performance:**\n\n"
        for league, stats in res.items():
            text += f"**{league}**: ROI {stats['ROI']} | WR {stats['WinRate']}\n"
        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Backtest Error: {e}")
        await message.answer("Error fetching backtest data.")

@dp.message(Command("kelly"))
async def cmd_kelly(message: types.Message):
    await message.answer(
        "To use Kelly Calc, send format:\n"
        "`kelly ODDS PROB BANKROLL`\n"
        "Example: `kelly 1.85 0.65 1000`",
        parse_mode="Markdown"
    )

@dp.message(lambda msg: msg.text and msg.text.lower().startswith('kelly '))
async def process_kelly(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) != 4:
            raise ValueError
        
        odds = float(parts[1])
        prob = float(parts[2])
        bank = float(parts[3])
        
        # Kelly Logic
        b = odds - 1
        q = 1 - prob
        f_star = (b * prob - q) / b
        
        if f_star < 0:
            action = "Do not bet"
            amount = 0
            fraction = 0
        else:
            action = "Bet"
            fraction = f_star
            amount = bank * f_star
        
        await message.answer(
            f"💰 **Kelly Advice:**\n\n"
            f"Action: {action}\n"
            f"Size: {amount:.2f} ({fraction*100:.1f}%)",
            parse_mode="Markdown"
        )
    except:
        await message.answer("Invalid format. Use: `kelly 1.85 0.65 1000`")

async def main():
    print("🤖 Bot started! Polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if not TOKEN:
        print("Error: TG_TOKEN or TG_BOT_TOKEN not set.")
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("Bot stopped")
