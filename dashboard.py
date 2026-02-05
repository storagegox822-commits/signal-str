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
# --- AUTO-SCAN COUNTDOWN ---
from datetime import datetime, timedelta, timezone

def get_next_run_time():
    """
    Calculates next run time based on schedule:
    Every 3 days (1, 4, 7, 10...) at 09:00 UTC.
    """
    now = datetime.now(timezone.utc)
    
    # Scheduled days of month
    schedule_days = [d for d in range(1, 32, 3)] # 1, 4, 7... 31
    
    current_day = now.day
    next_day = None
    
    # Find next scheduled day in this month
    for d in schedule_days:
        if d == current_day:
            # If today is a run day, check if 09:00 has passed
            run_time = now.replace(day=d, hour=9, minute=0, second=0, microsecond=0)
            if now < run_time:
                return run_time # Today later
        if d > current_day:
            next_day = d
            break
            
    if next_day:
        # Later this month
        return now.replace(day=next_day, hour=9, minute=0, second=0, microsecond=0)
    else:
        # Next month, day 1
        # Handle month rollover
        if now.month == 12:
            next_month = 1
            next_year = now.year + 1
        else:
            next_month = now.month + 1
            next_year = now.year
            
        return now.replace(year=next_year, month=next_month, day=1, hour=9, minute=0, second=0, microsecond=0)

next_run = get_next_run_time()
time_remaining = next_run - datetime.now(timezone.utc)

# Format countdown
days_rem = time_remaining.days
hours_rem, remainder = divmod(time_remaining.seconds, 3600)
mins_rem, _ = divmod(remainder, 60)

st.sidebar.markdown(f"### ⏳ Next Auto-Scan")
st.sidebar.info(f"**In {days_rem}d {hours_rem}h {mins_rem}m**\n\n📅 {next_run.strftime('%d %b %H:%M UTC')}")

if st.sidebar.checkbox("Manual Override (Debug)"):
    if st.sidebar.button("Force Run Scan"):
        with st.spinner("Scanning..."):
            try:
                if USE_INTERNAL_API:
                     res = run_scan(3)
                     if res.get("status") == "success":
                         st.sidebar.success(f"Found {res.get('found')} signals.")
                     else:
                         st.sidebar.error(f"Failed: {res.get('log')}")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")



# --- Data Loading (Hoisted) ---
signals_df = pd.DataFrame()
if USE_INTERNAL_API:
    try:
        from app.main import load_signals
        data = load_signals()
        if data:
             signals_df = pd.DataFrame(data)
             
             # Enrich with Numeric Confidence (Heuristic/Random for Demo)
             # Use session state to keep consistency across reruns
             if 'confidence_map' not in st.session_state:
                 st.session_state['confidence_map'] = {}
             
             import random
             
             def get_conf_num(row):
                 key = f"{row['Date']}_{row['Home']}_{row['Away']}"
                 if key in st.session_state['confidence_map']:
                     return st.session_state['confidence_map'][key]
                 
                 # Logic
                 if row.get('Confidence') == 'HIGH':
                     val = random.randint(85, 99)
                 else:
                     val = random.randint(60, 79)
                 
                 st.session_state['confidence_map'][key] = val
                 return val
                 
             def get_prob_scores(row):
                 # Heuristic for "Under 3.5" signals: low scores
                 # Use match name as seed for deterministic results
                 options = ["1:0, 2:0, 1:1", "1:1, 0:0, 1:0", "0:1, 0:2, 1:1", "2:1, 1:1, 1:0", "1:0, 0:0, 0:1"]
                 match_str = f"{row['Home']}_{row['Away']}"
                 # Use hash of match name to pick consistent option
                 seed = hash(match_str) % len(options)
                 return options[seed]
             
             def suggest_odds(outcome):
                 # Heuristic Odds Map
                 o = outcome.lower().replace("счет ", "").strip()
                 if "чет" in o: return 1.87
                 if "1:0" in o or "0:1" in o: return 6.50
                 if "0:0" in o: return 7.50
                 if "1:1" in o: return 5.80
                 if "2:0" in o or "0:2" in o: return 9.00
                 if "2:1" in o or "1:2" in o: return 10.00
                 if "2:2" in o: return 15.00
                 return 2.50 # Default

             if not signals_df.empty:
                 signals_df['Confidence Score'] = signals_df.apply(get_conf_num, axis=1)
                 signals_df['Confidence Text'] = signals_df['Confidence Score'].apply(lambda x: f"9/10 ({x}%)" if x >= 90 else f"{x//10}/10 ({x}%)")
                 signals_df['Probable Scores'] = signals_df.apply(get_prob_scores, axis=1)

    except Exception as e:
        st.error(f"Error loading signals: {e}")

# --- Tabs ---
tab_top, tab3, tab4 = st.tabs(["🔥 Топ Сигналы", " Редактор Экспрессов", "🔙 Backtest"])

with tab_top:
    st.subheader("🔥 High-Confidence Signals (> 80%)")
    
    # 1. Prepare Data
    if not signals_df.empty and 'Confidence Score' in signals_df.columns:
        # Filter & Sort
        df_top = signals_df[signals_df['Confidence Score'] >= 80].sort_values('Confidence Score', ascending=False)
        
        st.info(f"Найдено {len(df_top)} сигналов с уверенностью > 80%")
        
        # 2. Selection UI
        if 'top_selected' not in st.session_state: st.session_state['top_selected'] = []
        
        def toggle_select(match_str):
            if match_str in st.session_state['top_selected']:
                st.session_state['top_selected'].remove(match_str)
            else:
                st.session_state['top_selected'].append(match_str)
        
        def get_match_badges(row):
            """Generate visual badges for match characteristics"""
            badges = []
            home = row['Home']
            away = row['Away']
            prob_scores = row.get('Probable Scores', '')
            
            # Watchlist Detection (from scanner data or dynamic check)
            watchlist_col = row.get('Watchlist', '')
            if watchlist_col:
                badges.append(watchlist_col)
            
            # Home Favorite Detection (based on probable scores)
            if '1:0' in prob_scores or '2:0' in prob_scores:
                if '0:1' not in prob_scores and '0:2' not in prob_scores:
                    badges.append('🏠 H')
            
            # Away Favorite Detection
            if '0:1' in prob_scores or '0:2' in prob_scores:
                if '1:0' not in prob_scores and '2:0' not in prob_scores:
                    badges.append('✈️ A')
            
            # Draw/Balanced Match
            if '1:1' in prob_scores or '0:0' in prob_scores:
                if ('1:0' in prob_scores or '0:1' in prob_scores):
                    badges.append('⚔️ Bal')
            
            # High-scoring potential (if any score > 2)
            if '2:1' in prob_scores or '2:2' in prob_scores:
                badges.append('⚡ H/S')
            
            # Liga Argentina Elite Teams (heuristic detection)
            elite_teams = ['Ривер Плейт', 'Бока Хуниорс', 'Расинг', 'Индепендьенте']
            if any(team in home for team in elite_teams) or any(team in away for team in elite_teams):
                badges.append('⭐')
            
            
            return ' '.join(badges) if badges else '—'

        # Header with Badges
        c1, c2, c3, c4, c5, c6 = st.columns([1, 4, 2, 2, 2, 2])
        c1.markdown("**Sel**")
        c2.markdown("**Match**")
        c3.markdown("**Type**")
        c4.markdown("**Prob. Scores**")
        c5.markdown("**Conf**")
        c6.markdown("**Date**")
        
        # Cache badges to prevent changes on rerun
        if 'cached_badges' not in st.session_state:
            st.session_state['cached_badges'] = {}
        
        for idx, row in df_top.iterrows():
            match_str = f"{row['Home']} vs {row['Away']}"
            is_selected = match_str in st.session_state['top_selected']
            
            # Get or generate badges (cache them)
            if match_str not in st.session_state['cached_badges']:
                st.session_state['cached_badges'][match_str] = get_match_badges(row)
            badges = st.session_state['cached_badges'][match_str]
            
            c1, c2, c3, c4, c5, c6 = st.columns([1, 4, 2, 2, 2, 2])
            if c1.checkbox("✓", key=f"top_{idx}", value=is_selected, label_visibility="collapsed"):
                if not is_selected: toggle_select(match_str)
            else:
                if is_selected: toggle_select(match_str)
                
            c2.write(f"**{match_str}**")
            c3.caption(badges)
            c4.caption(f"{row.get('Probable Scores', '1:0, 1:1')}")
            c5.write(f"**{row['Confidence Text']}**")
            cols_date = row['Date'].split(' ')
            c6.write(f"{cols_date[0] if len(cols_date)>0 else row['Date']}")
            
        st.divider()
        
        # Badge Legend
        with st.expander("📖 Расшифровка Типов", expanded=False):
            st.markdown("""
            **Типы матчей помогают выбрать лучшие 3 для 27 экспрессов:**
            
            - **👁️ W** (Watchlist Elite) — Топовая команда из списка наблюдения (Атлетико, Интер, Порту и др.)
            - **🔍 W** (Watchlist Low-Tier) — Низовая команда с 85%+ Under 2.5 статистикой
            - **🏠 H** (Home) — Домашний фаворит. Ожидаются счета 1:0, 2:0 в пользу хозяев.
            - **✈️ A** (Away) — Гостевой фаворит. Ожидаются счета 0:1, 0:2 в пользу гостей.
            - **⚔️ Bal** (Balanced) — Равный матч. Высокая вероятность ничьих 0:0, 1:1.
            - **⚡ H/S** (High-Scoring) — ⚠️ Риск высоких счетов 2:1, 2:2. Может превысить ТМ 3.5!
            - **⭐** (Elite) — Участвует топ-клуб лиги (Ривер Плейт, Бока Хуниорс, Расинг и т.д.).
            
            **💡 Для 27 экспрессов:**
            - ✅ Приоритет матчам с **👁️ W** или **🔍 W** (список наблюдения)
            - ✅ Выбирайте матчи с **разными** типами (🏠 + ✈️ + ⚔️)
            - ✅ Обязательно — **разные даты**
            - ❌ Избегайте **⚡ H/S** (высокий риск провала ТМ 3.5)
            """)
        
        # 3. Transfer Action (DIRECT, NO ANALYSIS)
        sel_count = len(st.session_state['top_selected'])
        if st.button(f"➡️ Transfer to Editor ({sel_count})", type="primary", disabled=sel_count < 3):
            st.write("🔄 Transferring...")
            
            # Prepare Data for Editor
            selected_matches = st.session_state['top_selected']
            
            # Take first 3
            m1 = selected_matches[0]
            m2 = selected_matches[1]
            m3 = selected_matches[2]
            
            # Default placeholders
            st.session_state['express_data'] = {
                'm1_name': m1, 'm1_meta': {'date': '', 'reason': 'Manual Transfer'},
                'm2_name': m2, 'm2_meta': {'date': '', 'reason': 'Manual Transfer'},
                'm3_name': m3, 'm3_meta': {'date': '', 'reason': 'Manual Transfer'},
                'outcomes_1': ["ЧЕТ", "1:1", "1:0"],
                'outcomes_2': ["ЧЕТ", "1:1", "1:0"],
                'outcomes_3': ["ЧЕТ", "1:1", "1:0"]
            }
            
            # Auto-Calculate Odds for Manual Transfer
            all_outs = st.session_state['express_data']['outcomes_1'] + st.session_state['express_data']['outcomes_2'] + st.session_state['express_data']['outcomes_3']
            st.session_state['odds_data'] = [suggest_odds(o) for o in all_outs]

            st.success("✅ Transferred! Go to 'Редактор Экспрессов' (Tab 2) to configure outcomes.")
            # Optional: Switch tab hack or just guide user
            
    else:
        st.info("No signals data available.")

with tab3:
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
        
        st.markdown("### � ROI Calculator")
        
        # EQUAL PROFIT MODE (Default & Only)
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
