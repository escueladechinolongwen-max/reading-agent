import streamlit as st
import asyncio
import edge_tts
import os
import time
import re
import base64
import json

# --- 1. 界面翻译包 (刚才报错就是因为缺了这一块) ---
UI_TEXT = {
    "Español": {
        "pinyin": "Pinyin", "trans": "Traducción", "audio_gen": "Generando audio...",
        "typing_instr": "Instrucción: Sigue el texto de arriba para practicar tu reconocimiento de caracteres y escritura.", 
        "refresh": "Regenerar Audio"
    },
    "English": {
        "pinyin": "Pinyin", "trans": "Translation", "audio_gen": "Generating audio...",
        "typing_instr": "Instruction: Follow the text above to practice your character recognition and typing skills.", 
        "refresh": "Regenerate Audio"
    }
}

# --- 2. 页面配置与 CSS 强化 ---
st.set_page_config(page_title="Long Wen AI Reading", page_icon="🐼", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FFFBF0; overflow: hidden !important; height: 100vh; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 0rem !important; max-width: 1200px !important; height: 100vh; display: flex; flex-direction: column; }
    
    /* 强制显示左上角玫红色箭头按钮 */
    header[data-testid="stHeader"] { background-color: transparent !important; visibility: visible !important; z-index: 1000000 !important; }
    [data-testid="collapsedControl"] { background-color: white !important; border-radius: 0 10px 10px 0 !important; box-shadow: 2px 2px 10px rgba(0,0,0,0.1) !important; color: #BE185D !important; visibility: visible !important; display: flex !important; z-index: 1000001 !important; width: 40px !important; height: 40px !important; }
    #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"], footer { visibility: hidden; }

    .main-title { text-align: center; font-family: 'Noto Serif SC', serif; font-weight: 900; color: #334155; font-size: 1.6rem; margin-bottom: 5px; margin-top: -30px; }
    
    /* 阅读框锁定高度 */
    .reading-scroll-area {
        background-color: white; padding: 20px 30px; border-radius: 1.5rem; border: 2px solid #eee; overflow-y: auto !important; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.03); height: calc(100vh - 360px) !important; margin-bottom: 15px; scroll-behavior: smooth;
    }

    .line-container { display: flex; margin-bottom: 8px; padding: 10px; border-radius: 12px; transition: all 0.4s ease; border-bottom: 1px solid #fcfcfc;}
    
    /* 🔴 变色高亮样式 🔴 */
    .active-meimei { background-color: #f0fdf4 !important; border: 1px solid #4ade80 !important; }
    .active-meimei ruby { color: #15803d !important; }
    .active-dawei { background-color: #eff6ff !important; border: 1px solid #60a5fa !important; }
    .active-dawei ruby { color: #1d4ed8 !important; }
    
    .role-label { min-width: 50px; font-weight: 900; color: #BE185D; font-size: 1rem; padding-top: 6px; }
    ruby { ruby-position: under; padding: 0 2px; font-size: 24px; font-weight: 900; color: #333; }
    rt { font-size: 12px; color: #666; font-weight: 700; }
    
    .typing-section { background: #fff; padding: 12px 20px; border-radius: 1rem; border: 2px solid #3B82F6; margin-bottom: 10px; }
    .instr-text { color: #1E40AF; font-size: 0.9em; font-weight: 800; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 核心数据与逻辑 ---
LESSONS = {
    "Dialogue I": [
        {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , "tr_es": "¿Qué fecha es hoy?", "tr_en": "What date is today?"},
        {"r": "大卫", "t": [("今天", "jīntiān"), ("9月1号", "jiǔ yuè yī hào"), ("。", "")] , "tr_es": "1 de septiembre.", "tr_en": "September 1st."},
        {"r": "美美", "t": [("今天", "jīntiān"), ("星期几", "xīngqī jǐ"), ("？", "")] , "tr_es": "¿Qué día es hoy?", "tr_en": "What day of week is it?"},
        {"r": "大卫", "t": [("星期三", "xīngqī sān"), ("。", "")] , "tr_es": "Miércoles.", "tr_en": "Wednesday."}
    ]
}

async def make_audio_v28(lesson_data, filename):
    timestamps = []
    curr = 0.0
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(lesson_data):
            voice = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
            raw = "".join([p[0] for p in line["t"]])
            dur = len(raw) * 0.45 + 0.6
            timestamps.append({"start": curr, "end": curr + dur, "role": line["r"]})
            communicate = edge_tts.Communicate(raw, voice)
            temp_f = f"temp_{i}.mp3"
            await communicate.save(temp_f)
            with open(temp_f, 'rb') as f: final_file.write(f.read())
            os.remove(temp_f)
            curr += dur
    return timestamps

def get_player_html(file_path, ts):
    with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    return f"""
    <div style="display:flex; flex-direction:column; align-items:center; background:white; padding:8px; border-radius:12px; border:1px solid #e2e8f0; margin-bottom:10px;">
        <audio id="p" controls src="data:audio/mp3;base64,{b64}" style="width:100%; max-width:450px; height:32px;"></audio>
        <div style="margin-top:5px; display:flex; gap:10px;">
            <button onclick="p.playbackRate=0.8" style="cursor:pointer; padding:2px 8px;">🐢 0.8x</button>
            <button onclick="p.playbackRate=1.0" style="cursor:pointer; padding:2px 8px;">▶ 1.0x</button>
            <button onclick="p.playbackRate=1.2" style="cursor:pointer; padding:2px 8px;">🐇 1.2x</button>
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
                        el.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
                    }} else {{
                        el.classList.remove("active-meimei", "active-dawei");
                    }}
                }}
            }});
        }};
    </script>
    """

# --- 4. 主程序 ---
def main():
    # 初始化 session state
    if "audio_path" not in st.session_state: st.session_state.audio_path = ""
    if "timestamps" not in st.session_state: st.session_state.timestamps = []
    if "current_lesson" not in st.session_state: st.session_state.current_lesson = ""

    with st.sidebar:
        st.title("🐼 AI Workshop")
        mode = st.radio("Mode", ["Preset Lessons", "AI Generator 🤖"])
        st.divider()
        ui_lang = st.selectbox("Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang] # 🔴 这里现在不会报错了！
        
        lesson_key = st.selectbox("Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)

    st.markdown(f'<div class="main-title">{lesson_key}</div>', unsafe_allow_html=True)
    lesson_data = LESSONS[lesson_key]
    
    if st.session_state.current_lesson != lesson_key:
        fname = f"v28_final_{int(time.time())}.mp3"
        st.session_state.timestamps = asyncio.run(make_audio_v28(lesson_data, fname))
        st.session_state.audio_path = fname
        st.session_state.current_lesson = lesson_key
    
    if os.path.exists(st.session_state.audio_path):
        st.components.v1.html(get_player_html(st.session_state.audio_path, st.session_state.timestamps), height=100)

    p_class = "" if show_pinyin else "hide-pinyin"
    html = f'<div class="reading-scroll-area {p_class}">'
    for idx, line in enumerate(lesson_data):
        html += f'<div class="line-container" id="line-{idx}">'
        html += f'<div style="display:flex; flex:1;"><div class="role-label">{line["r"]}</div><div>'
        for char, py in line["t"]:
            html += f'<ruby>{char}<rt>{py}</rt></ruby>' if show_pinyin and py else f'<ruby>{char}</ruby>'
        html += '</div></div>'
        if show_trans:
            html += f'<div class="right-zone"><span style="font-size:0.8rem;">{line["tr_es"] if ui_lang=="Español" else line["tr_en"]}</span></div>'
        html += '</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)

    st.markdown(f'<div class="typing-section"><p class="instr-text">✍️ {ui["typing_instr"]}</p></div>', unsafe_allow_html=True)
    st.text_input("input", placeholder="...", label_visibility="collapsed")

if __name__ == "__main__":
    main()
