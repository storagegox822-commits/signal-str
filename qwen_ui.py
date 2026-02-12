
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
