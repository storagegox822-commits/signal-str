#!/usr/bin/env python3
import os
import sys
import time
import json
from dotenv import load_dotenv

# Load Env
load_dotenv()

# Internal Imports
from app.main import run_scan, load_signals, analyze_express, save_history, HistoryItem, AnalyzeRequest
from app.utils import generate_variations, calculate_stakes, generate_express_html, upload_to_beget, send_telegram_message

def main():
    print("🤖 Signalizer Bot Starting...")
    
    # 1. Run Scan (3 Days)
    print("🔍 Running Scan (3 Days)...")
    try:
        scan_res = run_scan(days=3)
        if scan_res.get("status") != "success":
            print(f"❌ Scan failed: {scan_res.get('log')}")
            # Even if scan failed, check if we have cached signals? 
            # Ideally stop, but let's check cache.
    except Exception as e:
        print(f"❌ Scan Exception: {e}")

    # 2. Load Signals
    signals = load_signals()
    if not signals:
        print("⚠️ No signals found. Exiting.")
        return

    print(f"✅ Found {len(signals)} signals.")
    
    # Filter / Sort Logic (Take top 3 based on implementation or simple logic)
    # Assuming load_signals returns list of MatchSignal dicts
    # We need 3 matches for Express.
    if len(signals) < 3:
        print("⚠️ Not enough signals (need 3). Exiting.")
        return

    # Take Top 3 (Assuming they are sorted or just take first found)
    top_3 = signals[:3]
    matches_for_ai = [f"{s['Home']} vs {s['Away']}" for s in top_3]
    odds_data = [s.get('Odds', 0) for s in top_3] # Simplified odds handling
    
    # Pad Odds Data for 3 matches x 3 outcomes (Placeholder logic for tracking)
    # In dashboard logic, odds_data was list of 9 float. 
    # Here we might not have exact odds for 3 outcomes. 
    # Let's simplify and just pass what we have or 0.
    
    print(f"🔬 Analyzing Matches: {matches_for_ai}")
    
    # 3. AI Analysis
    req = AnalyzeRequest(matches=matches_for_ai, model="gpt-4o-mini")
    ai_res = analyze_express(req)
    analysis_text = ai_res.get("analysis", "")
    
    if not analysis_text or "Error" in analysis_text:
        print(f"❌ AI Analysis Failed: {analysis_text}")
        return

    # 4. Parse Analysis (Self-Healing Logic Replicated)
    # Improve: Import parsing logic? For now, replicate minimal necessary or use regex from utils?
    # Actually, let's keep it simple. We need explicit outcomes to generate variations.
    # We will try to parse "Strict" format from AI.
    
    import re
    blocks = analysis_text.split('⚽')
    if len(blocks) < 2: blocks = analysis_text.split('\n\n')
    
    parsed_outcomes = []
    meta_info = []
    
    for block in blocks:
        if not block.strip(): continue
        scores = re.findall(r'\b(\d{1})[:|-](\d{1})\b', block)
        outcomes = []
        for s in scores:
            try:
                g1, g2 = int(s[0]), int(s[1])
                if (g1+g2)%2 == 0: outcomes.append("ЧЕТ")
                else: outcomes.append(f"Счет {g1}:{g2}")
            except: pass
        
        # Uniquify & Enforce CHET
        u_out = []
        [u_out.append(x) for x in outcomes if x not in u_out]
        if "ЧЕТ" not in u_out: u_out.insert(0, "ЧЕТ")
        
        # Fill
        while len(u_out) < 3: u_out.append("ЧЕТ") # Fallback
        
        parsed_outcomes.append(u_out[:3])
        
        # Meta
        d = ""
        r = ""
        dm = re.search(r'📅.*?: (.*)', block)
        if dm: d = dm.group(1).strip()
        rm = re.search(r'📝.*?: (.*)', block)
        if rm: r = rm.group(1).strip()
        meta_info.append({'date': d, 'reason': r})
        
        if len(parsed_outcomes) == 3: break

    if len(parsed_outcomes) < 3:
        print("❌ Could not parse 3 matches outcomes.")
        return

    # 5. Generate Variations & Stakes (Fixed Profit Logic)
    variations = generate_variations(parsed_outcomes)
    BUDGET = 3000
    
    # Use Dutching with default odds (1.9) since we don't have specific outcome odds from AI yet.
    # This results in flat stakes but follows the "Fixed Profit" distribution logic.
    from app.utils import calculate_dutching_stakes
    stakes = calculate_dutching_stakes(BUDGET, variations, odds_flat_list=None)
    
    print(f"💰 Generated {len(variations)} variations. Stake: {stakes[0]:.2f} RUB")
    
    # 6. Generate HTML
    timestamp = int(time.time())
    filename = f"express_{timestamp}.html"
    
    html = generate_express_html(
        matches_for_ai[0], matches_for_ai[1], matches_for_ai[2],
        variations, stakes,
        meta_info[0] if len(meta_info)>0 else {},
        meta_info[1] if len(meta_info)>1 else {},
        meta_info[2] if len(meta_info)>2 else {},
        timestamp
    )
    
    # 7. Upload
    print("🚀 Uploading to Beget...")
    link = upload_to_beget(filename, html)
    
    if link:
        print(f"✅ Uploaded: {link}")
        
        # 8. Notify Telegram
        msg = f"🤖 **ABto-Bot Report**\n📅 Scan (3 Days)\n💰 Budget: 3000₽\n\n🌍 **Express Link:** {link}"
        tg_ok = send_telegram_message(
            os.getenv("TG_BOT_TOKEN"),
            os.getenv("TG_CHAT_ID"),
            msg
        )
        if tg_ok: print("✅ Notification sent.")
        else: print("❌ Telegram failed.")
        
        # 9. Save History
        h_item = HistoryItem(
            date=time.strftime("%Y-%m-%d"),
            matches=matches_for_ai,
            outcomes={"m1": parsed_outcomes[0], "m2": parsed_outcomes[1], "m3": parsed_outcomes[2]},
            odds={}, # Skip complex odds for now
            variations_count=len(variations),
            roi_calculation="-",
            timestamp=float(timestamp)
        )
        save_history(h_item)
        
    else:
        print("❌ Upload failed.")

if __name__ == "__main__":
    main()
