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

# 🌍 语言包 (新增了行数控制)
UI_TEXT = {
    "Español": { 
        "instr": "✍️ Escribe aquí para practicar...", 
        "gen_btn": "Generar Lección ✨", 
        "topic": "Tema", "level": "Nivel", "keywords": "Palabras",
        "lines": "Líneas (Longitud)",
        "loading": "✨ Creando magia...",
        "show_py": "Mostrar Pinyin", 
        "show_tr": "Mostrar Traducción",
        "refresh": "Regenerar Audio" 
    },
    "English": { 
        "instr": "✍️ Type here to practice...", 
        "gen_btn": "Generate Lesson ✨", 
        "topic": "Topic", "level": "Level", "keywords": "Keywords",
        "lines": "Lines (Length)",
        "loading": "✨ Creating magic...",
        "show_py": "Show Pinyin", 
        "show_tr": "Show Translation",
        "refresh": "Regenerate Audio"
    }
}

# --- 2. 🎨 CSS 完美对齐 & 防止误伤 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&family=Nunito:wght@700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFBF0 !important;
        font-family: 'Nunito', 'Noto Sans SC', sans-serif;
        overflow: hidden !important;
    }
    
    .block-container {
        padding-top: 50px !important;
        padding-bottom: 140px !important; 
        max-width: 1000px !important;
    }

    .main-title {
        text-align: center; color: #5D5650; font-weight: 800; 
        font-size: 2rem; letter-spacing: 1px; margin-bottom: 20px;
        text-shadow: 2px 2px 0px #FFEaa7;
    }

    /* ☁️ 阅读卡片 (严格锁定最大宽度 900px) */
    .scroll-container {
        background: #FFFFFF;
        border-radius: 25px;
        padding: 30px;
        box-shadow: 0 8px 20px rgba(235, 212, 180, 0.4);
        border: 2px solid #FFF5E0;
        height: 60vh; 
        overflow-y: auto;
        display: flex; flex-direction: column; gap: 15px;
        width: 100%; 
        max-width: 900px; 
        margin: 0 auto;
    }

    .cute-row {
        display: flex; align-items: flex-start; padding: 15px;
        border-bottom: 2px dashed #FFF0D4; transition: all 0.3s ease; border-radius: 12px;
    }
    .cute-row:hover { background-color: #FFFCF5; }

    .cute-avatar {
        background-color: #FFD166; color: #fff; width: 40px; height: 40px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 12px; font-weight: bold; margin-right: 15px; flex-shrink: 0;
        box-shadow: 2px 2px 0px #F4B860;
    }
    .avatar-dawei { background-color: #6FCF97; box-shadow: 2px 2px 0px #27AE60; }

    .cute-chinese { flex: 1; display: flex; flex-wrap: wrap; gap: 2px; align-items: flex-end; }
    ruby { font-size: 24px; font-weight: 700; color: #4A4A4A; ruby-position: under; line-height: 2.0; margin-right: 2px;}
    rt { font-size: 12px; color: #FF8BA7; font-weight: 600; font-family: sans-serif; }

    .cute-trans {
        width: 35%; padding-left: 20px; color: #AAB7B8; font-size: 0.9rem; font-style: italic;
        border-left: 2px solid #F0F3F4; display: flex; align-items: center; line-height: 1.4;
    }

    /* 🚀 底部固定层：使用 Wrapper 保证完美对齐 */
    .footer-wrapper {
        position: fixed; bottom: 30px; left: 0; width: 100%;
        display: flex; justify-content: center;
        pointer-events: none; /* 让空白处可以点击穿透 */
        z-index: 99999;
    }

    /* 真实的胶囊容器 (宽度与上方卡片严格一致) */
    .fixed-footer {
        width: calc(100% - 4rem); /* 减去两侧默认 padding */
        max-width: 900px; /* 与卡片保持同样的极值 */
        background-color: #FFFFFF;
        padding: 5px 20px;
        border-radius: 50px;
        box-shadow: 0 10px 25px rgba(255, 159, 28, 0.2);
        border: 3px solid #FFE5B4;
        pointer-events: auto; /* 恢复点击 */
        transition: all 0.3s ease;
    }
    
    .fixed-footer:focus-within {
        border-color: #FFD166;
        box-shadow: 0 10px 30px rgba(255, 159, 28, 0.3);
        transform: translateY(-2px);
    }

    /* 仅修改胶囊内部的输入框，绝不影响侧边栏 */
    .fixed-footer div[data-testid="stTextInput"] { margin-bottom: 0 !important; }
    .fixed-footer input {
        border: none !important; background-color: transparent !important; 
        font-size: 1.1rem !important; color: #5D5650 !important;
        box-shadow: none !important; padding: 10px !important;
    }

    .hide-pinyin rt { display: none !important; }
    .hide-trans .cute-trans { opacity: 0; }
    .active-highlight { background-color: #FFF8E1 !important; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# --- 3. AI 逻辑 ---
def call_ai(topic, level, keywords, num_lines):
    if not MY_API_KEY: return None
    try:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel(TARGET_MODEL)
        safety = {HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE}

        prompt = f"""
        Act as a JSON API. Create a Chinese dialogue between '美美' (Female) and '大卫' (Male).
        Topic: {topic}. Level: {level}. Keywords: {keywords}.
        
        CRITICAL RULES:
        1. Dialogue MUST be exactly {num_lines} lines long.
        2. YOU MUST INCLUDE PUNCTUATION (，。？！) in the text list.
        3. Treat punctuation as a character with empty pinyin "".
        4. Output JSON ARRAY only.
        
        Format Example: 
        [
            {{"r": "美美", "t": [["你", "nǐ"], ["好", "hǎo"], ["！", ""]], "tr_es": "¡Hola!", "tr_en": "Hello!"}}
        ]
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
            dur = len(raw) * 0.28 + 0.5 
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
    <div style="width:100%; text-align:center; margin-bottom:15px;">
        <audio id="p" controls src="data:audio/mp3;base64,{b64}" style="width:100%; max-width:400px; height:40px; border-radius:20px;"></audio>
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
                        el.classList.add("active-highlight");
                        el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }} else {{
                        el.classList.remove("active-highlight");
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
        
        # 🌟 新增：动态控制行数 (4 到 12 行，默认 6 行)
        num_lines = st.slider(ui["lines"], min_value=4, max_value=12, value=6, step=2)
        
        if st.button(ui["gen_btn"]):
            with st.spinner(ui["loading"]):
                res = call_ai(topic, level, keys, num_lines)
                if res:
                    st.session_state.current_data = res
                    st.session_state.audio_file = ""
                    st.rerun()
        
        st.divider()
        show_pinyin = st.toggle(ui["show_py"], value=True)
        show_trans = st.toggle(ui["show_tr"], value=True)
        
        if st.button(f"🔄 {ui['refresh']}"):
            st.session_state.audio_file = ""
            st.rerun()

    st.markdown('<div class="main-title">Reading Assistant Pro</div>', unsafe_allow_html=True)

    if st.session_state.current_data:
        if not st.session_state.audio_file:
            fname = f"audio_{int(time.time())}.mp3"
            st.session_state.ts = asyncio.run(make_audio(st.session_state.current_data, fname))
            st.session_state.audio_file = fname
        
        if os.path.exists(st.session_state.audio_file):
            st.components.v1.html(get_player_html(st.session_state.audio_file, st.session_state.ts), height=60)

        container_class = ""
        if not show_pinyin: container_class += " hide-pinyin"
        if not show_trans: container_class += " hide-trans"

        html_str = f'<div class="scroll-container {container_class}">'
        for idx, line in enumerate(st.session_state.current_data):
            trans = line.get("tr_es", "") if ui_lang == "Español" else line.get("tr_en", "")
            avatar_class = "cute-avatar"
            if line["r"] == "大卫": avatar_class += " avatar-dawei"
            
            hanzi_html = ""
            for char, py in line.get("t", []):
                hanzi_html += f'<ruby>{char}<rt>{py}</rt></ruby>'
            
            html_str += f'<div class="cute-row" id="row-{idx}"><div class="{avatar_class}">{line["r"][0]}</div><div class="cute-chinese">{hanzi_html}</div><div class="cute-trans">{trans}</div></div>'
        
        html_str += '</div>'
        st.markdown(html_str, unsafe_allow_html=True)
        
        # 底部框架准备
        st.markdown('<div class="footer-wrapper"><div class="fixed-footer"></div></div>', unsafe_allow_html=True)
        
        # 真实的练习输入框
        st.text_input("user_input", label_visibility="collapsed", placeholder=ui["instr"])
        
        # 🌟 精准搬运：只拿最后一个输入框，绝不碰侧边栏的关键词框
        st.markdown("""
        <script>
            const allInputs = window.parent.document.querySelectorAll('.stTextInput');
            const practiceInput = allInputs[allInputs.length - 1]; // 永远抓取最后一个
            const footerEl = window.parent.document.querySelector('.fixed-footer');
            if(practiceInput && footerEl) { footerEl.appendChild(practiceInput); }
        </script>
        """, unsafe_allow_html=True)

    else:
        st.info("👈 Please enter settings and click Generate")

if __name__ == "__main__":
    main()
