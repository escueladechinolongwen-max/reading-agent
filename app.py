import streamlit as st
import asyncio
import edge_tts
import os
import time
import random
import re

# --- 1. 页面基本配置 ---
st.set_page_config(
    page_title="Long Wen Reading Assistant", 
    page_icon="🐼", 
    layout="wide"
)

# --- 2. 界面双语语言包 ---
UI_TEXT = {
    "Español": {
        "pinyin": "Pinyin", "trans": "Traducción", "audio_gen": "Generando audio...",
        "typing_title": "✍️ Práctica", "typing_instr": "Escribe el texto de arriba aquí para practicar.", 
        "perfect": "🎉 ¡Excelente!", "refresh": "🔄 Regenerar Audio"
    },
    "English": {
        "pinyin": "Pinyin", "trans": "Translation", "audio_gen": "Generating audio...",
        "typing_title": "✍️ Practice", "typing_instr": "Type the text above here to practice.", 
        "perfect": "🎉 Perfect!", "refresh": "🔄 Regenerate Audio"
    }
}

# --- 3. 视觉设计 (CSS) - V24 干净修复版 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    .stApp { background-color: #FFFBF0; }
    
    /* ⬆️ 修复顶部空间：给更多留白，防止切头 */
    .block-container { 
        padding-top: 3rem !important; 
        padding-bottom: 2rem !important; 
        max-width: 1000px !important; 
    }

    /* 隐藏 Streamlit 默认的汉堡菜单和页脚，看起来更像原生 App */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 智能阅读框 */
    .reading-scroll-area {
        background-color: white; padding: 25px 30px; border-radius: 1.5rem;
        border: 2px solid #eee; overflow-y: auto; margin-bottom: 15px; 
        transition: height 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }
    
    /* 媒体查询：适配屏幕高度 */
    @media (min-height: 901px) { .reading-scroll-area { height: 60vh; } }
    @media (max-height: 900px) { .reading-scroll-area { height: 50vh; } }
    @media (max-height: 700px) { .reading-scroll-area { height: 42vh; } }

    .line-container { display: flex; margin-bottom: 8px; align-items: flex-start; justify-content: space-between; padding-bottom: 8px; border-bottom: 1px solid #fcfcfc; }
    .left-zone { display: flex; flex: 1; align-items: flex-start; max-width: 75%; }
    .role-label { min-width: 50px; font-weight: 900; color: #BE185D; font-size: 1rem; padding-top: 6px; font-family: 'Noto Serif SC', serif; }
    
    ruby { ruby-position: under; padding: 0 2px; font-family: "Noto Serif SC", serif; font-size: 24px; font-weight: 900; color: #333; letter-spacing: 1px; }
    rt { font-family: 'Noto Sans SC', sans-serif; font-size: 12px; color: #15803D !important; font-weight: 700; padding-top: 4px !important; }
    
    .right-zone { width: 22%; background: #EFF6FF; border-left: 3px solid #3B82F6; padding: 6px 10px; border-radius: 8px; margin-top: 5px; }
    .trans-text { font-size: 0.85rem; color: #1D4ED8; font-family: 'Noto Sans SC', sans-serif; font-weight: 700; line-height: 1.3; }
    
    .typing-section { background: #fff; padding: 15px 25px; border-radius: 1rem; border: 2px solid #eee; box-shadow: 0 -4px 15px rgba(0,0,0,0.04); }
    .instr-text { color: #666; font-size: 0.9em; font-weight: 700; margin-bottom: 5px; }
    
    .hide-pinyin rt { display: none !important; }
    .hide-pinyin ruby { line-height: 1.6 !important; }
    
    .main-header { 
        font-family: 'Noto Serif SC', serif; font-weight: 900; color: #2c3e50; 
        font-size: 2rem; text-align: center; margin-bottom: 20px; 
    }
</style>
""", unsafe_allow_html=True)

# --- 4. 数据库 (这里以后可以改成上传功能) ---
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

# --- 5. 语音核心 (V23 Pro) ---
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

# --- 6. 主程序 ---
def main():
    if "audio_v23" not in st.session_state: st.session_state.audio_v23 = ""
    if "lesson_v23" not in st.session_state: st.session_state.lesson_v23 = ""

    with st.sidebar:
        st.title("Settings")
        ui_lang = st.selectbox("Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        
        # 移除了调试用的红色标签，界面更干净
        st.divider()
        lesson_key = st.selectbox("Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)
        
        st.divider()
        if st.button(ui["refresh"]): # 移除了 type="primary" 让按钮没那么抢眼
            st.session_state.lesson_v23 = "" 
            st.rerun()

    # 顶部标题 (现在应该有更多空间了)
    st.markdown(f'<div class="main-header">{lesson_key}</div>', unsafe_allow_html=True)
    
    lesson_data = LESSONS[lesson_key]
    
    # 语音处理
    if st.session_state.lesson_v23 != lesson_key:
        fname = f"audio_v24_{int(time.time())}.mp3"
        with st.spinner(ui["audio_gen"]):
            asyncio.run(make_audio_v23(lesson_data, fname))
            st.session_state.audio_v23 = fname
            st.session_state.lesson_v23 = lesson_key
    
    st.audio(st.session_state.audio_v23)
    
    # 阅读区
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
    st.markdown(f'<div class="typing-section"><p class="instr-text">{ui["typing_instr"]}</p></div>', unsafe_allow_html=True)
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
