import streamlit as st
import asyncio
import edge_tts
import os
import time
import re
import base64
import json
import google.generativeai as genai

# --- 1. 配置与样式 ---
st.set_page_config(page_title="Long Wen Reading Pro", page_icon="🐼", layout="wide", initial_sidebar_state="expanded")

# 自动从 Render 环境变量抓取
MY_API_KEY = os.environ.get("GOOGLE_API_KEY") 

UI_TEXT = {
    "Español": { 
        "pinyin": "Pinyin", "trans": "Traducción", "typing_instr": "Instrucción: Sigue el texto de arriba para practicar.", 
        "refresh": "Regenerar Audio", "gen_btn": "Generar Lección ✨", 
        "topic": "Tema", "level": "Nivel (HSK)", "keywords": "Palabras clave",
        "ai_thinking": "La IA está pensando..."
    },
    "English": { 
        "pinyin": "Pinyin", "trans": "Translation", "typing_instr": "Instruction: Follow the text above to practice.", 
        "refresh": "Regenerate Audio", "gen_btn": "Generate Lesson ✨", 
        "topic": "Topic", "level": "Level (HSK)", "keywords": "Keywords",
        "ai_thinking": "AI is thinking..."
    }
}

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FFFBF0; overflow: hidden !important; height: 100vh; }
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; max-width: 1200px !important; height: 100vh; display: flex; flex-direction: column; }
    header[data-testid="stHeader"] { background-color: transparent !important; visibility: visible !important; height: 0px !important; z-index: 100; }
    [data-testid="collapsedControl"] { 
        visibility: visible !important; display: flex !important; background-color: #BE185D !important; color: white !important; 
        border-radius: 50% !important; padding: 0.5rem !important; top: 60px !important; left: 20px !important; 
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2) !important; z-index: 999999 !important; 
    }
    #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"], footer { visibility: hidden; }
    .main-title { text-align: center; font-family: 'Noto Serif SC', serif; font-weight: 900; color: #334155; font-size: 1.6rem; margin-bottom: 5px; margin-top: -10px; }
    .reading-scroll-area { 
        background-color: white; padding: 20px 30px; border-radius: 1.5rem; border: 2px solid #eee; 
        overflow-y: auto !important; box-shadow: 0 4px 15px rgba(0,0,0,0.03); 
        height: calc(100vh - 380px) !important; margin-bottom: 15px; scroll-behavior: smooth; 
    }
    .line-container { display: flex; margin-bottom: 8px; padding: 10px; border-radius: 12px; transition: all 0.2s ease; border-bottom: 1px solid #fcfcfc;}
    .active-meimei { background-color: #dcfce7 !important; border-left: 5px solid #22c55e !important; }
    .active-dawei { background-color: #dbeafe !important; border-left: 5px solid #3b82f6 !important; }
    .role-label { min-width: 50px; font-weight: 900; color: #BE185D; font-size: 1rem; padding-top: 6px; }
    ruby { ruby-position: under; padding: 0 2px; font-size: 24px; font-weight: 900; color: #333; }
    rt { font-size: 12px; color: #666; font-weight: 700; }
    .typing-section { background: #fff; padding: 12px 20px; border-radius: 1rem; border: 2px solid #3B82F6; margin-bottom: 10px; }
    .hide-pinyin rt { display: none !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 基础对话 ---
BASE_LESSON = [
    {"r": "美美", "t": [("你好", "nǐhǎo")], "tr_es": "Hola", "tr_en": "Hello"},
    {"r": "大卫", "t": [("你好", "nǐhǎo")], "tr_es": "Hola", "tr_en": "Hello"}
]

# --- 4. 增强版 AI 解析逻辑 ---
def call_real_ai(topic, level, keywords):
    if not MY_API_KEY:
        return BASE_LESSON
    try:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        # 指令升级：强制纯净 JSON
        prompt = f"""
        TASK: Create a Chinese dialogue.
        ROLES: '美美' (Female) and '大卫' (Male).
        TOPIC: {topic}, LEVEL: {level}, KEYWORDS: {keywords}.
        FORMAT: Output ONLY a valid JSON array. No text before or after.
        STRUCTURE: [{{"r": "美美", "t": [["汉", "hàn"]], "tr_es": "Spanish", "tr_en": "English"}}]
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        # 暴力提取 JSON 部分
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
    except:
        return BASE_LESSON # 失败时保底，不显示红字

# --- 5. 语音与播放器 ---
async def make_audio_safe(lesson_data, filename):
    ts = []
    curr = 0.0
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(lesson_data):
            voice = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
            raw = "".join([p[0] for p in line["t"]])
            dur = len(raw) * 0.3 + 1.0
            ts.append({"start": curr, "end": curr + dur, "role": line["r"]})
            try:
                communicate = edge_tts.Communicate(raw, voice)
                temp_f = f"t_{int(time.time())}_{i}.mp3"
                await communicate.save(temp_f)
                if os.path.exists(temp_f):
                    with open(temp_f, 'rb') as f: final_file.write(f.read())
                    os.remove(temp_f)
            except: pass
            curr += dur
    return ts

def get_player_html(file_path, ts):
    with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    return f"""
    <div style="display:flex; flex-direction:column; align-items:center; background:white; padding:8px; border-radius:12px; border:1px solid #e2e8f0; margin-bottom:10px;">
        <audio id="p" controls src="data:audio/mp3;base64,{b64}" style="width:100%; max-width:450px; height:32px;"></audio>
        <div style="margin-top:5px;">
            <button onclick="p.playbackRate=0.8" style="padding:2px 8px;">🐢 0.8x</button>
            <button onclick="p.playbackRate=1.0" style="padding:2px 8px;">▶ 1.0x</button>
            <button onclick="p.playbackRate=1.2" style="padding:2px 8px;">🐇 1.2x</button>
        </div>
    </div>
    <script>
        const p = document.getElementById('p');
        const ts = {json.dumps(ts)};
        p.ontimeupdate = () => {{
            const cur = p.currentTime / p.playbackRate;
            ts.forEach((t, i) => {{
                const el = window.parent.document.getElementById('line-'+i);
                if (el) {{
                    if (cur >= t.start && cur < t.end) {{
                        el.classList.add(t.role === "美美" ? "active-meimei" : "active-dawei");
                        el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }} else {{ el.classList.remove("active-meimei", "active-dawei"); }}
                }}
            }});
        }};
    </script>
    """

def main():
    if "data_v31" not in st.session_state: st.session_state.data_v31 = BASE_LESSON
    if "audio_v31" not in st.session_state: st.session_state.audio_v31 = ""
    if "ts_v31" not in st.session_state: st.session_state.ts_v31 = []

    with st.sidebar:
        st.title("🐼 AI Workshop")
        mode = st.radio("Mode", ["Preset", "AI Generator 🤖"])
        ui_lang = st.selectbox("Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        if mode == "AI Generator 🤖":
            topic = st.text_input(ui["topic"], "School")
            col1, col2 = st.columns(2)
            with col1: level = st.selectbox(ui["level"], ["HSK 1", "HSK 2", "HSK 3"])
            with col2: keywords = st.text_input(ui["keywords"], "老师, 同学")
            if st.button(ui["gen_btn"]):
                with st.spinner(ui["ai_thinking"]):
                    st.session_state.data_v31 = call_real_ai(topic, level, keywords)
                    st.session_state.audio_v31 = ""
                    st.rerun()
        else:
            if st.button("Load Dialogue I"):
                st.session_state.data_v31 = [
                    {"r": "美美", "t": [("今天", "jīntiān"), ("几号", "jǐhào")], "tr_es": "¿Qué fecha es hoy?", "tr_en": "..."},
                    {"r": "大卫", "t": [("9月1号", "jiǔyuè yīhào")], "tr_es": "1 de sept.", "tr_en": "..."}
                ]
                st.session_state.audio_v31 = ""
                st.rerun()
        st.divider()
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)
        if st.button(f"🔄 {ui['refresh']}"):
            st.session_state.audio_v31 = ""
            st.rerun()

    st.markdown('<div class="main-title">Reading Assistant</div>', unsafe_allow_html=True)
    if not st.session_state.audio_v31:
        fname = f"v34_{int(time.time())}.mp3"
        st.session_state.ts_v31 = asyncio.run(make_audio_safe(st.session_state.data_content if "data_content" in st.session_state else st.session_state.data_v31, fname))
        st.session_state.audio_v31 = fname
    
    if os.path.exists(st.session_state.audio_v31):
        st.components.v1.html(get_player_html(st.session_state.audio_v31, st.session_state.ts_v31), height=100)

    p_class = "" if show_pinyin else "hide-pinyin"
    html = f'<div class="reading-scroll-area {p_class}">'
    for idx, line in enumerate(st.session_state.data_v31):
        html += f'<div class="line-container" id="line-{idx}">'
        html += f'<div style="display:flex; flex:1;"><div class="role-label">{line["r"]}</div><div>'
        for char, py in line["t"]:
            html += f'<ruby>{char}<rt>{py}</rt></ruby>' if show_pinyin and py else f'<ruby>{char}</ruby>'
        html += '</div></div>'
        if show_trans:
            html += f'<div class="right-zone"><span style="font-size:0.8rem;">{line["tr_es"] if ui_lang=="Español" else line["tr_en"]}</span></div>'
        html += '</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)
    st.markdown('<div class="typing-section"><p style="color:#1E40AF; font-size:0.9em; font-weight:800; margin-bottom:5px;">✍️ Practice Section</p></div>', unsafe_allow_html=True)
    st.text_input("inp", placeholder="...", label_visibility="collapsed")

if __name__ == "__main__":
    main()
