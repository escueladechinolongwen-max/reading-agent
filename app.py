import streamlit as st
import asyncio
import edge_tts
import os
import time
import re
import base64
import json

# --- 1. 全局配置与翻译字典 (放在最前面防止报错) ---
st.set_page_config(
    page_title="Long Wen Reading Pro", 
    page_icon="🐼", 
    layout="wide", 
    initial_sidebar_state="expanded" # 默认强制展开侧边栏
)

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

# --- 2. 视觉设计 (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFBF0;
        overflow: hidden !important; 
        height: 100vh;
    }

    .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 1200px !important;
        height: 100vh;
        display: flex;
        flex-direction: column;
    }

    /* 🔴 修复2：左上角箭头 (Red Target) 🔴 */
    header[data-testid="stHeader"] { 
        background-color: transparent !important; 
        visibility: visible !important; 
        z-index: 100 !important; 
        height: 0px !important; /* 避免占位 */
    }
    
    [data-testid="collapsedControl"] { 
        visibility: visible !important; 
        display: flex !important;
        background-color: #BE185D !important; /* 鲜艳的玫红色背景 */
        color: white !important; /* 白色箭头 */
        border-radius: 50% !important; /* 圆形按钮 */
        padding: 0.5rem !important;
        top: 60px !important; /* 往下挪，防止被遮挡 */
        left: 20px !important; 
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2) !important;
        z-index: 999999 !important;
        transition: transform 0.2s;
    }
    [data-testid="collapsedControl"]:hover {
        transform: scale(1.1);
    }

    /* 隐藏其他杂项 */
    #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"], footer { visibility: hidden; }

    .main-title { text-align: center; font-family: 'Noto Serif SC', serif; font-weight: 900; color: #334155; font-size: 1.6rem; margin-bottom: 5px; margin-top: -10px; }
    
    /* 阅读框 */
    .reading-scroll-area {
        background-color: white; padding: 20px 30px; border-radius: 1.5rem; 
        border: 2px solid #eee; overflow-y: auto !important; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.03); 
        height: calc(100vh - 350px) !important; 
        margin-bottom: 15px; 
        scroll-behavior: smooth;
    }

    .line-container { display: flex; margin-bottom: 8px; padding: 10px; border-radius: 12px; transition: all 0.3s ease; border-bottom: 1px solid #fcfcfc;}
    
    /* 高亮样式 */
    .active-meimei { background-color: #dcfce7 !important; border-left: 5px solid #22c55e !important; transform: scale(1.01); }
    .active-dawei { background-color: #dbeafe !important; border-left: 5px solid #3b82f6 !important; transform: scale(1.01); }
    
    .role-label { min-width: 50px; font-weight: 900; color: #BE185D; font-size: 1rem; padding-top: 6px; }
    ruby { ruby-position: under; padding: 0 2px; font-size: 24px; font-weight: 900; color: #333; }
    rt { font-size: 12px; color: #666; font-weight: 700; }
    
    .typing-section { background: #fff; padding: 12px 20px; border-radius: 1rem; border: 2px solid #3B82F6; margin-bottom: 10px; }
    .instr-text { color: #1E40AF; font-size: 0.9em; font-weight: 800; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 核心数据 ---
LESSONS = {
    "Dialogue I": [
        {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , "tr_es": "¿Qué fecha es hoy?", "tr_en": "What date is today?"},
        {"r": "大卫", "t": [("今天", "jīntiān"), ("9月1号", "jiǔ yuè yī hào"), ("。", "")] , "tr_es": "1 de septiembre.", "tr_en": "September 1st."},
        {"r": "美美", "t": [("今天", "jīntiān"), ("星期几", "xīngqī jǐ"), ("？", "")] , "tr_es": "¿Qué día es hoy?", "tr_en": "What day of week is it?"},
        {"r": "大卫", "t": [("星期三", "xīngqī sān"), ("。", "")] , "tr_es": "Miércoles.", "tr_en": "Wednesday."},
        {"r": "美美", "t": [("明天", "míngtiān"), ("几月几号", "jǐ yuè jǐ hào"), ("？", "")] , "tr_es": "¿Qué fecha es mañana?", "tr_en": "What's the date tomorrow?"},
        {"r": "大卫", "t": [("明天", "míngtiān"), ("9月2号", "jiǔ yuè èr hào"), ("。", "")] , "tr_es": "Mañana es 2 de sept.", "tr_en": "Tomorrow is Sept 2nd."}
    ]
}

# --- 4. 模拟 AI 生成逻辑 (修复3: AI功能) ---
def ai_generate_lesson(topic):
    # 这里是模拟数据，未来填入 API Key 即可变为真 AI
    return [
        {"r": "美美", "t": [("我们", "wǒmen"), ("去", "qù"), ("超市", "chāoshì"), ("吧", "ba"), ("。", "")] , "tr_es": "Vamos al supermercado.", "tr_en": "Let's go to the supermarket."},
        {"r": "大卫", "t": [("好", "hǎo"), ("的", "de"), ("，", ""), ("我", "wǒ"), ("想", "xiǎng"), ("买", "mǎi"), ("苹果", "píngguǒ"), ("。", "")] , "tr_es": "Vale, quiero comprar manzanas.", "tr_en": "Okay, I want to buy apples."}
    ]

# --- 5. 语音生成与时间戳 (修复1: 调整时间公式) ---
async def make_audio_v29(lesson_data, filename):
    timestamps = []
    curr = 0.0
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(lesson_data):
            voice = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
            raw = "".join([p[0] for p in line["t"]])
            # 💡 核心修复：更紧凑的时间计算公式
            # 旧公式: len * 0.45 + 0.6 (太慢)
            # 新公式: len * 0.32 + 0.15 (紧跟语速)
            dur = len(raw) * 0.32 + 0.15
            
            timestamps.append({"start": curr, "end": curr + dur, "role": line["r"]})
            communicate = edge_tts.Communicate(raw, voice)
            temp_f = f"temp_{i}.mp3"
            await communicate.save(temp_f)
            with open(temp_f, 'rb') as f: final_file.write(f.read())
            os.remove(temp_f)
            curr += dur
    return timestamps

# 播放器组件
def get_player_html(file_path, ts):
    with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    return f"""
    <div style="display:flex; flex-direction:column; align-items:center; background:white; padding:8px; border-radius:12px; border:1px solid #e2e8f0; margin-bottom:10px;">
        <audio id="p" controls src="data:audio/mp3;base64,{b64}" style="width:100%; max-width:450px; height:32px;"></audio>
        <div style="margin-top:5px; display:flex; gap:10px;">
            <button onclick="p.playbackRate=0.8" style="cursor:pointer; padding:2px 8px; border:1px solid #ccc; border-radius:4px;">🐢 0.8x</button>
            <button onclick="p.playbackRate=1.0" style="cursor:pointer; padding:2px 8px; border:1px solid #ccc; border-radius:4px;">▶ 1.0x</button>
            <button onclick="p.playbackRate=1.2" style="cursor:pointer; padding:2px 8px; border:1px solid #ccc; border-radius:4px;">🐇 1.2x</button>
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
                    // 给每个句子增加 0.1s 的容错，防止提前消失
                    if (cur >= t.start && cur < (t.end + 0.1)) {{
                        el.classList.add(t.role === "美美" ? "active-meimei" : "active-dawei");
                        el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }} else {{
                        el.classList.remove("active-meimei", "active-dawei");
                    }}
                }}
            }});
        }};
    </script>
    """

# --- 6. 主程序 ---
def main():
    if "audio_path" not in st.session_state: st.session_state.audio_path = ""
    if "timestamps" not in st.session_state: st.session_state.timestamps = []
    if "data_content" not in st.session_state: st.session_state.data_content = LESSONS["Dialogue I"] # 默认内容

    # 侧边栏逻辑
    with st.sidebar:
        st.title("🐼 Settings")
        
        # AI 模式切换器
        mode = st.radio("Mode / Modo", ["Preset Lessons", "AI Generator 🤖"])
        
        if mode == "AI Generator 🤖":
            st.info("Try typing 'Shopping' or 'School'")
            topic = st.text_input("Topic", "")
            if st.button("Generate Lesson ✨"):
                # 调用 AI 生成
                st.session_state.data_content = ai_generate_lesson(topic)
                st.session_state.audio_path = "" # 清空旧音频，强制重新生成
                st.rerun()
        else:
            # 传统模式
            lesson_key = st.selectbox("Lección", list(LESSONS.keys()))
            if st.session_state.get("last_lesson") != lesson_key:
                st.session_state.data_content = LESSONS[lesson_key]
                st.session_state.audio_path = "" # 强制更新
                st.session_state.last_lesson = lesson_key
        
        st.divider()
        ui_lang = st.selectbox("Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)
        
        if st.button(f"🔄 {ui['refresh']}"):
            st.session_state.audio_path = ""
            st.rerun()

    # 主界面渲染
    st.markdown(f'<div class="main-title">Dialogue / AI Lesson</div>', unsafe_allow_html=True)
    
    # 自动生成音频 (如果为空)
    if not st.session_state.audio_path:
        fname = f"audio_v29_{int(time.time())}.mp3"
        st.session_state.timestamps = asyncio.run(make_audio_v29(st.session_state.data_content, fname))
        st.session_state.audio_path = fname
    
    # 播放器
    if os.path.exists(st.session_state.audio_path):
        st.components.v1.html(get_player_html(st.session_state.audio_path, st.session_state.timestamps), height=100)

    # 阅读内容
    p_class = "" if show_pinyin else "hide-pinyin"
    html = f'<div class="reading-scroll-area {p_class}">'
    for idx, line in enumerate(st.session_state.data_content):
        html += f'<div class="line-container" id="line-{idx}">'
        html += f'<div style="display:flex; flex:1;"><div class="role-label">{line["r"]}</div><div>'
        for char, py in line["t"]:
            html += f'<ruby>{char}<rt>{py}</rt></ruby>' if show_pinyin and py else f'<ruby>{char}</ruby>'
        html += '</div></div>'
        if show_trans:
            html += f'<div class="right-zone"><span style="font-size:0.8rem;">{line["tr_es"] if ui_lang=="Español" else line["tr_en"]}</span></div>'
        html += '</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)

    # 练习区
    st.markdown(f'<div class="typing-section"><p class="instr-text">✍️ {ui["typing_instr"]}</p></div>', unsafe_allow_html=True)
    st.text_input("input", placeholder="...", label_visibility="collapsed")

if __name__ == "__main__":
    main()
