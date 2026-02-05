#!/usr/bin/env python3
"""
Under 3.5 Opponents (-3.5 Fav) Filter Checker для 5 лиг
Data: FBref + football-data.co.uk CSV
"""

import pandas as pd
import requests
import numpy as np
from datetime import datetime, timedelta
import os
from watchlist import is_watchlist_team, get_watchlist_info

# Set to True if you have a working proxy/VPN for FBref, otherwise use CSV (False)
USE_FBREF = False

# ========================================
# 5 ЛИГ + ОПТИМИЗИРОВАННЫЕ ФИЛЬТРЫ
# ========================================
FILTER_PROFILES = {
    "Primeira Liga": {
        "fbref_id": "POR-Primeira-Liga",
        "odds_key": "soccer_portugal_primeira_liga",
        "team_top": ["FC Porto", "SL Benfica", "Sporting CP"],
        "opp_last5_max": 5,
        "clean_last3_min": 2,
        "opp_avg_g_max": 1.1,
        "min_odds": 1.58
    },
    "Greek Super League": {
        "fbref_id": "GRE-Super-League",
        "odds_key": "soccer_greece_super_league",
        "team_top": ["PAOK FC", "Olympiacos FC", "AEK Athens"],
        "opp_last5_max": 4,
        "xg_opp_max": 0.9,
        "min_odds": 1.60
    },
    "La Liga 2": {
        "fbref_id": "ESP-Segunda",
        "odds_key": "soccer_spain_segunda_division",
        "team_top": ["Real Valladolid", "RCD Espanyol", "CD Leganes"],
        "opp_last5_max": 6,
        "btts_no_pct_min": 55,
        "home_winrate_min": 70,
        "min_odds": 1.58
    },
    "Eredivisie": {
        "fbref_id": "NED-Eredivisie",
        "odds_key": "soccer_netherlands_eredivisie",
        "team_top": ["PSV Eindhoven", "AFC Ajax", "Feyenoord"],
        "opp_last5_max": 7,
        "clean_sheets_pct_min": 50,
        "min_odds": 1.62
    },
    "Argentina Liga": {
        "fbref_id": "ARG-Primera",
        "odds_key": "soccer_argentina_primera_division",
        "team_top": ["River Plate", "Boca Juniors", "CA Independiente"],
        "opp_last5_max": 6,
        "clean_last4_min": 2,
        "min_odds": 1.60
    },
    # --- BIG 5 ADDITIONS ---
    "Premier League": {
        "fbref_id": "ENG-Premier League",
        "odds_key": "soccer_epl",
        "team_top": ["Manchester City", "Arsenal", "Liverpool", "Chelsea", "Manchester Utd"],
        "opp_last5_max": 8, # Looser filter for testing
        "clean_last3_min": 0,
        "min_odds": 1.20
    },
    "La Liga": {
        "fbref_id": "ESP-La Liga",
        "odds_key": "soccer_spain_la_liga",
        "team_top": ["Real Madrid", "Barcelona", "Atletico Madrid"],
        "opp_last5_max": 8,
        "clean_last3_min": 0,
        "min_odds": 1.20
    },
    "Serie A": {
        "fbref_id": "ITA-Serie A",
        "odds_key": "soccer_italy_serie_a",
        "team_top": ["Inter", "Juventus", "Milan", "Napoli"],
        "opp_last5_max": 8,
        "clean_last3_min": 0,
        "min_odds": 1.20
    },
    "Bundesliga": {
        "fbref_id": "GER-Bundesliga",
        "odds_key": "soccer_germany_bundesliga",
        "team_top": ["Bayern Munich", "Bayer Leverkusen", "Dortmund"],
        "opp_last5_max": 8,
        "clean_last3_min": 0,
        "min_odds": 1.20
    },
    "Ligue 1": {
        "fbref_id": "FRA-Ligue 1",
        "odds_key": "soccer_france_ligue_one",
        "team_top": ["Paris SG", "Monaco", "Marseille"],
        "opp_last5_max": 8,
        "clean_last3_min": 0,
        "min_odds": 1.20
    }
}

# ... [DATA LOADERS kept as is] ...

# ========================================
# ODDS ENGINE
# ========================================
from odds_api import OddsFetcher
odds_fetcher = OddsFetcher()

def get_real_odds(odds_key, home_team, away_team):
    """Finds odds in cache for fuzzy matched teams"""
    # Note: Team names in Odds API might differ from FBref/CSV.
    # Simple fuzzy match or exact match attempt.
    
    odds_data = odds_fetcher.get_odds(odds_key)
    if not odds_data:
        return 0.0
        
    # Logic to find match in odds_data dict (event_id -> {home, away, draw})
    # Since odds_api.py returns simplified dict, but we need team names.
    # Refactoring odds_api.py return format might be needed if we don't have team names in the cache dict keys.
    # Actually, odds_api.py _save_to_cache saves event_id. 
    # We need to query by team name. 
    
    # IMPROVED LOGIC: Re-implement simple match lookup here or in OddsModule.
    # For now, return placeholder if not found.
    return 0.0

# ========================================
# MAIN SCANNER
# ========================================
def scan_5leagues(days_ahead=7):
    """Скан матчей на N дней"""
    signals = []
    
    for name, config in FILTER_PROFILES.items():
        print(f"Scanning {name}...")
        
        # 0. Prefetch odds
        if 'odds_key' in config:
            odds_fetcher.get_odds(config['odds_key'])
        
        # 1. Try FBref first
        # ... (rest of logic)

# ========================================
# DATA LOADERS
# ========================================
def load_football_data_csv(league_code, season='2425'):
    """football-data.co.uk CSV"""
    base_url = f"https://www.football-data.co.uk/mmz4281/{season}"
    csv_map = {
        'Primeira Liga': 'P1', 
        'La Liga 2': 'SP2', 
        'Eredivisie': 'N1', 
        'Greek Super League': 'G1',
        'Premier League': 'E0',
        'La Liga': 'SP1',
        'Serie A': 'I1',
        'Bundesliga': 'D1',
        'Ligue 1': 'F1'
    } 
    # Note: Greek and Argentina may not have direct CSVs on football-data, handle gracefully
    
    if league_code in csv_map:
        url = f"{base_url}/{csv_map[league_code]}.csv"
        try:
            return pd.read_csv(url)
        except Exception as e:
            print(f"Error loading CSV for {league_code}: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def load_fbref_fixtures(league_id, season='2425'):
    """FBref via soccerdata"""
    try:
        import soccerdata as sd
        # Mute logging
        import logging
        logging.getLogger("soccerdata").setLevel(logging.WARNING)
        
        fbref = sd.FBref(leagues=[league_id], seasons=season)
        schedule = fbref.read_schedule()
        return schedule
    except ImportError as e:
        print(f"Soccerdata import failed: {e}")
        print("Install: pip install soccerdata")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading FBref for {league_id}: {e}")
        return pd.DataFrame()

# ========================================
# FILTER ENGINE
# ========================================
def calculate_team_stats(df, team_col='home_team'):
    """Precompute stats для фильтров"""
    # ... (rest of the function)
    return df

def apply_league_filters(row, profile, league_name):
    # ... (rest of the function)
    return True

# ========================================
# MAIN SCANNER
# ========================================
def scan_5leagues(days_ahead=7):
    """Скан матчей на N дней"""
    signals = []
    
    for name, config in FILTER_PROFILES.items():
        print(f"Scanning {name}...")
        
        # 1. Try FBref first (if enabled)
        fixtures = pd.DataFrame()
        if USE_FBREF:
            fixtures = load_fbref_fixtures(config['fbref_id'])
        
        # 2. Fallback to CSV if empty
        if fixtures.empty:
            if USE_FBREF:
                print(f"FBref empty for {name}, trying CSV...")
            fixtures = load_football_data_csv(name)
            
        # 3. Fallback to Odds API (The Ultimate Fallback)
        if fixtures.empty and 'odds_key' in config:
            print(f"CSV empty for {name}, trying Odds API...")
            odds_data = odds_fetcher.get_odds(config['odds_key'])
            if odds_data:
                # Normalize Odds API data to DataFrame
                # expected: date, home_team, away_team
                clean_data = []
                for m in odds_data:
                    clean_data.append({
                        'date': m['commence_time'],
                        'home_team': m['home_team'],
                        'away_team': m['away_team'],
                        'odds_h': m['h2h']['home'],
                        'odds_a': m['h2h']['away']
                    })
                fixtures = pd.DataFrame(clean_data)
                
                # Convert date to datetime (UTC by default from Odds API)
                fixtures['date'] = pd.to_datetime(fixtures['date'])
                
                # Check if timezone aware, if not assume UTC (Odds API returns ISO8601 with Z usually)
                if fixtures['date'].dt.tz is None:
                    fixtures['date'] = fixtures['date'].dt.tz_localize('UTC')
                
                # Convert to MSK (Europe/Moscow or UTC+3)
                # Since pytz might not be installed (though pandas usually has it), we can use fixed offset if needed
                # But let's try standard tz_convert with 'Europe/Moscow' or simple timedelta if relying on minimal env
                try:
                    fixtures['date'] = fixtures['date'].dt.tz_convert('Europe/Moscow').dt.tz_localize(None)
                except:
                    # Fallback manually to UTC+3
                    fixtures['date'] = fixtures['date'] + pd.Timedelta(hours=3)
                    fixtures['date'] = fixtures['date'].dt.tz_localize(None) # Make naive local

        if not fixtures.empty:
            # Normalize structure
            if 'date' not in fixtures.columns and 'Date' in fixtures.columns:
                fixtures['date'] = pd.to_datetime(fixtures['Date'], dayfirst=True, errors='coerce')
            elif 'date' in fixtures.columns and not pd.api.types.is_datetime64_any_dtype(fixtures['date']):
                fixtures['date'] = pd.to_datetime(fixtures['date'], dayfirst=True, errors='coerce')
            
            # Drop invalid dates
            fixtures = fixtures.dropna(subset=['date'])
            
            # Filter upcoming
            today = datetime.now()
            week = today + timedelta(days=days_ahead)
            
            mask = (fixtures['date'] >= today) & (fixtures['date'] <= week)
            upcoming = fixtures[mask]
            
            for _, match in upcoming.iterrows():
                if apply_league_filters(match, config, name):
                    date_str = match['date'].strftime('%Y-%m-%d %H:%M (MSK)')
                    home_team = match.get('home_team') or match.get('Home')
                    away_team = match.get('away_team') or match.get('Away')
                    
                    # Check watchlist
                    watchlist_badge = ""
                    if is_watchlist_team(home_team) or is_watchlist_team(away_team):
                        home_cat, home_badge = get_watchlist_info(home_team)
                        away_cat, away_badge = get_watchlist_info(away_team)
                        watchlist_badge = home_badge or away_badge or "👁️ W"
                    
                    signals.append({
                        'League': name,
                        'Date': date_str,
                        'Home': home_team,
                        'Away': away_team,
                        'Prediction': 'Under 3.5 Opponent Goals',
                        'Odds': config['min_odds'], # Placeholder
                        'Confidence': 'HIGH',
                        'Watchlist': watchlist_badge
                    })
    
    # If no strict signals, get popular matches
    if not signals:
        print("No strict signals found. Fetching popular matches...")
        for name, config in FILTER_PROFILES.items():
            if name not in ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]:
                continue
                
            try:
                # Reuse data loading logic
                fixtures = load_football_data_csv(name)
                if not fixtures.empty:
                    if 'date' not in fixtures.columns and 'Date' in fixtures.columns:
                        fixtures['date'] = pd.to_datetime(fixtures['Date'], dayfirst=True, errors='coerce')
                    elif 'date' in fixtures.columns:
                        fixtures['date'] = pd.to_datetime(fixtures['date'], dayfirst=True, errors='coerce')
                    
                    fixtures = fixtures.dropna(subset=['date'])
                    today = datetime.now()
                    upcoming = fixtures[(fixtures['date'] >= today) & (fixtures['date'] <= today + timedelta(days=days_ahead))]
                    
                    for idx, row in upcoming.iterrows():
                        home = row.get('HomeTeam') or row.get('Home')
                        away = row.get('AwayTeam') or row.get('Away')
                        
                        # Check if top team is playing
                        is_top_match = (home in config['team_top']) or (away in config['team_top'])
                        
                        if is_top_match:
                            signals.append({
                                'League': name,
                                'Date': row['date'].strftime('%Y-%m-%d %H:%M (MSK)'),
                                'Home': home,
                                'Away': away,
                                'Prediction': 'Popular Match',
                                'Odds': 0.0, # Placeholder
                                'Confidence': 'INFO'
                            })
            except Exception as e:
                print(f"Error fetching popular for {name}: {e}")

    if not signals:
        print("No signals found.")
        signals_df = pd.DataFrame(columns=['League', 'Date', 'Home', 'Away', 'Prediction', 'Odds', 'Confidence'])
    else:
        signals_df = pd.DataFrame(signals).sort_values('Date').head(10) # Limit to 10 popular
    
    output_file = 'under35_signals_5leagues.csv'
    signals_df.to_csv(output_file, index=False)
    print(f"✅ {len(signals_df)} signals saved to {output_file}!")
    return signals_df

# ========================================
# RUN
# ========================================
if __name__ == "__main__":
    signals = scan_5leagues(days_ahead=7)
    if not signals.empty:
        print(signals.head())
    print("\n📊 Scan complete.")
