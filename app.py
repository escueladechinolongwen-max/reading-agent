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
        "instr": "✍️ Escribe aquí...", 
        "gen_btn": "Generar Lección ✨", 
        "topic": "Tema", "level": "Nivel", "keywords": "Palabras",
        "loading": "✨ Creando magia...",
        "show_py": "Mostrar Pinyin", 
        "show_tr": "Mostrar Traducción",
        "refresh": "Regenerar Audio" 
    },
    "English": { 
        "instr": "✍️ Type here...", 
        "gen_btn": "Generate Lesson ✨", 
        "topic": "Topic", "level": "Level", "keywords": "Keywords",
        "loading": "✨ Creating magic...",
        "show_py": "Show Pinyin", 
        "show_tr": "Show Translation",
        "refresh": "Regenerate Audio"
    }
}

# --- 2. 🎨 CSS 完美对齐版 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&family=Nunito:wght@700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFBF0 !important;
        font-family: 'Nunito', 'Noto Sans SC', sans-serif;
        overflow: hidden !important;
    }
    
    /* 1. 修复顶部显示不全的问题 */
    .block-container {
        padding-top: 60px !important; /* 增加顶部空间 */
        padding-bottom: 120px !important;
        max-width: 1000px !important; /* 统一最大宽度 */
    }

    /* 标题样式 */
    .main-title {
        text-align: center; color: #5D5650; font-weight: 800; 
        font-size: 2rem; letter-spacing: 1px; margin-bottom: 30px;
        text-shadow: 2px 2px 0px #FFEaa7;
    }

    /* 2. ☁️ 云朵卡片容器 (阅读区) */
    .scroll-container {
        background: #FFFFFF;
        border-radius: 25px;
        padding: 30px;
        box-shadow: 0 8px 20px rgba(235, 212, 180, 0.4);
        border: 2px solid #FFF5E0;
        height: 60vh; 
        overflow-y: auto;
        display: flex; flex-direction: column; gap: 15px;
        
        /* 核心对齐：宽度锁定 */
        width: 100%;
        max-width: 900px;
        margin: 0 auto; /* 居中 */
    }

    /* 行布局 */
    .cute-row {
        display: flex; align-items: flex-start;
        padding: 15px;
        border-bottom: 2px dashed #FFF0D4;
        transition: all 0.3s ease;
        border-radius: 12px;
    }
    .cute-row:hover { background-color: #FFFCF5; }

    /* 头像 */
    .cute-avatar {
        background-color: #FFD166; color: #fff;
        width: 40px; height: 40px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 12px; font-weight: bold; margin-right: 15px; flex-shrink: 0;
        box-shadow: 2px 2px 0px #F4B860;
    }
    .avatar-dawei { background-color: #6FCF97; box-shadow: 2px 2px 0px #27AE60; }

    /* 汉字区 */
    .cute-chinese {
        flex: 1; display: flex; flex-wrap: wrap; gap: 6px; align-items: flex-end;
    }
    ruby { 
        font-size: 24px; font-weight: 700; color: #4A4A4A; 
        ruby-position: under; line-height: 2.0; 
    }
    rt { 
        font-size: 12px; color: #FF8BA7; font-weight: 600; font-family: sans-serif;
    }

    /* 翻译区 */
    .cute-trans {
        width: 35%; padding-left: 20px;
        color: #AAB7B8; font-size: 0.9rem; font-style: italic;
        border-left: 2px solid #F0F3F4;
        display: flex; align-items: center; line-height: 1.4;
    }

    /* 3. 🎹 底部固定打字条 (与上面的卡片对齐) */
    .fixed-footer {
        position: fixed; bottom: 20px; left: 50%; 
        transform: translateX(-50%);
        
        /* 核心对齐：宽度与上面一致 */
        width: 90%; 
        max-width: 900px; /* 这里的 900px 和上面的 max-width 对应 */
        
        background: #FFFFFF;
        padding: 15px 25px;
        border-radius: 50px;
        box-shadow: 0 10px 25px rgba(255, 159, 28, 0.15);
        border: 2px solid #FFE5B4;
        display: flex; flex-direction: column; align-items: center;
        z-index: 9999;
    }
    
    .hide-pinyin rt { display: none !important; }
    .hide-trans .cute-trans { opacity: 0; }
    .active-highlight { background-color: #FFF8E1 !important; border-radius: 12px; }
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
        RULES: Include standard punctuation. Output JSON ARRAY only.
        Format: [{{"r": "美美", "t": [["你", "nǐ"], ["好", "hǎo"]], "tr_es": "Hola", "tr_en": "Hi"}}]
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
        
        if st.button(ui["gen_btn"]):
            with st.spinner(ui["loading"]):
                res = call_ai(topic, level, keys)
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
        
        st.markdown(f'<div class="fixed-footer"><div style="color:#FF9F1C; font-weight:bold; font-size:0.9rem; margin-bottom:5px;">{ui["instr"]}</div></div>', unsafe_allow_html=True)
        st.text_input("user_input", label_visibility="collapsed", placeholder="...")
        
        st.markdown("<script>const inputEl = window.parent.document.querySelector('.stTextInput');const footerEl = window.parent.document.querySelector('.fixed-footer');if(inputEl && footerEl) { footerEl.appendChild(inputEl); }</script>", unsafe_allow_html=True)

    else:
        st.info("👈 Please enter settings and click Generate")

if __name__ == "__main__":
    main()
