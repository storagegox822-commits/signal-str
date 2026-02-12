import os
import time
from dotenv import load_dotenv
from app.main import analyze_express, AnalyzeRequest, save_history, HistoryItem
from app.utils import generate_variations, calculate_dutching_stakes, generate_express_html, upload_to_beget, send_telegram_message

# Load Env
load_dotenv()

def test_main():
    print("🧪 Starting Test Workflow (Mock Signals)...")

    # Mock Signals
    matches_for_ai = [
        "Manchester City vs Chelsea",
        "Real Madrid vs Barcelona",
        "Juventus vs Milan"
    ]
    print(f"🔬 Analyzing Matches: {matches_for_ai}")

    # 1. AI Analysis
    req = AnalyzeRequest(matches=matches_for_ai, model="gpt-4o-mini")
    ai_res = analyze_express(req)
    analysis_text = ai_res.get("analysis", "")

    if not analysis_text or "Error" in analysis_text:
        print(f"❌ AI Analysis Failed: {analysis_text}")
        return

    # 2. Parse Analysis (Simple Mock Parse for Testing)
    # We simulate parsed outcomes to avoid fragile regex dependency in test
    parsed_outcomes = [
        ["ЧЕТ", "Счет 1:1", "Счет 2:0"],
        ["ЧЕТ", "Счет 2:2", "Счет 1:2"],
        ["ЧЕТ", "Счет 1:0", "Счет 0:1"]
    ]
    meta_info = [
        {'date': '2026-02-15', 'reason': 'Test Reason 1'},
        {'date': '2026-02-16', 'reason': 'Test Reason 2'},
        {'date': '2026-02-17', 'reason': 'Test Reason 3'}
    ]

    # 3. Generate Variations & Stakes
    variations = generate_variations(parsed_outcomes)
    BUDGET = 3000
    stakes = calculate_dutching_stakes(BUDGET, variations, odds_flat_list=None)

    print(f"💰 Generated {len(variations)} variations. Stake: {stakes[0]:.2f} RUB")

    # 4. Generate HTML
    timestamp = int(time.time())
    filename = f"test_express_{timestamp}.html"

    html = generate_express_html(
        matches_for_ai[0], matches_for_ai[1], matches_for_ai[2],
        variations, stakes,
        meta_info[0], meta_info[1], meta_info[2],
        timestamp
    )

    # 5. Upload
    print("🚀 Uploading to Beget...")
    link = upload_to_beget(filename, html)

    if link:
        print(f"✅ Uploaded: {link}")

        # 6. Notify Telegram
        msg = f"🧪 **Test Report**\n📅 Mock Data\n💰 Budget: 3000₽\n\n🌍 **Link:** {link}"
        tg_ok = send_telegram_message(
            os.getenv("TG_BOT_TOKEN"),
            os.getenv("TG_CHAT_ID"),
            msg
        )
        if tg_ok: print("✅ Notification sent.")
        else: print("❌ Telegram failed.")
        
    else:
        print("❌ Upload failed.")

if __name__ == "__main__":
    test_main()
