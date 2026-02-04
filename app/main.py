import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import json
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Signalizer 3.5 API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class MatchSignal(BaseModel):
    League: str
    Date: str
    Home: str
    Away: str
    Odds: float
    Confidence: str

class ScanRequest(BaseModel):
    days: int = 7

class AnalyzeRequest(BaseModel):
    matches: List[str]
    model: str = "gpt-3.5-turbo" # Default

class KellyRequest(BaseModel):
    odds: float
    win_prob: float
    bankroll: float

# ... (rest of code)

# --- Helpers ---
def translate_teams_batch(teams: List[str]) -> dict:
    """Translates a list of team names to Russian (Winline style) using LLM."""
    if not teams: return {}
    
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
        
        teams_txt = "\n".join(teams)
        prompt = f"""
        Переведи названия этих футбольных команд на РУССКИЙ язык.
        Используй транскрипцию, принятую в БК Winline.
        
        ВАЖНО:
        1. НЕ ОСТАВЛЯЙ АНГЛИЙСКИХ НАЗВАНИЙ. Все должно быть кириллицей.
        2. Если название редкое - просто транслитерируй (Racing -> Расинг).
        
        СПИСОК:
        {teams_txt}
        
        ФОРМАТ ОТВЕТА (JSON):
        {{
            "Original Name": "Russian Name",
            ...
        }}
        Только валидный JSON.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a translator helper. Output strictly JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Translation Error: {e}")
        return {t: t for t in teams} # Fallback to original

def load_signals():
    csv_file = "under35_signals_5leagues.csv"
    ru_csv_file = "under35_signals_5leagues_ru.csv"
    
    try:
        if not os.path.exists(csv_file):
            return []
            
        # Check Cache Validity
        use_cache = False
        if os.path.exists(ru_csv_file):
            # If RU file is newer than or same age as Source
            if os.path.getmtime(ru_csv_file) >= os.path.getmtime(csv_file):
                use_cache = True
        
        if use_cache:
            try:
                return pd.read_csv(ru_csv_file).to_dict(orient="records")
            except:
                pass # Cache corrupted? Proceed to regenerate
        
        # --- GENERATE TRANSLATION ---
        df = pd.read_csv(csv_file)
        if df.empty: return []
        
        # 1. Get Unique Teams
        teams = pd.concat([df['Home'], df['Away']]).unique().tolist()
        
        # 2. Translate
        print(f"Translating {len(teams)} teams for signals cache...")
        trans_map = translate_teams_batch(teams)
        
        # 3. Apply
        # Handle JSON returning slightly different keys or missing keys gracefully
        # Normalize map slightly?
        
        df['Home'] = df['Home'].map(lambda x: trans_map.get(x, x))
        df['Away'] = df['Away'].map(lambda x: trans_map.get(x, x))
        
        # 4. Save Cache
        df.to_csv(ru_csv_file, index=False)
        
        return df.to_dict(orient="records")
        
    except Exception as e:
        print(f"Load Signals Error: {e}")
        return []

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "active", "system": "Signalizer 3.5"}

@app.post("/scan/{days}")
def run_scan(days: int):
    """Trigger the external scanner script"""
    try:
        # Calling the script as a subprocess ensures isolation
        result = subprocess.run(
            [sys.executable, "under35_scanner.py"], 
            capture_output=True, text=True
        )
        if result.returncode == 0:
            signals = load_signals()
            return {"status": "success", "found": len(signals), "log": result.stdout}
        else:
            raise HTTPException(status_code=500, detail=result.stderr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signals")
def get_signals():
    """Get current signals"""
    return load_signals()

@app.get("/backtest")
def get_backtest():
    """Mock backtest data"""
    return {
        "Primeira Liga": {"ROI": "6.2%", "WinRate": "68%"},
        "Greek Super League": {"ROI": "4.1%", "WinRate": "62%"},
        "La Liga 2": {"ROI": "5.5%", "WinRate": "65%"},
        "Eredivisie": {"ROI": "3.8%", "WinRate": "60%"},
        "Argentina Liga": {"ROI": "7.0%", "WinRate": "72%"}
    }

@app.post("/analyze_express")
def analyze_express(req: AnalyzeRequest):
    """
    AI Analysis using OpenAI/Perplexity.
    Uses keys from .env
    """
    matches_text = "\n".join(req.matches)
    
    # Enhanced prompt in Russian
    prompt = f"""
🤖 АНАЛИЗ МАТЧЕЙ (ТМ 3.5)

📋 МАТЧИ:
{matches_text}

📊 ЗАДАЧА: Для КАЖДОГО матча дай прогноз с эмодзи:
1. 📅 ДАТА и Время (МСК).
2. ТРИ (3) точных счета.
3. Вероятность ТМ 3.5.
4. Уверенность.
5. Причина (Краткий сценарий матча).

⚠️ ВАЖНО: Названия команд пиши СТРОГО НА РУССКОМ языке (транслитерация Winline).
Пример: "Racing Club" -> "Расинг Клаб".

📈 ФОРМАТ (Строго, используй переносы строк!):
⚽ Расинг Клаб vs Бока Хуниорс (ПЕРЕВЕДИ НАЗВАНИЯ!)
📅 ДАТА: 23.10 19:00 МСК

🎯 СЧЕТА:
💎 1:1 (40%)
🔹 2:0 (30%)
🔹 3:0 (15%)

📉 ТМ 3.5: 82%
🛡️ УВЕРЕННОСТЬ: 8/10
📝 ПРИЧИНА: Гости фавориты, хозяева мало забивают, ожидается вязкая игра.

⚠️ ВАЖНО:
- УДАЛЯЙ любые ссылки на источники типа [1][2].
- Используй пустую строку между матчами.
- Придерживайся стиля с эмодзи.
    """
    
    try:
        from openai import OpenAI
        
        # Select provider based on model choice
        if "Perplexity" in req.model or "Sonar" in req.model:
            api_key = os.getenv("PERPLEXITY_API_KEY")
            base_url = "https://api.perplexity.ai"
            model_id = "sonar" # Defaulting to 'sonar' (prev. sonar-medium-online or similar)
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = None
            model_id = "gpt-4o-mini" # User requested this as backup
            
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "Ты профессиональный спортивный аналитик, специализирующийся на футбольной статистике."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1 # Deterministic
        )
        
        analysis = response.choices[0].message.content
        return {
            "analysis": analysis,
            "recommendation": "Analysis generated by " + model_id
        }
    except Exception as e:
        return {
            "analysis": f"AI Analysis Error: {str(e)}",
            "recommendation": "Please check API keys."
        }

@app.post("/kelly")
def calculate_kelly(req: KellyRequest):
    """
    f* = (bp - q) / b
    b = odds - 1
    p = win_prob
    q = 1 - p
    """
    b = req.odds - 1
    p = req.win_prob
    q = 1 - p
    
    f_star = (b * p - q) / b
    
    if f_star < 0:
        return {"action": "Do not bet", "fraction": 0, "amount": 0}
    
    amount = req.bankroll * f_star
    return {
        "action": "Bet",
        "fraction": round(f_star, 4),
        "amount": round(amount, 2)
    }

class NotifyRequest(BaseModel):
    message: str

# ... existing imports ...
from datetime import datetime

# History Data Model
class HistoryItem(BaseModel):
    date: str
    matches: list[str]
    outcomes: dict  # {m1: [o1,o2,o3], ...}
    odds: dict # {m1: [1.5, ...], ...}
    variations_count: int
    roi_calculation: str
    timestamp: float

HISTORY_FILE = "data/history.json"

@app.post("/save_history")
def save_history(item: HistoryItem):
    try:
        history = []
        if os.path.exists(HISTORY_FILE):
             with open(HISTORY_FILE, "r") as f:
                 history = json.load(f)
        
        history.append(item.dict())
        
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
            
        return {"status": "saved", "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DeleteHistoryRequest(BaseModel):
    timestamp: float = None
    delete_all: bool = False

@app.post("/delete_history")
def delete_history(req: DeleteHistoryRequest):
    try:
        if not os.path.exists(HISTORY_FILE):
             return {"status": "empty"}
             
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
            
        if req.delete_all:
            history = []
        elif req.timestamp:
            # Filter out the item with matching timestamp
            history = [h for h in history if h.get("timestamp") != req.timestamp]
            
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
            
        return {"status": "deleted", "remaining": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_history")
def get_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

@app.post("/notify_telegram")
def notify_telegram(req: NotifyRequest):
    """
    Send a message to the Telegram Bot.
    Uses 'TG_BOT_TOKEN' and 'TG_CHAT_ID' (optional default) or just sends updates.
    """
    token = os.getenv("TG_BOT_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID", "194014207") # Default from memory
    
    if not token:
         raise HTTPException(status_code=500, detail="TG_BOT_TOKEN not set")
         
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": req.message}
    
    try:
        import requests
        res = requests.post(url, json=payload)
        if res.status_code != 200:
             raise HTTPException(status_code=res.status_code, detail=res.text)
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
