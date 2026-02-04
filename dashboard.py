import streamlit as st
import pandas as pd
import requests
import json
import os

# config
st.set_page_config(page_title="Signalizer 3.5 Dashboard", layout="wide")

# --- AUTHENTICATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_login():
    if st.session_state.get("username_input") == "timbot" and st.session_state.get("password_input") == "Ae32c1c5":
        st.session_state.authenticated = True
    else:
        st.error("❌ Неверный логин или пароль")

if not st.session_state.authenticated:
    st.title("🔒 Вход в систему")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.text_input("Логин", key="username_input")
        st.text_input("Пароль", type="password", key="password_input")
        st.button("Войти", on_click=check_login)
    st.stop() # Stop execution until logged in
# ----------------------

# --- CROSS-ENV COMPATIBILITY ---
# Bridge Streamlit Secrets to OS Environ (for Streamlit Cloud)
try:
    if hasattr(st, "secrets"):
        for k, v in st.secrets.items():
            if isinstance(v, str) and k not in os.environ:
                os.environ[k] = v
except Exception as e:
    pass # Ignore if no secrets

# --- MONOLITHIC IMPORTS ---
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

# --- ENV VALIDATION ---
missing_keys = []
if "OPENAI_API_KEY" not in os.environ and "PERPLEXITY_API_KEY" not in os.environ:
    missing_keys.append("AI Key (OpenAI or Perplexity)")
if "TG_BOT_TOKEN" not in os.environ:
    missing_keys.append("TG Bot Token")

if missing_keys:
    st.sidebar.warning(f"⚠️ Missing Secrets:\n" + "\n".join([f"- {k}" for k in missing_keys]))
    st.sidebar.info("Add them in Streamlit Cloud -> Settings -> Secrets")
# ----------------------
days = st.sidebar.slider("Scan Days Ahead", 1, 14, 7)
if st.sidebar.button("Run Scan"):
    with st.spinner("Scanning leagues..."):
        try:
            if USE_INTERNAL_API:
                 res = run_scan(days)
                 if res.get("status") == "success":
                     st.sidebar.success(f"Scan complete! Found {res.get('found')} signals.")
                 else:
                     st.sidebar.error(f"Scan failed: {res.get('log')}")
            else:
                 requests.post(f"http://localhost:8000/scan/{days}")
        except Exception as e:
            st.sidebar.error(f"Scan Error: {e}")

# Tabs
tab1, tab_ai, tab_express, tab4 = st.tabs(["Signals", "AI Analyzer", "Express Editor", "Backtest"])

with tab1:
    st.subheader("Current Signals")
    signals_df = pd.DataFrame()
    
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
        default_m1 = "Team A vs Team B"
        default_m2 = "Team C vs Team D"
        default_m3 = "Team E vs Team F"

    col1, col2, col3 = st.columns(3)
    m1 = col1.text_input("Match 1", default_m1)
    m2 = col2.text_input("Match 2", default_m2)
    m3 = col3.text_input("Match 3", default_m3)
    
    # Selection Mode
    if is_transferred:
        st.markdown("**Outcomes & Odds (From AI):**")
        
        if 'odds_data' not in st.session_state:
            st.session_state['odds_data'] = [1.9]*9 
        
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
                 potentials = []
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
                 st.session_state['current_stakes'] = [stake] * 27
        
        else:
            # EQUAL PROFIT MODE
            total_budget = st.number_input("Общий Бюджет (Total Budget)", 1000, 1000000, 27000, step=1000)
            if st.button("Рассчитать Распределение (Dutching)"):
                od = st.session_state['odds_data']
                combos = []
                implied_prob_sum = 0
                for i in range(3):
                    for j in range(3,6):
                         for k in range(6,9):
                             combo_odd = od[i] * od[j] * od[k]
                             if combo_odd <= 1.0: combo_odd = 1.01 
                             prob = 1 / combo_odd
                             implied_prob_sum += prob
                             combos.append({"indices": (i, j, k), "odds": combo_odd, "prob": prob})
                
                constant_return = total_budget / implied_prob_sum
                net_profit = constant_return - total_budget
                roi = (net_profit / total_budget) * 100
                
                st.success(f"💎 Гарантированная Выплата (Payout): {constant_return:.2f} RUB")
                col_res1, col_res2 = st.columns(2)
                col_res1.metric("Чистая Прибыль (Net Profit)", f"{net_profit:.2f} RUB")
                col_res2.metric("ROI", f"{roi:.2f}%")
                
                results_data = []
                o1_names, o2_names, o3_names = st.session_state['express_data']['outcomes_1'], st.session_state['express_data']['outcomes_2'], st.session_state['express_data']['outcomes_3']
                
                for c in combos:
                    req_stake = constant_return / c['odds']
                    idx1, idx2, idx3 = c['indices'][0], c['indices'][1] - 3, c['indices'][2] - 6
                    name1 = o1_names[idx1] if idx1 < len(o1_names) else "?"
                    name2 = o2_names[idx2] if idx2 < len(o2_names) else "?"
                    name3 = o3_names[idx3] if idx3 < len(o3_names) else "?"
                    
                    results_data.append({
                        "Вариант": f"{name1} + {name2} + {name3}",
                        "Коэфф.": f"{c['odds']:.2f}",
                        "Сумма Ставки (RUB)": f"{req_stake:.0f}",
                        "Возможная Выплата": f"{req_stake * c['odds']:.2f}",
                        "Чистая Прибыль": f"{(req_stake * c['odds']) - total_budget:.2f}"
                    })
                
                st.write("### 📋 Распределение Ставок:")
                st.dataframe(pd.DataFrame(results_data), use_container_width=True)
                st.session_state['last_roi'] = f"Const Profit: {net_profit:.0f}"
                st.session_state['current_stakes'] = [constant_return / c['odds'] for c in combos]

        # Save to History
        if st.button("💾 Save to History"):
             import time
             try:
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
                     save_history(HistoryItem(**item_data))
                     st.success("Saved to Backtest/History!")
                 else:
                     requests.post(f"{API_URL}/save_history", json=item_data)
                     st.success("Saved to Backtest/History!")
             except Exception as e:
                 st.error(f"Save failed: {e}")

        should_generate = True
    else:
        bet_mode = "1X2"
        should_generate = st.button("Generate Variations")
    
    # Trigger Generation
    if should_generate:
        if 'generated_variations' not in st.session_state or st.button("Re-Generate"):
             import itertools
             # Simple generation for now
             if is_transferred:
                 st.session_state['generated_variations'] = list(itertools.product(o1, o2, o3))
             else:
                 st.info("Manual generation not fully implemented in refactor (add ExpressGenerator if needed)")
                 st.session_state['generated_variations'] = []

    # RENDER VARIATIONS checklist ...
    variations = st.session_state.get('generated_variations', [])
    if variations:
        st.success(f"Сгенерировано {len(variations)} вариантов")
        
        # Display Legend
        ed = st.session_state.get('express_data', {})
        meta1, meta2, meta3 = ed.get('m1_meta', {}), ed.get('m2_meta', {}), ed.get('m3_meta', {})
        
        # Helper Clean
        def clean_match_name(m):
             import re
             m = re.sub(r'\d{4}-\d{2}-\d{2}', '', m)
             m = re.sub(r'\d{2}-\d{2}', '', m)
             if " vs " in m: m = m.replace(" vs ", " - ")
             return m.strip()
        
        n1, n2, n3 = clean_match_name(m1), clean_match_name(m2), clean_match_name(m3)
        stakes_list = st.session_state.get('current_stakes', [])
        show_stakes = len(stakes_list) == len(variations)

        st.markdown("### 📋 Чек-лист Вариантов:")
        for i, v in enumerate(variations):
            bet_str = f"**1️⃣ {n1}**: {v[0]}   |   **2️⃣ {n2}**: {v[1]}   |   **3️⃣ {n3}**: {v[2]}"
            if show_stakes: bet_str += f"   💰 **{stakes_list[i]:.0f} ₽**"
            key = f"var_{i}"
            is_checked = st.session_state.get(key, False)
            label = f"~~🎫 Вариант #{i+1}:  {bet_str}~~" if is_checked else f"🎫 Вариант #{i+1}:  {bet_str}"
            st.checkbox(label, key=key)

        # Telegram Notification (REFACTORED SECTION)
        if is_transferred and st.button("📲 Отправить в Telegram"):
             try:
                 with st.spinner("⏳ Генерация HTML..."):
                     import time
                     from app.utils import generate_express_html, upload_to_beget, send_telegram_message
                     
                     timestamp = int(time.time())
                     filename = f"express_{timestamp}.html"
                     
                     html_content = generate_express_html(
                         m1, m2, m3, 
                         variations, 
                         stakes_list,
                         meta1, meta2, meta3, 
                         timestamp
                     )
                     
                     link = upload_to_beget(filename, html_content)
                     
                     if link:
                         st.success(f"Загружено! Ссылка: {link}")
                         st.markdown(f"[Открыть]({link})")
                         
                         msg = f"🆕 **Новый Экспресс (Manual)**\n📅 {meta1.get('date', 'Today')}\n\n🌍 **Ссылка:** {link}"
                         
                         tg_token = os.environ.get("TG_BOT_TOKEN")
                         tg_chat = os.environ.get("TG_CHAT_ID")
                         if tg_token and tg_chat:
                             send_telegram_message(tg_token, tg_chat, msg)
                             st.info("Telegram notification sent.")
                         else: 
                             try:
                                 notify_telegram(NotifyRequest(message=msg))
                             except: pass
                     else:
                         st.error("Upload failed.")
             except Exception as e:
                 st.error(f"Error: {e}")

with tab_ai:
    with st.expander("🤖 AI Анализатор", expanded=True):
        col1, col2 = st.columns([3,1])
        matches_input = col1.text_area("Матчи:", height=150)
        model_choice = col2.selectbox("AI Модель", ["Perplexity Sonar", "GPT-4o Mini"])
        
        if st.button("🚀 Анализировать") and matches_input.strip():
            with st.spinner("Thinking..."):
                raw_lines = [m.strip() for m in matches_input.strip().split('\n') if m.strip()]
                matches = [] 
                # Simple parser for now
                for line in raw_lines:
                    if '\t' in line:
                         parts = [p.strip() for p in line.split('\t') if p.strip()]
                         if len(parts) >= 5: matches.append(f"{parts[3]} vs {parts[4]}")
                         else: matches.append(f"{parts[-2]} vs {parts[-1]}")
                    else:
                         matches.append(line)
                
                try:
                    analysis_text = ""
                    if USE_INTERNAL_API:
                         req = AnalyzeRequest(matches=matches, model=model_choice)
                         res = analyze_express(req)
                         analysis_text = res.get("analysis", "")
                    else:
                         requests.post(f"{API_URL}/analyze_express", json={"matches":matches, "model":model_choice})
                    
                    if analysis_text:
                        st.session_state['last_analysis'] = analysis_text
                        st.session_state['analyzed_matches'] = matches
                        st.markdown(analysis_text)
                except Exception as e: st.error(f"Error: {e}")

        # --- Tab for AI History ---
        st.write("---")
        with st.expander("📜 История AI Анализов"):
             if st.button("🔄 Обновить Историю"): st.rerun()
             try:
                 hist_data = []
                 if USE_INTERNAL_API:
                     from app.main import get_ai_history_endpoint
                     hist_data = get_ai_history_endpoint()
                 else:
                     # For external API (not currently used in monolithic but good practice)
                     pass

                 if not hist_data:
                     st.info("История пуста.")
                 else:
                     for idx, item in enumerate(hist_data):
                         date_str = item.get('date_str', 'N/A')
                         matches_short = ", ".join([m.split('vs')[0] for m in item.get('matches', [])])
                         
                         with st.container():
                             c1, c2 = st.columns([4, 1])
                             c1.markdown(f"**{date_str}** | {matches_short}...")
                             if c2.button(f"👁️ View #{idx}"):
                                 st.session_state['last_analysis'] = item['analysis']
                                 st.session_state['analyzed_matches'] = item['matches']
                                 st.success("Loaded from History!")
             except Exception as e:
                 st.error(f"History load error: {e}")

        if 'last_analysis' in st.session_state:
            if st.button("🔄 Перенести в Редактор Экспрессов"):
                # Simplified Parsing Logic
                import re
                analysis = st.session_state['last_analysis']
                blocks = analysis.split('⚽')
                if len(blocks) < 2: blocks = analysis.split('\n\n')
                
                parsed_outcomes = []
                matched_meta = []
                
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
                    
                    u_out = []
                    [u_out.append(x) for x in outcomes if x not in u_out]
                    if "ЧЕТ" not in u_out: u_out.insert(0, "ЧЕТ")
                    while len(u_out) < 3: u_out.append("ЧЕТ")
                    
                    parsed_outcomes.append(u_out[:3])
                    
                    dm = re.search(r'📅.*?: (.*)', block)
                    rm = re.search(r'📝.*?: (.*)', block)
                    matched_meta.append({'date': dm.group(1).strip() if dm else '', 'reason': rm.group(1).strip() if rm else ''})
                
                if len(parsed_outcomes) >= 3:
                     metas = matched_meta + [{'date':'', 'reason':''}]*3
                     m_names = st.session_state['analyzed_matches']
                     st.session_state['express_data'] = {
                        'm1_name': m_names[0] if len(m_names)>0 else "M1", 'm1_meta': metas[0],
                        'm2_name': m_names[1] if len(m_names)>1 else "M2", 'm2_meta': metas[1],
                        'm3_name': m_names[2] if len(m_names)>2 else "M3", 'm3_meta': metas[2],
                        'outcomes_1': parsed_outcomes[0],
                        'outcomes_2': parsed_outcomes[1],
                        'outcomes_3': parsed_outcomes[2]
                     }
                     st.success(f"Transferred {len(parsed_outcomes)} matches!")

with tab4:
    st.subheader("📚 История Анализов (Backtest)")
    col1, col2 = st.columns([1, 1])
    if col1.button("🔄 Обновить"): st.rerun()
    if col2.button("🗑️ Удалить ВСЕ", type="primary"):
        if USE_INTERNAL_API: delete_history(DeleteHistoryRequest(delete_all=True))
        st.success("Cleared!")
        st.rerun()

    history = []
    if USE_INTERNAL_API: history = get_history()
    
    for item in reversed(history):
        with st.expander(f"📅 {item.get('date')} | Matches: {len(item.get('matches',[]))}"):
             st.json(item)
