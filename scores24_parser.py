
import time
from datetime import datetime
import pandas as pd
import random

def parse_scores24_selenium(url, date_filter="Today"):
    """
    Mock parser for Scores24 due to Cloudflare protection.
    Returns simulated Under 2.5/3.5 matches for testing UI flow.
    """
    print(f"Mocking Selenium parser for {url} with filter {date_filter}...")
    time.sleep(1) # Simulate network delay
    
    matches = []
    
    # Generate mock matches based on URL type
    is_u25 = "under-2-5" in url
    label = "U2.5" if is_u25 else "U3.5"
    
    # Teams (Expanded list)
    teams_pool = [
        ("Chelsea", "Arsenal"),
        ("Man City", "Liverpool"),
        ("Real Madrid", "Barcelona"),
        ("Juventus", "Milan"),
        ("Bayer Leverkusen", "Bayern Munich"),
        ("PSG", "Marseille"),
        ("Ajax", "Feyenoord"),
        ("Porto", "Benfica")
    ]
    
    # Determine date
    if date_filter.lower() == "tomorrow":
        target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        # Shift teams for variety
        teams = teams_pool[4:] 
    else: # Today
        target_date = datetime.now().strftime("%Y-%m-%d")
        teams = teams_pool[:4]
    
    for i, (home, away) in enumerate(teams):
        # Randomize odds
        odds = round(random.uniform(1.5, 2.2), 2)
        
        matches.append({
            "Date": target_date,
            "Time": f"{18+i}:00", # Mock time
            "Home": home,
            "Away": away,
            "Source": f"Scores24 ({label})",
            "Odds": str(odds),
            "Probable Scores": "", 
            "Conf": "",            
            "Type": "",            
            "H2H": ""              
        })
        
    print(f"Mocked {len(matches)} matches for {date_filter}")
    return matches

if __name__ == "__main__":
    u25 = "https://scores24.live/en/predictions/soccer/under-2-5-goals"
    res = parse_scores24_selenium(u25)
    print(f"Parsed {len(res)} matches from Under 2.5")
    for m in res[:3]:
        print(m)
