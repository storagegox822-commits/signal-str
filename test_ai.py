import sys
import os
from dotenv import load_dotenv

# Ensure app imports work
sys.path.append(os.getcwd())
load_dotenv()

try:
    from app.main import analyze_express, AnalyzeRequest
    
    matches = [
        "Manchester City vs Chelsea | Date: 2026-02-15 19:00 | League: Premier League",
        "Real Madrid vs Barcelona | Date: 2026-02-16 21:00 | League: La Liga",
        "Juventus vs Milan | Date: 2026-02-17 20:00 | League: Serie A"
    ]
    
    print(f"Running AI Analysis for: {matches}...")
    req = AnalyzeRequest(matches=matches, model="gpt-4o-mini")
    res = analyze_express(req)
    
    if "analysis" in res:
        print("\n✅ AI Analysis Success!")
        print("-" * 20)
        print(res["analysis"][:500] + "...") # Print first 500 chars
        print("-" * 20)
    else:
        print("\n❌ AI Analysis Failed!")
        print(res)

except Exception as e:
    print(f"\n❌ Error: {e}")
