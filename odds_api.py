import os
import sqlite3
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4/sports"
CACHE_FILE = "odds_cache.db"
CACHE_DURATION = 3600 * 6  # 6 hours cache

class OddsFetcher:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(CACHE_FILE)
        c = conn.cursor()
        # Dropping table to force schema update for new fields
        c.execute("DROP TABLE IF EXISTS odds_cache")
        c.execute('''CREATE TABLE IF NOT EXISTS odds_cache
                     (sport_key TEXT, event_id TEXT, home_team TEXT, away_team TEXT, commence_time TEXT, 
                      h2h_home REAL, h2h_away REAL, h2h_draw REAL, last_updated INTEGER, UNIQUE(sport_key, event_id))''')
        conn.commit()
        conn.close()

    def _get_from_cache(self, sport_key):
        conn = sqlite3.connect(CACHE_FILE)
        c = conn.cursor()
        # Clean old cache
        expiry = int(time.time()) - CACHE_DURATION
        c.execute("DELETE FROM odds_cache WHERE last_updated < ?", (expiry,))
        conn.commit()
        
        c.execute("SELECT event_id, home_team, away_team, commence_time, h2h_home, h2h_away, h2h_draw FROM odds_cache WHERE sport_key=?", (sport_key,))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return None
            
        data = []
        for r in rows:
            data.append({
                "id": r[0],
                "home_team": r[1],
                "away_team": r[2],
                "commence_time": r[3],
                "h2h": {"home": r[4], "away": r[5], "draw": r[6]}
            })
        return data

    def _save_to_cache(self, sport_key, data):
        conn = sqlite3.connect(CACHE_FILE)
        c = conn.cursor()
        now = int(time.time())
        
        for event in data:
            event_id = event['id']
            home = event['home_team']
            away = event['away_team']
            start = event['commence_time']
            
            # Extract H2H odds (avg or first bookie)
            h2h = [0.0, 0.0, 0.0] # Home, Away, Draw
            
            # Simple extractor - take the first bookmaker 'pinnacle' or just first available
            for bookie in event.get('bookmakers', []):
                for market in bookie.get('markets', []):
                    if market['key'] == 'h2h':
                        # Assuming outcomes are [Home, Away] or [Home, Away, Draw]
                        outcomes = {o['name']: o['price'] for o in market['outcomes']}
                        h2h[0] = outcomes.get(home, 0.0)
                        h2h[1] = outcomes.get(away, 0.0)
                        # Draw logic is tricky as name is usually 'Draw'
                        h2h[2] = outcomes.get('Draw', 0.0)
                        break
                if h2h[0]: break # Found odds from one bookie
            
            c.execute('''INSERT OR REPLACE INTO odds_cache 
                         (sport_key, event_id, home_team, away_team, commence_time, h2h_home, h2h_away, h2h_draw, last_updated)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                         (sport_key, event_id, home, away, start, h2h[0], h2h[1], h2h[2], now))
        conn.commit()
        conn.close()

    def get_odds(self, sport_key, regions='eu', markets='h2h'):
        """
        Get odds for a league. Checks cache first.
        Supports Key Rotation (comma separated in env).
        """
        cached = self._get_from_cache(sport_key)
        if cached:
            print(f"  [Odds] Using cached data for {sport_key}")
            return cached

        # Parse Keys (Comma separated)
        env_keys = os.getenv("ODDS_API_KEY", "").split(",")
        api_keys = [k.strip() for k in env_keys if k.strip()]
        
        if not api_keys:
            print("  [Odds] No API Keys found!")
            return {}

        print(f"  [Odds] Fetching fresh data for {sport_key}...")
        
        for i, key in enumerate(api_keys):
            print(f"  [Odds] Trying Key #{i+1}...")
            url = f"{BASE_URL}/{sport_key}/odds/?apiKey={key}&regions={regions}&markets={markets}"
            
            try:
                res = requests.get(url)
                if res.status_code == 200:
                    data = res.json()
                    self._save_to_cache(sport_key, data)
                    
                    remaining = res.headers.get('x-requests-remaining')
                    print(f"  [Odds] API Success (Key #{i+1}). Quota remaining: {remaining}")
                    
                    return self._get_from_cache(sport_key)
                
                elif res.status_code in [401, 429]:
                    print(f"  [Odds] Key #{i+1} Failed ({res.status_code}). Switching to next...")
                    continue # Try next key
                
                else:
                    print(f"  [Odds] API Error: {res.status_code} {res.text}")
                    return [] # Non-auth error, likely bad request, dont retry
                    
            except Exception as e:
                print(f"  [Odds] Request failed: {e}")
                return {}
        
        print("  [Odds] All API Keys exhausted.")
        return {}
