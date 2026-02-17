import streamlit as st
import asyncio
import edge_tts
import os
import time
import random
import re
import base64

# --- 1. 页面基本配置 ---
st.set_page_config(
    page_title="Long Wen Reading Pro", 
    page_icon="🐼", 
    layout="wide",
    initial_sidebar_state="expanded" # 强制展开侧边栏
)

# --- 2. 界面双语语言包 ---
UI_TEXT = {
    "Español": {
        "title": "Asistente de Lectura",
        "settings": "Configuración",
        "pinyin": "Pinyin", "trans": "Traducción", "audio_gen": "Generando audio...",
        "typing_instr": "Instrucción: Sigue el texto de arriba para practicar tu reconocimiento de caracteres y escritura.", 
        "perfect": "🎉 ¡Excelente!", "refresh": "Regenerar Audio",
        "speed": "Velocidad"
    },
    "English": {
        "title": "Reading Assistant",
        "settings": "Settings",
        "pinyin": "Pinyin", "trans": "Translation", "audio_gen": "Generating audio...",
        "typing_instr": "Instruction: Follow the text above to practice your character recognition and typing skills.", 
        "perfect": "🎉 Perfect!", "refresh": "Regenerate Audio",
        "speed": "Speed"
    }
}

# --- 3. 视觉设计 (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    .stApp { background-color: #FFFBF0; }
    
    /* 1. 顶部布局：调整间距 */
    .block-container { 
        padding-top: 2rem !important; 
        padding-bottom: 2rem !important; 
        max-width: 1200px !important; 
    }

    /* 2. 关键修复：不要隐藏 header，否则左上角的箭头 > 会消失！ */
    /* header {visibility: hidden;}  <-- 这行代码被删除了 */
    
    /* 只隐藏右上角的汉堡菜单 (三个点) */
    #MainMenu {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;} /* 隐藏顶部的彩条 */
    footer {visibility: hidden;}
    
    /* 侧边栏美化 */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    /* 3. 自定义播放器区域 */
    .audio-wrapper {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        background: #fff; padding: 10px; border-radius: 12px; margin-top: 0px; margin-bottom: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* 倍速按钮 */
    .speed-btn {
        background-color: white; border: 1px solid #cbd5e1; border-radius: 8px;
        padding: 4px 12px; margin: 0 5px; cursor: pointer; 
        font-size: 13px; font-weight: bold; color: #475569;
        transition: all 0.2s;
    }
    .speed-btn:hover { background-color: #e0f2fe; color: #0284c7; border-color: #0284c7; }
    .speed-btn:active { transform: scale(0.95); }

    /* 4. 阅读框：高度最大化 */
    .reading-scroll-area {
        background-color: white; padding: 25px 30px; border-radius: 1.5rem;
        border: 2px solid #eee; overflow-y: auto; margin-bottom: 15px; 
        transition: height 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }
    
    /* 根据屏幕高度智能调整阅读区高度 */
    @media (min-height: 901px) { .reading-scroll-area { height: 65vh; } }
    @media (max-height: 900px) { .reading-scroll-area { height: 55vh; } }
    @media (max-height: 700px) { .reading-scroll-area { height: 45vh; } }

    /* 文本样式 */
    .line-container { display: flex; margin-bottom: 8px; align-items: flex-start; justify-content: space-between; padding-bottom: 8px; border-bottom: 1px solid #fcfcfc; }
    .left-zone { display: flex; flex: 1; align-items: flex-start; max-width: 75%; }
    .role-label { min-width: 50px; font-weight: 900; color: #BE185D; font-size: 1rem; padding-top: 6px; font-family: 'Noto Serif SC', serif; }
    ruby { ruby-position: under; padding: 0 2px; font-family: "Noto Serif SC", serif; font-size: 24px; font-weight: 900; color: #333; letter-spacing: 1px; }
    rt { font-family: 'Noto Sans SC', sans-serif; font-size: 12px; color: #15803D !important; font-weight: 700; padding-top: 4px !important; }
    .right-zone { width: 22%; background: #EFF6FF; border-left: 3px solid #3B82F6; padding: 6px 10px; border-radius: 8px; margin-top: 5px; }
    .trans-text { font-size: 0.85rem; color: #1D4ED8; font-family: 'Noto Sans SC', sans-serif; font-weight: 700; line-height: 1.3; }
    
    .typing-section { background: #fff; padding: 15px 25px; border-radius: 1rem; border: 2px solid #eee; box-shadow: 0 -4px 15px rgba(0,0,0,0.04); }
    .instr-text { color: #555; font-size: 0.95em; font-weight: 700; margin-bottom: 8px; }
    
    .hide-pinyin rt { display: none !important; }
    .hide-pinyin ruby { line-height: 1.6 !important; }
    
    .main-title { 
        text-align: center; font-family: 'Noto Serif SC', serif; 
        font-weight: 900; color: #334155; font-size: 1.8rem; margin-bottom: 10px; margin-top: -10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. 数据库 ---
LESSONS = {
    "Dialogue I": [
        {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("，", ""), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , "tr_es": "David, disculpe, ¿qué fecha es hoy?", "tr_en": "David, what's the date today?"},
        {"r": "大卫", "t": [("今天", "jīntiān"), ("9月1号", "jiǔ yuè yī hào"), ("。", "")] , "tr_es": "Hoy es 1 de septiembre.", "tr_en": "Today is Sept 1st."},
        {"r": "美美", "t": [("今天", "jīntiān"), ("星期几", "xīngqī jǐ"), ("？", "")] , "tr_es": "¿Qué día es hoy?", "tr_en": "What day of week is it?"},
        {"r": "大卫", "t": [("星期三", "xīngqī sān"), ("。", "")] , "tr_es": "Miércoles.", "tr_en": "Wednesday."},
        {"r": "美美", "t": [("明天", "míngtiān"), ("几月几号", "jǐ yuè jǐ hào"), ("？", "")] , "tr_es": "¿Qué fecha es mañana?", "tr_en": "What's the date tomorrow?"},
        {"r": "大卫", "t": [("明天", "míngtiān"), ("9月2号", "jiǔ yuè èr hào"), ("。", "")] , "tr_es": "Mañana es 2 de sept.", "tr_en": "Tomorrow is Sept 2nd."},
        {"r": "美美", "t": [("昨天", "zuótiān"), ("呢", "ne"), ("？", "")] , "tr_es": "¿Y ayer?", "tr_en": "And yesterday?"},
        {"r": "大卫", "t": [("昨天", "zuótiān"), ("是", "shì"), ("8月31号", "bā yuè sānshíyī hào"), ("。", "")] , "tr_es": "Ayer fue 31 de agosto.", "tr_en": "Yesterday was Aug 31st."}
    ],
    "Dialogue II": [
        {"r": "美美", "t": [("明天", "míngtiān"), ("是", "shì"), ("星期六", "xīngqīliù"), ("，", ""), ("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("吗", "ma"), ("？", "")] , "tr_es": "¿Vas a la escuela mañana?", "tr_en": "Are you going to school tomorrow?"},
        {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("。", "")] , "tr_es": "Sí, voy.", "tr_en": "Yes, I am."},
        {"r": "美美", "t": [("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("做", "zuò"), ("什么", "shénme"), ("？", "")] , "tr_es": "¿A qué vas?", "tr_en": "What will you do there?"},
        {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("学校", "xuéxiào"), ("看书", "kànshū"), ("。", ""), ("你", "nǐ"), ("吗", "ma"), ("？", "")] , "tr_es": "A leer. ¿Y tú?", "tr_en": "To read. And you?"},
        {"r": "美美", "t": [("我", "wǒ"), ("不", "bù"), ("去", "qù"), ("。", ""), ("我", "wǒ"), ("去", "qù"), ("我", "wǒ"), ("的", "de"), ("西班牙朋友", "Xībānyá péngyou"), ("家", "jiā"), ("看猫", "kàn māo"), ("。", "")] , "tr_es": "Voy a casa de mi amigo.", "tr_en": "I'm going to my friend's house."},
        {"r": "大卫", "t": [("是", "shì"), ("去", "qù"), ("西西", "Xīxi"), ("家", "jiā"), ("吗", "ma"), ("？", "")] , "tr_es": "¿A casa de Xixi?", "tr_en": "To Xixi's house?"},
        {"r": "美美", "t": [("是的", "shìde"), ("。", "")] , "tr_es": "Sí.", "tr_en": "Yes."},
        {"r": "大卫", "t": [("西西", "Xīxi"), ("家", "jiā"), ("有", "yǒu"), ("几", "jǐ"), ("只", "zhī"), ("猫", "māo"), ("？", "")] , "tr_es": "¿Cuántos gatos?", "tr_en": "How many cats?"},
        {"r": "美美", "t": [("他", "tā"), ("有", "yǒu"), ("两", "liǎng"), ("只", "zhī"), ("猫", "māo"), ("。", "")] , "tr_es": "Tiene dos.", "tr_en": "He has two cats."}
    ]
}

# --- 5. 语音核心逻辑 ---
async def make_audio_v23(lesson_data, filename):
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(lesson_data):
            voice = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
            raw = "".join([pair[0] for pair in line["t"]])
            txt = raw.replace("9月", "九月").replace("1号", "一号").replace("2号", "二号").replace("8月", "八月").replace("31号", "三十一号")
            clean = re.sub(r'[^\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef0-9]', '', txt)
            temp_f = f"t_{i}_{int(time.time())}.mp3"
            try:
                communicate = edge_tts.Communicate(clean, voice)
                await communicate.save(temp_f)
                with open(temp_f, 'rb') as chunk:
                    final_file.write(chunk.read())
            except: pass
            finally:
                if os.path.exists(temp_f): os.remove(temp_f)

# 辅助：自定义HTML5播放器
def get_audio_html(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f"""
    <div class="audio-wrapper">
        <audio id="player" controls src="data:audio/mp3;base64,{b64}" style="width: 100%; max-width: 500px; height: 35px;"></audio>
        <div style="margin-top: 8px; display: flex; gap: 10px; align-items: center;">
            <button class="speed-btn" onclick="document.getElementById('player').playbackRate = 0.8">🐢 0.8x</button>
            <button class="speed-btn" onclick="document.getElementById('player').playbackRate = 1.0">▶ 1.0x</button>
            <button class="speed-btn" onclick="document.getElementById('player').playbackRate = 1.25">🐇 1.25x</button>
        </div>
    </div>
    """

# --- 6. 主程序 ---
def main():
    if "audio_v23" not in st.session_state: st.session_state.audio_v23 = ""
    if "lesson_v23" not in st.session_state: st.session_state.lesson_v23 = ""

    # ==========================================
    # 🔴 侧边栏 (Sidebar) - 设置区
    # ==========================================
    with st.sidebar:
        st.title("🐼 Settings")
        
        # 语言选择
        ui_lang = st.selectbox("Language / Idioma", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        st.divider()
        
        # 课文选择
        lesson_key = st.selectbox("Lección / Lesson", list(LESSONS.keys()))
        
        # 开关
        c1, c2 = st.columns(2)
        with c1:
            show_pinyin = st.toggle(ui["pinyin"], value=True)
        with c2:
            show_trans = st.toggle(ui["trans"], value=False)
            
        st.divider()
        
        # 刷新按钮
        if st.button(f"🔄 {ui['refresh']}", use_container_width=True):
            st.session_state.lesson_v23 = ""
            st.rerun()

    # ==========================================
    # 🔴 核心阅读区 (Main Area)
    # ==========================================
    
    # 标题
    st.markdown(f'<div class="main-title">{lesson_key}</div>', unsafe_allow_html=True)
    
    # 准备数据
    lesson_data = LESSONS[lesson_key]
    
    # 生成音频
    if st.session_state.lesson_v23 != lesson_key:
        fname = f"audio_v25_3_{int(time.time())}.mp3"
        with st.spinner(ui["audio_gen"]):
            asyncio.run(make_audio_v23(lesson_data, fname))
            st.session_state.audio_v23 = fname
            st.session_state.lesson_v23 = lesson_key
    
    # 播放器
    if os.path.exists(st.session_state.audio_v23):
        st.components.v1.html(get_audio_html(st.session_state.audio_v23), height=95)
    
    # 阅读卡片
    p_class = "" if show_pinyin else "hide-pinyin"
    html_card = f'<div class="reading-scroll-area {p_class}">'
    for line in lesson_data:
        html_card += '<div class="line-container">'
        html_card += f'<div class="left-zone"><div class="role-label">{line["r"]}</div><div class="text-content">'
        for char, py in line["t"]:
            if show_pinyin and py:
                html_card += f'<ruby>{char}<rt>{py}</rt></ruby>'
            else:
                html_card += f'<ruby style="line-height:1.4;">{char}</ruby>'
        html_card += '</div></div>'
        if show_trans:
            t_content = line["tr_en"] if ui_lang == "English" else line["tr_es"]
            html_card += f'<div class="right-zone"><span class="trans-text">{t_content}</span></div>'
        html_card += '</div>'
    html_card += '</div>'
    st.markdown(html_card, unsafe_allow_html=True)

    # 练习区
    st.markdown(f'<div class="typing-section"><p class="instr-text">✍️ {ui["typing_instr"]}</p></div>', unsafe_allow_html=True)
    user_input = st.text_input("inp", placeholder="...", label_visibility="collapsed")
    
    full_text = "".join(["".join([p[0] for p in l["t"]]) for l in lesson_data])
    
    if user_input:
        res = '<div style="background:white; padding:10px 15px; border-radius:10px; border:2px solid #ddd; margin-top:5px;">'
        max_l = max(len(full_text), len(user_input))
        for i in range(max_l):
            if i < len(user_input) and i < len(full_text):
                color = "#2ecc71" if user_input[i] == full_text[i] else "#e74c3c"
                res += f'<span style="color:{color}; font-size:20px; font-weight:bold;">{user_input[i]}</span>'
            elif i < len(user_input):
                res += f'<span style="color:#e74c3c; font-size:20px;">{user_input[i]}</span>'
        st.markdown(res + '</div>', unsafe_allow_html=True)
        if user_input.strip() == full_text.strip(): st.balloons()

if __name__ == "__main__":
    main()
