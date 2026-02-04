import streamlit as st
import pandas as pd
import requests
import json

# config
st.set_page_config(page_title="Signalizer 3.5 Dashboard", layout="wide")

# --- CROSS-ENV COMPATIBILITY ---
# Bridge Streamlit Secrets to OS Environ (for Streamlit Cloud)
try:
    if hasattr(st, "secrets"):
        import os
        for k, v in st.secrets.items():
            # Handle nested secrets possibly? usually flat for env vars
            if isinstance(v, str) and k not in os.environ:
                os.environ[k] = v
except Exception as e:
    pass # Ignore if no secrets

# --- MONOLITHIC IMPORTS ---
# Import logic directly from app/main.py to run without separate backend
try:
    from app.main import (
        load_signals, 
        run_scan, 
        analyze_express, 
        save_history, 
        notify_telegram,
        get_history,
        delete_history,
        AnalyzeRequest,
        HistoryItem,
        NotifyRequest, 
        DeleteHistoryRequest
    )
    USE_INTERNAL_API = True
except ImportError:
    USE_INTERNAL_API = False
    st.error("❌ Could not import backend logic. Ensure 'app/main.py' exists.")

st.title("⚽ Signalizer 3.5 Dashboard")
st.markdown("Automated Under 3.5 Opponent Analysis")

# Sidebar
st.sidebar.header("Controls")
days = st.sidebar.slider("Scan Days Ahead", 1, 14, 7)
if st.sidebar.button("Run Scan"):
    with st.spinner("Scanning leagues..."):
        try:
            if USE_INTERNAL_API:
                 # Direct call
                 res = run_scan(days)
                 # run_scan returns dict
                 if res.get("status") == "success":
                     st.sidebar.success(f"Scan complete! Found {res.get('found')} signals.")
                 else:
                     st.sidebar.error(f"Scan failed: {res.get('log')}")
            else:
                 # Fallback (Legacy)
                 requests.post(f"http://localhost:8000/scan/{days}")
        except Exception as e:
            st.sidebar.error(f"Scan Error: {e}")

# Tabs
tab1, tab_ai, tab_express, tab4 = st.tabs(["Signals", "AI Analyzer", "Express Editor", "Backtest"])

with tab1:
    st.subheader("Current Signals")
    
    # Try local cache/Direct Read
    import os
    signals_df = pd.DataFrame()
    loaded_source = "Internal"
    
    # DIRECT LOAD
    if USE_INTERNAL_API:
        try:
            data = load_signals()
            if data:
                 signals_df = pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error loading signals: {e}")
    
    if not signals_df.empty:
        st.dataframe(signals_df, use_container_width=True)
    else:
        st.info("No signals found. Try running a scan.")

with tab_express:
    st.subheader("🛠️ Express Editor (27 Variations)")
    st.markdown("Create a system from 3 matches. Covers all combinations.")

    # Check for transferred data
    is_transferred = False
    if 'express_data' in st.session_state:
        st.info("ℹ️ Using data from AI Analyzer")
        ed = st.session_state['express_data']
        
        # SELF-HEAL: Ensure "ЧЕТ" is in outcomes for safety
        for key in ['outcomes_1', 'outcomes_2', 'outcomes_3']:
            if key in ed:
                outcomes = ed[key]
                if "ЧЕТ" not in outcomes and len(outcomes) >= 3:
                     outcomes[0] = "ЧЕТ" # Force replace first for max safety
                     ed[key] = outcomes
                     st.session_state['express_data'] = ed # Update state
        
        default_m1 = ed['m1_name']
        default_m2 = ed['m2_name']
        default_m3 = ed['m3_name']
        is_transferred = True
    else:
        # Default Auto-fill logic (Scanner)
        default_m1 = "Team A vs Team B"
        default_m2 = "Team C vs Team D"
        default_m3 = "Team E vs Team F"
        try:
             # Existing scanner fallback...
             pass 
        except:
             pass

    col1, col2, col3 = st.columns(3)
    m1 = col1.text_input("Match 1", default_m1)
    m2 = col2.text_input("Match 2", default_m2)
    m3 = col3.text_input("Match 3", default_m3)
    
    # Selection Mode
    if is_transferred:
        st.markdown("**Outcomes & Odds (From AI):**")
        
        # Load odds from session if exist, else 1.0
        if 'odds_data' not in st.session_state:
            st.session_state['odds_data'] = [1.9]*9 # Default odds
        
        # Helper for Input Grid
        def odds_row(match_idx, match_name, outcomes, offset):
            st.markdown(f"**{match_name}**")
            c1, c2, c3 = st.columns(3)
            with c1: 
                st.write(f"🔹 {outcomes[0]}")
                st.session_state['odds_data'][offset] = st.number_input(f"Odds 1", 1.0, 100.0, st.session_state['odds_data'][offset], key=f"o_{offset}" )
            with c2: 
                st.write(f"🔹 {outcomes[1]}")
                st.session_state['odds_data'][offset+1] = st.number_input(f"Odds 2", 1.0, 100.0, st.session_state['odds_data'][offset+1], key=f"o_{offset+1}" )
            with c3: 
                st.write(f"🔹 {outcomes[2]}")
                st.session_state['odds_data'][offset+2] = st.number_input(f"Odds 3", 1.0, 100.0, st.session_state['odds_data'][offset+2], key=f"o_{offset+2}" )

        o1 = st.session_state['express_data']['outcomes_1']
        o2 = st.session_state['express_data']['outcomes_2']
        o3 = st.session_state['express_data']['outcomes_3']
        
        odds_row(1, m1, o1, 0)
        odds_row(2, m2, o2, 3)
        odds_row(3, m3, o3, 6)
        
        # ROI Calculator
        st.markdown("### 💰 ROI Calculator")
        
        calc_mode = st.radio("Режим Расчета", ["Фиксированная Ставка (Fixed Stake)", "Равная Прибыль (Equal Profit)"], horizontal=True)
        
        if calc_mode == "Фиксированная Ставка (Fixed Stake)":
            stake = st.number_input("Ставка на один вариант (Unit)", 100, 10000, 1000)
            if st.button("Рассчитать Потенциал"):
                 import numpy as np
                 od = st.session_state['odds_data']
                 # Potential returns for all 27 combos
                 potentials = []
                 # Indices: 0-2 (M1), 3-5 (M2), 6-8 (M3)
                 for i in range(3):
                     for j in range(3,6):
                         for k in range(6,9):
                             combo_odd = od[i] * od[j] * od[k]
                             potentials.append(combo_odd * stake)
                 
                 min_win = min(potentials)
                 max_win = max(potentials)
                 total_cost = stake * 27
                 
                 st.info(f"📉 Общая Стоимость: {total_cost}\n\n💸 Мин. Выплата: {min_win:.2f} (Прибыль: {min_win-total_cost:.2f})\n\n🚀 Макс. Выплата: {max_win:.2f} (Прибыль: {max_win-total_cost:.2f})")
                 st.session_state['last_roi'] = f"Profit: {min_win-total_cost:.0f}..{max_win-total_cost:.0f}"
                 
                 # Store stakes for checklist
                 st.session_state['current_stakes'] = [stake] * 27
        
        else:
            # EQUAL PROFIT MODE
            total_budget = st.number_input("Общий Бюджет (Total Budget)", 1000, 1000000, 27000, step=1000)
            if st.button("Рассчитать Распределение (Dutching)"):
                od = st.session_state['odds_data']
                
                # 1. Generate all combos and their total odds
                combos = []
                implied_prob_sum = 0
                
                # Indices: 0-2 (M1), 3-5 (M2), 6-8 (M3)
                for i in range(3):
                    for j in range(3,6):
                         for k in range(6,9):
                             combo_odd = od[i] * od[j] * od[k]
                             # Avoid division by zero
                             if combo_odd <= 1.0: combo_odd = 1.01 
                             
                             prob = 1 / combo_odd
                             implied_prob_sum += prob
                             
                             combos.append({
                                 "indices": (i, j, k),
                                 "odds": combo_odd,
                                 "prob": prob
                             })
                
                # 2. Calculate Constant Return
                # Constant Return = Total Budget / Sum(1/odds)
                constant_return = total_budget / implied_prob_sum
                net_profit = constant_return - total_budget
                roi = (net_profit / total_budget) * 100
                
                st.success(f"💎 Гарантированная Выплата (Payout): {constant_return:.2f} RUB")
                
                col_res1, col_res2 = st.columns(2)
                col_res1.metric("Чистая Прибыль (Net Profit)", f"{net_profit:.2f} RUB")
                col_res2.metric("ROI", f"{roi:.2f}%")
                
                # 3. Calculate Individual Stakes and Prepare Table
                results_data = []
                
                # Need outcome names for table
                o1_names = st.session_state['express_data']['outcomes_1'] # len 3
                o2_names = st.session_state['express_data']['outcomes_2'] # len 3
                o3_names = st.session_state['express_data']['outcomes_3'] # len 3
                
                outcomes_list = [o1_names, o2_names, o3_names]
                
                for c in combos:
                    req_stake = constant_return / c['odds']
                    
                    # Map indices to names. 
                    # c['indices'] are raw like 0, 3, 6.
                    # M1 indices: 0,1,2 -> map to 0,1,2
                    # M2 indices: 3,4,5 -> map to 0,1,2
                    # M3 indices: 6,7,8 -> map to 0,1,2
                    
                    idx1 = c['indices'][0]
                    idx2 = c['indices'][1] - 3
                    idx3 = c['indices'][2] - 6
                    
                    name1 = o1_names[idx1] if idx1 < len(o1_names) else "?"
                    name2 = o2_names[idx2] if idx2 < len(o2_names) else "?"
                    name3 = o3_names[idx3] if idx3 < len(o3_names) else "?"
                    
                    results_data.append({
                        "Вариант": f"{name1} + {name2} + {name3}",
                        "Коэфф.": f"{c['odds']:.2f}",
                        "Сумма Ставки (RUB)": f"{req_stake:.0f}", # Round for readability
                        "Возможная Выплата": f"{req_stake * c['odds']:.2f}",
                        "Чистая Прибыль": f"{(req_stake * c['odds']) - total_budget:.2f}"
                    })
                
                st.write("### 📋 Распределение Ставок:")
                st.dataframe(pd.DataFrame(results_data), use_container_width=True)
                
                st.session_state['last_roi'] = f"Const Profit: {net_profit:.0f}"
                
                # Store stakes for checklist (ordered)
                # We need to make sure the order matches the 'variations' generation order.
                # The 'combos' list was generated with nested loops: i (0-2), j (3-5), k (6-9)
                # This matches itertools.product order used in generation.
                st.session_state['current_stakes'] = [constant_return / c['odds'] for c in combos]

        # Save to History
        if st.button("💾 Save to History"):
             import time
             try:
                 # Prepare Item
                 item_data = {
                     "date": st.session_state['express_data'].get('m1_meta',{}).get('date', 'Today'),
                     "matches": [m1, m2, m3],
                     "outcomes": {"m1": o1, "m2": o2, "m3": o3},
                     "odds": {"m1": st.session_state['odds_data'][0:3], "m2": st.session_state['odds_data'][3:6], "m3": st.session_state['odds_data'][6:9]},
                     "variations_count": 27,
                     "roi_calculation": st.session_state.get('last_roi', "N/A"),
                     "timestamp": time.time()
                 }
                 
                 if USE_INTERNAL_API:
                     item = HistoryItem(**item_data)
                     res = save_history(item)
                     if res.get("status") == "saved":
                         st.success("Saved to Backtest/History!")
                     else:
                         st.error("Error saving history")
                 else:
                     requests.post(f"{API_URL}/save_history", json=item_data)
                     st.success("Saved to Backtest/History!")
             except Exception as e:
                 st.error(f"Save failed: {e}")

        # Implicit Generation Mode for AI Data
        bet_mode = None 
        should_generate = True # Auto-generate
    else:
        # Manual Mode - Strictly 1X2 (27 variations)
        bet_mode = "1X2"
        should_generate = st.button("Generate Variations")
    
    from express_logic import ExpressGenerator
    gen = ExpressGenerator()
    
    # State Management for Variations
    if 'generated_variations' not in st.session_state:
        st.session_state['generated_variations'] = []
    
    # Trigger Generation
    if should_generate:
        # If manual validation (button click) or auto-transfer (always true)
        # For manual: only run if button clicked. For transfer: run if empty or matches changed?
        # To avoid re-generating on every click in AI mode, checks implied.
        
        # For AI mode, we run once when data arrives or simply render if present.
        # Ideally, we only run generation if list is empty OR explicit button click.
        
        matches = [m1, m2, m3]
        variations = []
        
        if is_transferred:
            import itertools
            variations = list(itertools.product(o1, o2, o3))
        elif bet_mode == "1X2":
            variations = gen.generate_27_system(matches)
        
        # Update State
        st.session_state['generated_variations'] = variations

    # RENDER FROM STATE
    variations = st.session_state['generated_variations']
    if variations:
        st.success(f"Сгенерировано {len(variations)} вариантов")
        
        # Display Legend (Enhanced)
        st.markdown("### 🔑 Легенда Матчей:")
        
        # Check if we have meta data (from new parsing)
        meta_1 = ed.get('m1_meta', {}) if is_transferred else {}
        meta_2 = ed.get('m2_meta', {}) if is_transferred else {}
        meta_3 = ed.get('m3_meta', {}) if is_transferred else {}
        
        def render_legend_item(idx, match_name, meta, outcomes):
             date_s = meta.get('date', '') if meta else ''
             reason_s = meta.get('reason', '') if meta else ''
             # Format outcome list string
             out_str = ", ".join(outcomes)
             
             content = f"**{idx}️⃣ {match_name}**"
             if date_s: content += f"  |  📅 {date_s}"
             content += f"\n\n🎯 **Ожидание:** {out_str}"
             if reason_s: content += f"\n\n📝 **Сценарий:** {reason_s}"
             
             st.info(content)

        render_legend_item(1, m1, meta_1, o1 if is_transferred else [])
        render_legend_item(2, m2, meta_2, o2 if is_transferred else [])
        render_legend_item(3, m3, meta_3, o3 if is_transferred else [])

        # Helper to strict shorten
        import re
        def clean_match_name(m):
             # Remove dates (YYYY-MM-DD)
             m = re.sub(r'\d{4}-\d{2}-\d{2}', '', m)
             # Remove short dates (DD-MM)
             m = re.sub(r'\d{2}-\d{2}', '', m)
             # Remove times
             m = re.sub(r'\d{2}:\d{2}', '', m)
             
             # Format as Team - Team
             if " vs " in m:
                 m = m.replace(" vs ", " - ")
             
             return m.strip()
        
        n1 = clean_match_name(m1)
        n2 = clean_match_name(m2)
        n3 = clean_match_name(m3)

        # Display with Checkboxes
        st.markdown("### 📋 Чек-лист Вариантов (Отмечай сделанные):")
        
        # Check if we have stakes to show
        show_stakes = False
        stakes_list = []
        if 'current_stakes' in st.session_state and len(st.session_state['current_stakes']) == len(variations):
            show_stakes = True
            stakes_list = st.session_state['current_stakes']
        
        for i, v in enumerate(variations):
            # Format: 1️⃣ Name: Outcome | 2️⃣ Name: Outcome...
            # User requested full names like Winline (Team - Team)
            bet_str = f"**1️⃣ {n1}**: {v[0]}   |   **2️⃣ {n2}**: {v[1]}   |   **3️⃣ {n3}**: {v[2]}"
            
            if show_stakes:
                bet_str += f"   💰 **{stakes_list[i]:.0f} ₽**"
            
            # Unique key
            key = f"var_{i}"
            
            # check state to apply style
            is_checked = st.session_state.get(key, False)
            
            if is_checked:
                label = f"~~🎫 Вариант #{i+1}:  {bet_str}~~"
            else:
                label = f"🎫 Вариант #{i+1}:  {bet_str}"
            
            st.checkbox(label, key=key)

        # Telegram Notification with HTML Snapshot
        if is_transferred and st.button("📲 Отправить в Telegram"):
             try:
                 with st.spinner("⏳ Генерация и загрузка HTML..."):
                     import time
                     import paramiko
                     
                     # 1. Generate HTML (Rich Template)
                     timestamp = int(time.time())
                     filename = f"express_{timestamp}.html"
                     
                     # Extract Data for Legend
                     # Clean names for checklist
                     import re
                     def clean_match_name_html(m):
                          m = re.sub(r'\d{4}-\d{2}-\d{2}', '', m)
                          m = re.sub(r'\d{2}-\d{2}', '', m)
                          m = re.sub(r'\d{2}:\d{2}', '', m)
                          m = m.replace('*', '') # Remove asterisks
                          if " vs " in m: m = m.replace(" vs ", " - ")
                          return m.strip()
                     
                     n1, n2, n3 = clean_match_name_html(m1), clean_match_name_html(m2), clean_match_name_html(m3)
                     
                     # Get Meta
                     ed = st.session_state.get('express_data', {})
                     meta1 = ed.get('m1_meta', {})
                     meta2 = ed.get('m2_meta', {})
                     meta3 = ed.get('m3_meta', {})
                     
                     # Outcomes strings
                     o1_str = ", ".join(o1) if isinstance(o1, list) else str(o1)
                     o2_str = ", ".join(o2) if isinstance(o2, list) else str(o2)
                     o3_str = ", ".join(o3) if isinstance(o3, list) else str(o3)
                     
                     # Get Stakes if available
                     stakes_list = st.session_state.get('current_stakes', [])
                     use_stakes = len(stakes_list) == len(variations)
                     
                     html_content = f"""
                     <!DOCTYPE html>
                     <html lang="ru">
                     <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Express Analysis #{timestamp}</title>
                        <style>
                            :root {{
                                --bg: #ffffff;
                                --text: #31333f;
                                --accent: #ff4b4b;
                                --card-bg: #f0f2f6; 
                                --border: #e0e0e0;
                            }}
                            body {{ 
                                font-family: "Source Sans Pro", -apple-system, sans-serif; 
                                background-color: var(--bg); 
                                color: var(--text); 
                                padding: 20px; 
                                max-width: 900px; 
                                margin: 0 auto; 
                            }}
                            h1, h2, h3 {{ color: #0e1117; font-weight: 600; }}
                            
                            /* Legend Styles */
                            .legend-card {{
                                background-color: #e8f4f9; /* Light Blue tint like screenshot */
                                border-radius: 8px;
                                padding: 15px;
                                margin-bottom: 15px;
                                border: 1px solid #d1e4ee;
                            }}
                            .match-header {{
                                font-weight: bold;
                                color: #0068c9;
                                margin-bottom: 8px;
                                display: flex;
                                align-items: center;
                                gap: 10px;
                            }}
                            .match-info {{ margin-bottom: 5px; font-size: 0.95em; }}
                            .icon {{ font-size: 1.2em; }}
                            
                            /* Checklist Styles */
                            .checklist-container {{
                                margin-top: 30px;
                            }}
                            .checklist-item {{
                                padding: 10px 0;
                                border-bottom: 1px solid #eee;
                                display: flex;
                                align-items: center;
                                transition: 0.2s;
                            }}
                            .checklist-item:hover {{ background-color: #f9f9f9; }}
                            .checklist-item input[type="checkbox"] {{
                                width: 20px;
                                height: 20px;
                                margin-right: 15px;
                                cursor: pointer;
                                accent-color: var(--accent);
                            }}
                            .checklist-label {{
                                font-size: 1em;
                                cursor: pointer;
                                line-height: 1.4;
                            }}
                            .checklist-item.checked .checklist-label {{
                                text-decoration: line-through;
                                color: #888;
                            }}
                            .var-badge {{
                                font-weight: bold;
                                color: #555;
                                margin-right: 5px;
                            }}
                            .team-tag {{
                                background: #eee;
                                padding: 2px 6px;
                                border-radius: 4px;
                                font-size: 0.85em;
                                margin: 0 4px;
                            }}
                            .stake-tag {{
                                margin-left: 10px;
                                font-weight: bold;
                                color: #2e7d32;
                                background: #e8f5e9;
                                padding: 2px 8px;
                                border-radius: 4px;
                            }}
                        </style>
                     </head>
                     <body>
                        <h1>ℹ️ Легенда Матчей:</h1>
                        
                        <!-- MATCH 1 -->
                        <div class="legend-card">
                            <div class="match-header">
                                <span class="icon">1️⃣</span> {n1} | 📅 {meta1.get('date', '')}
                            </div>
                            <div class="match-info">🎯 <strong>Ожидание:</strong> {o1_str}</div>
                            <div class="match-info">📝 <strong>Сценарий:</strong> {meta1.get('reason', 'N/A')}</div>
                        </div>

                        <!-- MATCH 2 -->
                        <div class="legend-card">
                            <div class="match-header">
                                <span class="icon">2️⃣</span> {n2} | 📅 {meta2.get('date', '')}
                            </div>
                            <div class="match-info">🎯 <strong>Ожидание:</strong> {o2_str}</div>
                            <div class="match-info">📝 <strong>Сценарий:</strong> {meta2.get('reason', 'N/A')}</div>
                        </div>

                        <!-- MATCH 3 -->
                        <div class="legend-card">
                            <div class="match-header">
                                <span class="icon">3️⃣</span> {n3} | 📅 {meta3.get('date', '')}
                            </div>
                            <div class="match-info">🎯 <strong>Ожидание:</strong> {o3_str}</div>
                            <div class="match-info">📝 <strong>Сценарий:</strong> {meta3.get('reason', 'N/A')}</div>
                        </div>

                        <div class="checklist-container">
                            <h2>📋 Чек-лист Вариантов (Отмечай сделанные):</h2>
                     """
                     
                     for i, v in enumerate(variations):
                         stake_html = ""
                         if use_stakes:
                             stake_html = f'<span class="stake-tag">💰 {stakes_list[i]:.0f} ₽</span>'
                         
                         # Format: Var #1: [1] Team...: Outcome | [2] Team...: Outcome ...
                         row_html = f"""
                         <div class="checklist-item" id="row_{i}">
                            <input type="checkbox" onclick="toggleRow({i})">
                            <label class="checklist-label" onclick="toggleRow({i})">
                                <span class="var-badge">🎫 В{i+1}:</span> 
                                <span class="team-tag">1️⃣ {n1}</span> <b>{v[0]}</b> | 
                                <span class="team-tag">2️⃣ {n2}</span> <b>{v[1]}</b> | 
                                <span class="team-tag">3️⃣ {n3}</span> <b>{v[2]}</b>
                                {stake_html}
                            </label>
                         </div>
                         """
                         html_content += row_html
                         
                     html_content += """
                        </div>
                        
                        <script>
                            function toggleRow(id) {
                                var row = document.getElementById("row_" + id);
                                var checkbox = row.querySelector("input[type='checkbox']");
                                
                                // If triggered by label click, toggle checkbox manually
                                if (event.target !== checkbox) {
                                    checkbox.checked = !checkbox.checked;
                                }
                                
                                if (checkbox.checked) {
                                    row.classList.add("checked");
                                } else {
                                    row.classList.remove("checked");
                                }
                            }
                        </script>
                     </body>
                     </html>
                     """
                     
                     # 2. Upload to Beget
                     HOST = 'ttimbah0.beget.tech'
                     USER = 'ttimbah0'
                     PASS = '@@Ae32c1c5'
                     REMOTE_DIR = '/home/t/ttimbah0/dev.5na5.ru/public_html/project/expbeg/snapshots'
                     PUBLIC_URL = f"http://dev.5na5.ru/project/expbeg/snapshots/{filename}"
                     
                     ssh = paramiko.SSHClient()
                     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                     ssh.connect(HOST, username=USER, password=PASS)
                     
                     # Ensure dir exists
                     ssh.exec_command(f"mkdir -p {REMOTE_DIR}")
                     
                     sftp = ssh.open_sftp()
                     with sftp.open(f"{REMOTE_DIR}/{filename}", "w") as f:
                         f.write(html_content)
                     sftp.close()
                     ssh.close()
                     
                     # 3. Send to Telegram
                     msg = f"🆕 **Новый Экспресс**\n📅 {st.session_state['express_data'].get('m1_meta',{}).get('date', 'Today')}\n\n🌍 **Ссылка:** {PUBLIC_URL}"
                     
                     if USE_INTERNAL_API:
                         notify_telegram(NotifyRequest(message=msg))
                     else:
                         requests.post(f"{API_URL}/notify_telegram", json={"message": msg})
                     
                     st.success(f"Загружено! Ссылка отправлена в бот: {PUBLIC_URL}")
                     st.markdown(f"[Открыть Посстоянную Ссылку]({PUBLIC_URL})")
                     
             except Exception as e:
                 st.error(f"Ошибка загрузки: {e}")

with tab_ai:
    # ========================================
    # AI ANALYZER (Improved UI)
    # ========================================
    with st.expander("🤖 AI Анализатор", expanded=True):
        st.markdown("### Вставь матчи (один на строку)")
        
        col1, col2 = st.columns([3,1])
        with col1:
            matches_input = st.text_area(
                "Матчи:",
                placeholder="CA Tigre vs Racing Club\nGimnasia vs Aldosivi\n...",
                height=150
            )
        with col2:
            model_choice = st.selectbox("AI Модель", ["Perplexity Sonar", "GPT-4o Mini"])
        
        if st.button("🚀 Анализировать") and matches_input.strip():
            with st.spinner("🤖 ИИ думает..."):
                # Clean and split matches
                raw_lines = [m.strip() for m in matches_input.strip().split('\n') if m.strip()]
                matches = []
                
                for line in raw_lines:
                    # HEURISTIC: Check for specific "Tabbed" format from user
                    # Format: 0 \t League \t Date \t Team A \t Team B
                    if '\t' in line:
                         parts = [p.strip() for p in line.split('\t') if p.strip()]
                         # Usually last 2 are teams, or indices 3 and 4
                         if len(parts) >= 2:
                             # Try to find the teams. Heuristic: take last 2 textual columns
                             # Or just take specifically index 3 and 4 if len >= 5
                             if len(parts) >= 5: 
                                 matches.append(f"{parts[3]} vs {parts[4]}")
                             else:
                                 # Fallback: Join last 2
                                 matches.append(f"{parts[-2]} vs {parts[-1]}")
                    else:
                         # assume standard format
                         matches.append(line)
                
                try:
                    analysis_text = ""
                    
                    if USE_INTERNAL_API:
                         # Internal Call
                         from app.main import AnalyzeRequest
                         req = AnalyzeRequest(matches=matches, model=model_choice)
                         res = analyze_express(req)
                         analysis_text = res.get("analysis", "")
                         if "Error" in analysis_text:
                             st.error(analysis_text)
                             analysis_text = "" # Fail
                    else:
                        # Legacy API
                        payload = {"matches": matches, "model": model_choice}
                        res = requests.post(f"{API_URL}/analyze_express", json=payload)
                        if res.status_code == 200:
                            analysis_text = res.json()["analysis"]
                        else:
                            st.error(f"Ошибка анализа: {res.text}")

                    if analysis_text:
                        st.success("✅ Анализ Завершен")
                        st.markdown(analysis_text)
                        
                        # Store analysis in session state for parsing
                        st.session_state['last_analysis'] = analysis_text
                        st.session_state['analyzed_matches'] = matches
                except Exception as e:
                    st.error(f"Ошибка: {e}")

        # Transfer Button Logic
        if 'last_analysis' in st.session_state:
            if st.button("🔄 Перенести в Редактор Экспрессов"):
                # Parsing Logic
                import re
                analysis = st.session_state['last_analysis']
                
                # --- Robust Parsing Strategy ---
                blocks = []
                
                # Method 1: Split by Emoji (Standard)
                if '⚽' in analysis:
                     blocks = analysis.split('⚽')
                
                # Method 2: Regex for Numbered Matches (Fallback)
                if len(blocks) < 2:
                     # Look for "1. Team A vs Team B" or similar patterns
                     # Split by lookahead for digit + dot + space at start of line
                     blocks = re.split(r'\n\d+\.\s', analysis)
                
                # Method 3: Double Newline (Last Resort)
                if len(blocks) < 2:
                     blocks = analysis.split('\n\n')

                parsed_outcomes = []
                parsed_names = [] # Store extracted names
                matched_meta = []
                
                # Validation Data
                all_names_russian = True
                
                for block in blocks:
                    if not block.strip(): continue
                    
                    # Extract Name (First non-empty line usually)
                    lines = block.strip().split('\n')
                    block_name = lines[0].strip()
                    # Clean common prefixes
                    block_name = block_name.replace('⚽', '').strip()
                    # Remove "1. ", "2. " etc
                    block_name = re.sub(r'^\d+\.\s*', '', block_name)
                    
                    parsed_names.append(block_name)
                    
                    # Extract scores (looking for 1:1, 2:0 etc). 
                    # STRICT REGEX: Single digit only to avoid Match Times like 19:30, 23:30
                    scores = re.findall(r'\b(\d{1})[:|-](\d{1})\b', block)
                    
                    # Apply Logic: If Sum Even -> "Even", Else -> "CS Score"
                    outcomes = []
                    for s in scores:
                        try:
                            g1, g2 = int(s[0]), int(s[1])
                            total = g1 + g2
                            
                            # Double check for sanity (Under 3.5 usually low scores)
                            if g1 > 5 or g2 > 5: continue 
                            
                            if total % 2 == 0:
                                outcomes.append("ЧЕТ")
                            else:
                                outcomes.append(f"Счет {g1}:{g2}")
                        except:
                            pass
                    
                    # Unique
                    unique_outcomes = []
                    for o in outcomes:
                        if o not in unique_outcomes:
                            unique_outcomes.append(o)
                    
                    # STRICT RULE: Must include "ЧЕТ"
                    if "ЧЕТ" not in unique_outcomes:
                         # Insert at 0 to ensure it survives the slice (Highest Priority)
                         unique_outcomes.insert(0, "ЧЕТ")
                    
                    # Keep Top 3
                    unique_outcomes = unique_outcomes[:3]
                    
                    # Fill if needed (unlikely if CHET is there, but if only CHET exists...)
                    if len(unique_outcomes) < 3:
                        # Fallbacks
                        if "Счет 2:1" not in unique_outcomes: unique_outcomes.append("Счет 2:1")
                        if "Счет 1:0" not in unique_outcomes: unique_outcomes.append("Счет 1:0")
                        if "ЧЕТ" not in unique_outcomes: unique_outcomes.append("ЧЕТ")
                    
                    parsed_outcomes.append(unique_outcomes[:3])
                    
                    # EXTRACT DETAILS (Date & Reason)
                    date_info = ""
                    reason_info = ""
                    try:
                        date_match = re.search(r'📅.*?: (.*)', block)
                        if date_match: date_info = date_match.group(1).strip()
                        
                        reason_match = re.search(r'📝.*?: (.*)', block)
                        if reason_match: reason_info = reason_match.group(1).strip()
                    except:
                         pass
                    
                    # Store meta keys
                    matched_meta.append({'date': date_info, 'reason': reason_info})

                # Store result
                if len(parsed_outcomes) >= 3:
                    # Provide defaults for meta if parsing failed
                    metas = matched_meta + [{'date':'', 'reason':''}]*3 
                    
                    # Use Parsed Names if available, else Fallback
                    m1_n = parsed_names[0] if len(parsed_names) > 0 else (st.session_state['analyzed_matches'][0] if len(st.session_state['analyzed_matches']) > 0 else "Матч 1")
                    m2_n = parsed_names[1] if len(parsed_names) > 1 else (st.session_state['analyzed_matches'][1] if len(st.session_state['analyzed_matches']) > 1 else "Матч 2")
                    m3_n = parsed_names[2] if len(parsed_names) > 2 else (st.session_state['analyzed_matches'][2] if len(st.session_state['analyzed_matches']) > 2 else "Матч 3")

                    st.session_state['express_data'] = {
                        'm1_name': m1_n,
                        'm1_meta': metas[0],
                        
                        'm2_name': m2_n,
                        'm2_meta': metas[1],
                        
                        'm3_name': m3_n,
                        'm3_meta': metas[2],
                        
                        'outcomes_1': parsed_outcomes[0],
                        'outcomes_2': parsed_outcomes[1],
                        'outcomes_3': parsed_outcomes[2]
                    }
                    st.success(f"✅ Успешно перенесено {len(parsed_outcomes)} матчей!")
                else:
                    st.warning(f"⚠️ Распознано только {len(parsed_outcomes)} уникальных матчей из 3. Проверьте формат.")
                    with st.expander("🕵️ Показать Ответ AI (Raw Text)"):
                        st.text(st.session_state['last_analysis'])
                    st.info("💡 Совет: Попробуйте 'GPT-4o Mini' или проанализируйте заново.")

# In Tab 2 (Express Editor), we need to check session_state
# This requires modifying the top of the file/tab 2 logic too.
# But since I am editing Tab 3 check, I will only inject the transfer logic here.
# I need to use replace_file_content separately for Tab 2 adjustments.

with tab4:
    st.subheader("📚 История Анализов (Backtest)")
    
    col1, col2 = st.columns([1, 1])
    if col1.button("🔄 Обновить Историю"):
        st.rerun()

    if col2.button("🗑️ Удалить ВСЕ", type="primary"):
        if USE_INTERNAL_API:
             delete_history(DeleteHistoryRequest(delete_all=True))
        else:
             requests.post(f"{API_URL}/delete_history", json={"delete_all": True})
             
        st.success("История очищена!")
        import time
        time.sleep(1)
        st.rerun()

    try:
        # Use new History endpoint
        history = []
        if USE_INTERNAL_API:
             history = get_history()
        else:
             res = requests.get(f"{API_URL}/get_history")
             if res.status_code == 200:
                 history = res.json()
                 
        if not history:
            st.info("История пуста.")
        else:
            # Show newest first
            for i, item in enumerate(reversed(history)):
                # Use columns inside expander header or just custom layout
                cols = st.columns([0.9, 0.1])
                title = f"📅 {item.get('date','Dateless')} | 🔢 {len(item.get('matches',[]))} Матчей (ROI: {item.get('roi_calculation','?')})"
                
                with st.expander(title):
                     c1, c2 = st.columns(2)
                     c1.write("**Матчи:**")
                     for m in item.get('matches', []):
                         c1.write(f"- {m}")
                     
                     c2.write("**Кэфы (ROI):**")
                     c2.info(item.get('roi_calculation', 'N/A'))
                     
                     st.json(item) # Show full data debug
                     
                     if st.button("❌ Удалить этот анализ", key=f"del_{item.get('timestamp', i)}"):
                         if USE_INTERNAL_API:
                             delete_history(DeleteHistoryRequest(timestamp=item.get('timestamp')))
                         else:
                             requests.post(f"{API_URL}/delete_history", json={"timestamp": item.get('timestamp')})
                             
                         st.success("Удалено!")
                         st.rerun()
    except Exception as e:
        st.write(f"Нет данных или ошибка: {e}")
