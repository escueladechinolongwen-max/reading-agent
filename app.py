import streamlit as st
import asyncio
import edge_tts
import os
import time
import base64
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- 1. 核心配置 ---
st.set_page_config(page_title="Long Wen Reading Pro", page_icon="🐼", layout="wide", initial_sidebar_state="expanded")
MY_API_KEY = os.environ.get("GOOGLE_API_KEY")
TARGET_MODEL = 'models/gemini-2.5-flash'

# 🌍 语言包
UI_TEXT = {
    "Español": { 
        "instr": "✍️ Escribe aquí para practicar...", 
        "gen_btn": "Generar Lección ✨", 
        "topic": "Tema", "level": "Nivel", "keywords": "Palabras",
        "loading": "Creando lección..."
    },
    "English": { 
        "instr": "✍️ Type here to practice...", 
        "gen_btn": "Generate Lesson ✨", 
        "topic": "Topic", "level": "Level", "keywords": "Keywords",
        "loading": "Creating lesson..."
    }
}

# --- 2. CSS 布局 (修复显示问题) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #f8fafc;
        overflow: hidden !important; 
        height: 100vh;
    }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0 !important;
        max-width: 95% !important;
        height: 100vh;
        display: flex;
        flex-direction: column;
    }

    .header-area { flex: 0 0 auto; text-align: center; margin-bottom: 10px; }
    .main-title { font-family: 'Noto Serif SC'; font-weight: 900; color: #334155; font-size: 1.5rem; }

    /* 滚动阅读区 */
    .scroll-container {
        flex: 1 1 auto;
        overflow-y: auto;
        padding: 20px;
        background: white;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 80px; 
        display: flex;
        flex-direction: column;
        gap: 0px; /* 让行与行更紧凑 */
    }

    /* 行容器 */
    .row-container {
        display: flex;
        border-bottom: 1px dashed #f1f5f9;
        padding: 15px;
        align-items: flex-start;
        transition: background 0.3s ease;
    }

    /* 左侧：翻译 */
    .left-box {
        width: 30%;
        padding-right: 20px;
        border-right: 2px solid #f1f5f9;
        color: #059669;
        font-size: 0.95rem;
        font-style: italic;
        text-align: right;
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }

    /* 右侧：汉字 */
    .right-box {
        width: 70%;
        padding-left: 20px;
        display: flex;
        flex-wrap: wrap; 
        gap: 5px;
        align-items: flex-end;
    }

    /* 字体 */
    ruby { font-size: 28px; font-weight: 900; color: #1e293b; ruby-position: under; line-height: 2.2; }
    rt { font-size: 13px; color: #64748b; font-weight: 600; transform: translateY(-5px); }
    
    .role-tag {
        font-size: 0.8rem; background: #e2e8f0; color: #64748b;
        padding: 2px 6px; border-radius: 4px; margin-right: 8px;
        height: fit-content; margin-top: 10px;
    }

    /* 底部固定 */
    .fixed-bottom {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: white; padding: 15px 30px;
        border-top: 3px solid #3b82f6; z-index: 999;
        box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .highlight-active { background-color: #f0f9ff; }
</style>
""", unsafe_allow_html=True)

# --- 3. AI 逻辑 ---
def call_ai(topic, level, keywords):
    if not MY_API_KEY: return None
    try:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel(TARGET_MODEL)
        safety = {HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE}

        prompt = f"""
        Act as a JSON API. Create a Chinese dialogue (4-6 lines) between '美美' (Female) and '大卫' (Male).
        Topic: {topic}. Level: {level}. Keywords: {keywords}.
        
        RULES:
        1. Include standard punctuation (，。？！).
        2. Output JSON ARRAY only.
        Format: [{{"r": "美美", "t": [["你", "nǐ"], ["好", "hǎo"], ["，", ""]], "tr_es": "Hola", "tr_en": "Hi"}}]
        """
        response = model.generate_content(prompt, safety_settings=safety)
        text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)
    except Exception as e:
        st.error(str(e))
        return None

# --- 4. 音频 ---
async def make_audio(data, filename):
    ts = []
    curr = 0.0
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(data):
            voice = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
            raw = "".join([p[0] for p in line.get("t", [])])
            dur = len(raw) * 0.26 + 0.5 
            ts.append({"start": curr, "end": curr + dur, "role": line["r"]})
            try:
                comm = edge_tts.Communicate(raw, voice)
                temp_f = f"tmp_{int(time.time())}_{i}.mp3"
                await comm.save(temp_f)
                with open(temp_f, 'rb') as f: final_file.write(f.read())
                os.remove(temp_f)
            except: pass
            curr += dur
    return ts

# --- 5. 播放器 ---
def get_player_html(file_path, ts):
    with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    return f"""
    <div style="width:100%; display:flex; justify-content:center; margin-bottom:10px;">
        <audio id="p" controls src="data:audio/mp3;base64,{b64}" style="width:400px; height:35px;"></audio>
    </div>
    <script>
        const p = document.getElementById('p');
        const ts = {json.dumps(ts)};
        p.ontimeupdate = () => {{
            const cur = p.currentTime;
            ts.forEach((t, i) => {{
                const el = window.parent.document.getElementById('row-'+i);
                if (el) {{
                    if (cur >= t.start && cur < t.end) {{
                        el.classList.add("highlight-active");
                        el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }} else {{
                        el.classList.remove("highlight-active");
                    }}
                }}
            }});
        }};
    </script>
    """

def main():
    if "current_data" not in st.session_state: st.session_state.current_data = None
    if "audio_file" not in st.session_state: st.session_state.audio_file = ""

    with st.sidebar:
        st.header("🐼 Settings")
        ui_lang = st.selectbox("Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        topic = st.text_input(ui["topic"], "School")
        level = st.selectbox(ui["level"], ["HSK 1", "HSK 2", "HSK 3"])
        keys = st.text_input(ui["keywords"], "书, 学习")
        if st.button(ui["gen_btn"]):
            with st.spinner(ui["loading"]):
                res = call_ai(topic, level, keys)
                if res:
                    st.session_state.current_data = res
                    st.session_state.audio_file = ""
                    st.rerun()

    st.markdown('<div class="header-area"><div class="main-title">Long Wen Reading Pro</div></div>', unsafe_allow_html=True)

    if st.session_state.current_data:
        if not st.session_state.audio_file:
            fname = f"audio_{int(time.time())}.mp3"
            st.session_state.ts = asyncio.run(make_audio(st.session_state.current_data, fname))
            st.session_state.audio_file = fname
        
        if os.path.exists(st.session_state.audio_file):
            st.components.v1.html(get_player_html(st.session_state.audio_file, st.session_state.ts), height=60)

        # 🔵 重点修复：构建 HTML 字符串
        full_html = '<div class="scroll-container">'
        
        for idx, line in enumerate(st.session_state.current_data):
            trans = line.get("tr_es", "") if ui_lang == "Español" else line.get("tr_en", "")
            
            # 开始构建这一行
            row_html = f"""
            <div class="row-container" id="row-{idx}">
                <div class="left-box">{trans}</div>
                <div class="right-box">
                    <span class="role-tag">{line['r']}</span>
            """
            
            # 添加汉字拼音
            for char, py in line.get("t", []):
                row_html += f'<ruby>{char}<rt>{py}</rt></ruby>'
            
            # 闭合标签
            row_html += """
                </div>
            </div>
            """
            full_html += row_html
            
        full_html += '</div>'
        
        # 🔵 重点修复：使用 unsafe_allow_html=True 渲染
        st.markdown(full_html, unsafe_allow_html=True)
        
        # 底部固定区
        st.markdown(f"""
        <div class="fixed-bottom">
            <div style="font-weight:bold; color:#3b82f6; margin-bottom:5px;">{ui['instr']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.text_input("input", label_visibility="collapsed", placeholder="Type here...")
        st.markdown("""
        <script>
            const inputFrame = window.parent.document.querySelector('.stTextInput');
            const footer = window.parent.document.querySelector('.fixed-bottom');
            if(inputFrame && footer) { footer.appendChild(inputFrame); }
        </script>
        """, unsafe_allow_html=True)

    else:
        st.info("👈 Please enter settings and click Generate")

if __name__ == "__main__":
    main()
