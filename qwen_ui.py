
import streamlit.components.v1 as components

def qwen_component():
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://js.puter.com/v2/"></script>
        <style>
            body { font-family: sans-serif; padding: 10px; }
            .btn {
                background-color: #ff4b4b;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
                margin-right: 10px;
            }
            .btn:hover { opacity: 0.9; }
            .btn-secondary { background-color: #555; }
            #output {
                margin-top: 15px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background: #f9f9f9;
                white-space: pre-wrap;
                min-height: 100px;
            }
            .loading { color: #888; font-style: italic; }
        </style>
    </head>
    <body>
        <h3>🧠 Qwen AI Assistant (via Puter.js)</h3>
        
        <!-- Feature 1: Search -->
        <div style="margin-bottom: 20px;">
            <h4>🔍 Search Popular "Under" Matches</h4>
            <p>Find popular matches with high probability of Under 3.5 goals for next 3 days.</p>
            <button class="btn" onclick="searchMatches()">Search Next 3 Days</button>
        </div>

        <!-- Feature 2: Analyzer -->
        <div style="margin-bottom: 20px;">
            <h4>🧪 Match Analyzer</h4>
            <textarea id="matchesInput" rows="4" style="width: 100%; margin-bottom: 10px;" placeholder="Enter matches (e.g., Real Madrid vs Barcelona)"></textarea>
            <button class="btn btn-secondary" onclick="analyzeMatches()">Analyze with Qwen</button>
        </div>

        <div id="output">Output will appear here...</div>

        <script>
            async function searchMatches() {
                const output = document.getElementById('output');
                output.innerHTML = '<span class="loading">Searching via Qwen AI... please wait...</span>';
                
                try {
                    const prompt = "List 5 popular football matches happening in the next 3 days that are highly likely to have Under 3.5 goals. For each, give a short reason and estimated score. Return in clean text format.";
                    const resp = await puter.ai.chat(prompt);
                    output.innerText = resp;
                } catch (e) {
                    output.innerText = "Error: " + e.message;
                }
            }

            async function analyzeMatches() {
                const input = document.getElementById('matchesInput').value;
                if (!input) { alert("Please enter matches first."); return; }
                
                const output = document.getElementById('output');
                output.innerHTML = '<span class="loading">Analyzing via Qwen AI... please wait...</span>';
                
                try {
                    const prompt = "Analyze these matches for Under 3.5 Goals outcomes. Provide strictly the most probable 3 scores (e.g. 1:1, 1:0, 0:0) for each match:\\n\\n" + input;
                    const resp = await puter.ai.chat(prompt);
                    output.innerText = resp;
                } catch (e) {
                    output.innerText = "Error: " + e.message;
                }
            }
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=600, scrolling=True)


def qwen_batch_component(matches, autostart=False):
    """
    Component to analyze a batch of matches using Qwen AI (Puter.js)
    matches: List of match dicts
    autostart: If True, analysis starts automatically.
    """
    matches_json = json.dumps(matches)
    matches_count = len(matches)
    
    autostart_script = ""
    if autostart:
        autostart_script = "window.onload = function() { startAnalysis(); };"
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://js.puter.com/v2/"></script>
        <style>
            body {{ font-family: sans-serif; padding: 10px; font-size: 14px; background-color: #0e1117; color: white; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #333; padding: 8px; text-align: left; }}
            th {{ background-color: #262730; }}
            .match-name {{ font-weight: bold; color: #ffbd45; }}
            .loading {{ color: #ccc; font-style: italic; }}
            a {{ color: #4da6ff; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .btn {{
                background-color: #ff4b4b;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
                margin-bottom: 20px;
            }}
            .btn:hover {{ opacity: 0.9; }}
        </style>
    </head>
    <body>
        <h3>🧠 Qwen AI Analysis (Background Process)</h3>
        <button class="btn" onclick="startAnalysis()">▶️ Start Analysis ({matches_count} Matches)</button>
        <div id="status">Ready. Click start.</div>
        
        <table id="resultsTable">
            <thead>
                <tr>
                    <th>Sel</th>
                    <th>Match</th>
                    <th>Type</th>
                    <th>Conf</th>
                    <th>Prob. Scores</th>
                    <th>H2H</th>
                    <th>Date</th>
                </tr>
            </thead>
            <tbody>
                <!-- Rows will be injected here -->
            </tbody>
        </table>

        <script>
            const matches = {matches_json};
            {autostart_script}
            
            async function startAnalysis() {{
                const status = document.getElementById('status');
                const tbody = document.querySelector('#resultsTable tbody');
                tbody.innerHTML = ''; // Clear
                
                status.innerText = "Analyzing " + matches.length + " matches via Qwen AI...";
                
                for (let i = 0; i < matches.length; i++) {{
                    const m = matches[i];
                    const rowId = 'row-' + i;
                    
                    // Creates row skeleton
                    const tr = document.createElement('tr');
                    tr.id = rowId;
                    tr.innerHTML = `
                        <td><input type="checkbox"></td>
                        <td><span class="match-name">${{m.Home}} vs ${{m.Away}}</span></td>
                        <td class="type-cell"><span class="loading">...</span></td>
                        <td class="conf-cell"><span class="loading">...</span></td>
                        <td class="score-cell"><span class="loading">...</span></td>
                        <td><a href="https://www.google.com/search?q=${{encodeURIComponent(m.Home + ' vs ' + m.Away + ' h2h')}}" target="_blank">📊 Stats</a></td>
                        <td>${{m.Date}}</td>
                    `;
                    tbody.appendChild(tr);
                    
                    // Run AI (Prompt Engineering)
                    try {{
                        // We use a simpler prompt to ensure speed/reliability
                         const promptSimple = `Analyze football match ${{m.Home}} vs ${{m.Away}} for Under 3.5 goals potential. 
                         Return ONLY a JSON string with keys: type, conf, scores.
                         Example: {{ "type": "🏠 H ⚔️ Bal ⭐", "conf": "7/10 (70%)", "scores": "1:1, 0:0, 1:0" }}`;

                        const resp = await puter.ai.chat(promptSimple);
                        
                        let type = "—"; let conf = "—"; let scores = "—";
                        
                        // heuristic parsing if json fails or text is mixed
                        if (resp.includes("{{")) {{
                             try {{
                                 const jsonPart = resp.substring(resp.indexOf("{{"), resp.lastIndexOf("}}")+1);
                                 const data = JSON.parse(jsonPart);
                                 type = data.type || type;
                                 conf = data.conf || conf;
                                 scores = data.scores || scores;
                             }} catch(e) {{
                                 // fallback parsing
                                 if (resp.includes("Type:")) type = resp.split("Type:")[1].split("|")[0].trim();
                             }}
                        }} else {{
                             if (resp.includes("Type:")) type = resp.split("Type:")[1].split("|")[0].trim();
                             if (resp.includes("Conf:")) conf = resp.split("Conf:")[1].split("|")[0].trim();
                             if (resp.includes("Scores:")) scores = resp.split("Scores:")[1].trim();
                        }}
                        
                        // Update DOM
                        const rowEl = document.getElementById(rowId);
                        if(rowEl) {{
                            rowEl.querySelector('.type-cell').innerText = type;
                            rowEl.querySelector('.conf-cell').innerText = conf;
                            rowEl.querySelector('.score-cell').innerText = scores;
                        }}
                        
                    }} catch (e) {{
                        console.error(e);
                        const rowEl = document.getElementById(rowId);
                        if(rowEl) rowEl.querySelector('.type-cell').innerText = "Error";
                    }}
                    
                    // Small delay to be nice to Puter
                    await new Promise(r => setTimeout(r, 500));
                }}
                
                status.innerText = "Analysis Complete.";
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=800, scrolling=True)
