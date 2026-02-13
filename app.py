import streamlit as st
import asyncio
import edge_tts
import os
import time
import random
import html

# --- 1. 页面基本配置 ---
st.set_page_config(
    page_title="阅读 Pro - 双翼分栏版", 
    page_icon="🎓", 
    layout="centered"
)

# --- 2. 界面双语语言包 ---
UI_TEXT = {
    "Español": {
        "pinyin": "Pinyin", 
        "trans": "Traducción", 
        "audio_gen": "Preparando voces...",
        "typing_title": "✍️ Práctica de Escritura",
        "typing_instr": "Escribe el texto de arriba aquí para mejorar tu habilidad.",
        "perfect": "🎉 ¡Excelente!"
    },
    "English": {
        "pinyin": "Pinyin", 
        "trans": "Translation", 
        "audio_gen": "Generating voices...",
        "typing_title": "✍️ Typing Practice",
        "typing_instr": "Type the text above here to master your typing skills.",
        "perfect": "🎉 Perfect!"
    }
}

# --- 3. 视觉设计 (CSS) - 左右分栏与紧凑化 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    .stApp { background-color: #FFFBF0; }
    
    .reading-card {
        background-color: white; 
        padding: 20px 30px; 
        border-radius: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.04);
        max-width: 850px; 
        margin: 0 auto;
    }

    /* 左右分栏容器 */
    .line-container { 
        display: flex; 
        margin-bottom: 8px; 
        align-items: flex-start;
        justify-content: space-between;
        border-bottom: 1px solid #fcfcfc;
        padding: 4px 0;
    }

    /* 左侧：姓名 + 中文 */
    .left-zone {
        display: flex;
        flex: 1;
        align-items: flex-start;
        max-width: 70%;
    }

    .role-label {
        min-width: 55px; 
        font-weight: 900; 
        color: #BE185D; /* 角色：胭脂红 */
        font-size: 1em; 
        padding-top: 10px; 
        font-family: 'Noto Serif SC', serif;
    }

    .text-content { line-height: 2.6; }

    ruby { 
        ruby-position: under; 
        padding: 0 3px; 
        font-family: "Noto Serif SC", serif; 
        font-size: 22px; 
        font-weight: 900; 
        color: #333; 
    }

    /* 拼音：绿色 */
    rt { 
        font-family: 'Noto Sans SC', sans-serif; 
        font-size: 11px; 
        color: #15803D !important; 
        font-weight: 700; 
        padding-top: 6px !important; 
    }

    /* 右侧：翻译独立框 (蓝色) */
    .right-zone {
        width: 25%;
        background: #EFF6FF;
        border-left: 3px solid #3B82F6;
        padding: 6px 12px;
        border-radius: 8px;
        margin-top: 8px;
        min-height: 35px;
    }

    .trans-text { 
        font-size: 0.8em; 
        color: #1D4ED8; /* 翻译：深蓝色 */
        font-family: 'Noto Sans SC', sans-serif; 
        font-weight: 700;
        line-height: 1.3;
    }

    /* 隐藏拼音模式 */
    .hide-pinyin rt { display: none !important; }
    .hide-pinyin .text-content { line-height: 1.4 !important; }
    .hide-pinyin .role-label { padding-top: 2px !important; }

    /* 说明文字 */
    .instr-box {
        color: #666;
        font-size: 0.9em;
        font-weight: 700;
        margin-top: 15px;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. 数据库：Dialogue I & II ---
LESSONS = {
    "Dialogue I": [
        {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("，", ""), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , "tr_es": "David, ¿qué fecha es hoy?", "tr_en": "David, what's the date today?"},
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

# --- 5. 语音合成核心逻辑 (纯净版) ---
async def make_audio(lesson_data, filename):
    ssml = "<?xml version='1.0' encoding='UTF-8'?>"
    ssml += "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>"
    for line in lesson_data:
        voice = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
        text = "".join([pair[0] for pair in line["t"]])
        # 转换数字发音
        text = text.replace("9月", "九月").replace("1号", "一号").replace("2号", "二号").replace("8月", "八月").replace("31号", "三十一号")
        ssml += f"<voice name='{voice}'>{html.escape(text)}</voice><break time='600ms'/>"
    ssml += "</speak>"
    await edge_tts.Communicate(ssml).save(filename)

# --- 6. 主程序 ---
def main():
    if "final_audio" not in st.session_state: st.session_state.final_audio = ""

    with st.sidebar:
        st.title("Settings")
        ui_lang = st.selectbox("Language / Idioma", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        st.divider()
        lesson_key = st.selectbox("Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)

    st.subheader(lesson_key)
    lesson_data = LESSONS[lesson_key]
    
    # 语音缓存刷新
    if "curr_lesson" not in st.session_state or st.session_state.curr_lesson != lesson_key:
        fname = f"vo_{int(time.time())}.mp3"
        with st.spinner(ui["audio_gen"]):
            asyncio.run(make_audio(lesson_data, fname))
            st.session_state.final_audio = fname
            st.session_state.curr_lesson = lesson_key
    st.audio(st.session_state.final_audio)
    
    # 渲染双翼卡片
    p_class = "" if show_pinyin else "hide-pinyin"
    full_plain_text = ""
    
    html_card = f'<div class="reading-card {p_class}">'
    for line in lesson_data:
        html_card += '<div class="line-container">'
        
        # 左翼：姓名 + 中文
        html_card += f'<div class="left-zone"><div class="role-label">{line["r"]}</div><div class="text-content">'
        for char, py in line["t"]:
            if show_pinyin and py:
                html_card += f'<ruby>{char}<rt>{py}</rt></ruby>'
            else:
                html_card += f'<ruby style="line-height:1.4;">{char}</ruby>'
            full_plain_text += char
        html_card += '</div></div>'
        
        # 右翼：翻译框
        if show_trans:
            t_content = line["tr_en"] if ui_lang == "English" else line["tr_es"]
            html_card += f'<div class="right-zone"><span class="trans-text">{t_content}</span></div>'
            
        html_card += '</div>'
    html_card += '</div>'
    
    st.markdown(html_card, unsafe_allow_html=True)

    # 打字练习区
    st.markdown(f'<p class="instr-box">✍️ {ui["typing_instr"]}</p>', unsafe_allow_html=True)
    user_input = st.text_input("Typing Input", placeholder="Type here...", label_visibility="collapsed")
    
    if user_input:
        res_html = '<div style="background:white; padding:10px 15px; border-radius:12px; border:2px solid #eee;">'
        max_l = max(len(full_plain_text), len(user_input))
        for i in range(max_l):
            if i < len(user_input) and i < len(full_plain_text):
                color = "#2ecc71" if user_input[i] == full_plain_text[i] else "#e74c3c"
                res_html += f'<span style="color:{color}; font-size:20px; font-weight:bold;">{user_input[i]}</span>'
            elif i < len(user_input):
                res_html += f'<span style="color:#e74c3c; font-size:20px;">{user_input[i]}</span>'
        st.markdown(res_html + '</div>', unsafe_allow_html=True)
        if user_input.strip() == full_plain_text.strip(): st.balloons()

if __name__ == "__main__":
    main()
