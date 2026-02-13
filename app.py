import streamlit as st
import asyncio
import edge_tts
import os
import time
import random

# --- 1. 页面配置 ---
st.set_page_config(page_title="阅读智能体 Pro", page_icon="📖", layout="centered")

# --- 2. 语言包 (含打字说明) ---
UI_TEXT = {
    "Español": {
        "pinyin": "Pinyin", "trans": "Traducción", "audio_gen": "Afinando voces...",
        "typing_title": "✍️ Práctica de Escritura",
        "typing_instruction": "Escribe el texto de arriba aquí para mejorar tu habilidad de escritura.",
        "perfect": "🎉 ¡Excelente!"
    },
    "English": {
        "pinyin": "Pinyin", "trans": "Translation", "audio_gen": "Fine-tuning voices...",
        "typing_title": "✍️ Typing Practice",
        "typing_instruction": "Type the text above here to practice your typing skills.",
        "perfect": "🎉 Perfect!"
    }
}

# --- 3. 视觉设计 (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    .stApp { background-color: #FFFBF0; }
    
    .reading-card {
        background-color: white; padding: 20px 30px; border-radius: 2rem;
        border: 4px solid white; box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        max-width: 700px; margin: 0 auto;
    }

    .line-container { display: flex; margin-bottom: 5px; align-items: flex-start; }

    .role-label {
        min-width: 65px; font-weight: 900; color: #BE185D; 
        font-size: 1.05em; padding-top: 12px; font-family: 'Noto Serif SC', serif;
    }

    .text-content { flex: 1; line-height: 2.8; }

    ruby {
        ruby-position: under; padding: 0 3px; font-family: "Noto Serif SC", serif;
        font-size: 24px; font-weight: 900; color: #333;
    }

    rt {
        font-family: 'Noto Sans SC', sans-serif; font-size: 12px;
        color: #27ae60 !important; /* 拼音：绿色 */
        font-weight: 700; padding-top: 10px !important; /* 间距拉开 */
    }

    .trans-text { 
        font-size: 0.85em; color: #1d4ed8; /* 翻译：蓝色 */
        font-family: 'Noto Sans SC', sans-serif; font-weight: 600;
        font-style: italic; margin-left: 10px;
    }

    /* 拼音关闭时的紧凑处理 */
    .hide-pinyin rt { display: none !important; }
    .hide-pinyin .text-content { line-height: 1.8 !important; }
    .hide-pinyin .role-label { padding-top: 6px !important; }

    .instruction-text { font-size: 0.9em; color: #666; font-weight: 700; margin-bottom: 5px; }
    .block-container { padding-top: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. 数据库 ---
LESSONS = {
    "Dialogue I": {
        "data": [
            {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("，", ""), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , "tr_es": "David, ¿qué fecha es hoy?", "tr_en": "David, what's the date today?"},
            {"r": "大卫", "t": [("今天", "jīntiān"), ("9月1号", "jiǔ yuè yī hào"), ("。", "")] , "tr_es": "Hoy es 1 de septiembre.", "tr_en": "Today is September 1st."},
            {"r": "美美", "t": [("今天", "jīntiān"), ("星期几", "xīngqī jǐ"), ("？", "")] , "tr_es": "¿Qué día es hoy?", "tr_en": "What day is today?"},
            {"r": "大卫", "t": [("星期三", "xīngqī sān"), ("。", "")] , "tr_es": "Miércoles.", "tr_en": "Wednesday."}
        ],
        "audio_script": [("Xiaoxiao", "大卫，请问，今天几号？"), ("Yunxi", "今天九月一号。"), ("Xiaoxiao", "今天星期几？"), ("Yunxi", "星期三。")]
    },
    "Dialogue II": {
        "data": [
            {"r": "美美", "t": [("明天", "míngtiān"), ("是", "shì"), ("星期六", "xīngqīliù"), ("，", ""), ("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("吗", "ma"), ("？", "")] , "tr_es": "¿Vas a la escuela mañana?", "tr_en": "Are you going to school tomorrow?"},
            {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("。", "")] , "tr_es": "Sí, voy.", "tr_en": "Yes, I am."},
            {"r": "美美", "t": [("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("做", "zuò"), ("什么", "shénme"), ("？", "")] , "tr_es": "¿A qué vas?", "tr_en": "What will you do there?"},
            {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("学校", "xuéxiào"), ("看书", "kànshū"), ("。", ""), ("你", "nǐ"), ("吗", "ma"), ("？", "")] , "tr_es": "A leer. ¿Y tú?", "tr_en": "To read. And you?"},
            {"r": "美美", "t": [("我", "wǒ"), ("不", "bù"), ("去", "qù"), ("。", ""), ("我", "wǒ"), ("去", "qù"), ("我", "wǒ"), ("的", "de"), ("西班牙朋友", "Xībānyá péngyou"), ("家", "jiā"), ("看猫", "kàn māo"), ("。", "")] , "tr_es": "No, voy a casa de mi amigo.", "tr_en": "No, I'm going to my friend's house."},
            {"r": "大卫", "t": [("是", "shì"), ("去", "qù"), ("西西", "Xīxi"), ("家", "jiā"), ("吗", "ma"), ("？", "")] , "tr_es": "¿A casa de Xixi?", "tr_en": "To Xixi's house?"},
            {"r": "美美", "t": [("是的", "shìde"), ("。", "")] , "tr_es": "Sí.", "tr_en": "Yes."},
            {"r": "大卫", "t": [("西西", "Xīxi"), ("家", "jiā"), ("有", "yǒu"), ("几", "jǐ"), ("只", "zhī"), ("猫", "māo"), ("？", "")] , "tr_es": "¿Cuántos gatos?", "tr_en": "How many cats?"},
            {"r": "美美", "t": [("他", "tā"), ("有", "yǒu"), ("两", "liǎng"), ("只", "zhī"), ("猫", "māo"), ("。", "")] , "tr_es": "Tiene dos.", "tr_en": "He has two."}
        ],
        "audio_script": [("Xiaoxiao", "明天是星期六，你去学校吗？"), ("Yunxi", "我去。"), ("Xiaoxiao", "你去学校做什么？"), ("Yunxi", "我去学校看书。你呢？"), ("Xiaoxiao", "我不去。我去我的西班牙朋友家看猫。"), ("Yunxi", "是去西西家吗？"), ("Xiaoxiao", "是的。"), ("Yunxi", "西西家有几只猫？"), ("Xiaoxiao", "他有两只猫。")]
    }
}

# --- 5. 核心逻辑：单一文件多声音合成 (SSML) ---
async def make_dialogue_audio(script, filename):
    # 构建 SSML 格式字符串
    ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>"
    for voice_short, text in script:
        v_full = f"zh-CN-{voice_short}Neural"
        # 给每句对话加上角色的声音标签
        ssml += f"<voice name='{v_full}'>{text}</voice><break time='450ms'/>"
    ssml += "</speak>"
    
    communicate = edge_tts.Communicate(ssml)
    await communicate.save(filename)

# --- 6. 主程序 ---
def main():
    if "audio_file" not in st.session_state: st.session_state.audio_file = ""

    with st.sidebar:
        ui_lang = st.selectbox("Language / Idioma", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        lesson_key = st.selectbox("Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)

    lesson = LESSONS[lesson_key]
    
    # 语音生成逻辑
    if "current_l" not in st.session_state or st.session_state.current_l != lesson_key:
        fname = f"voice_{int(time.time())}.mp3"
        with st.spinner(ui["audio_gen"]):
            asyncio.run(make_dialogue_audio(lesson["audio_script"], fname))
            st.session_state.audio_file = fname
            st.session_state.current_l = lesson_key
    
    st.audio(st.session_state.audio_file)
    
    # 渲染卡片
    p_class = "" if show_pinyin else "hide-pinyin"
    full_plain_text = ""
    
    html_all = f'<div class="reading-card {p_class}">'
    for line in lesson["data"]:
        html_all += f'<div class="line-container"><div class="role-label">{line["r"]}</div><div class="text-content">'
        for char, py in line["t"]:
            html_all += f'<ruby>{char}<rt>{py}</rt></ruby>'
            full_plain_text += char
        if show_trans:
            t_content = line["tr_en"] if ui_lang == "English" else line["tr_es"]
            html_all += f'<span class="trans-text">{t_content}</span>'
        html_all += '</div></div>'
    html_all += '</div>'
    st.markdown(html_all, unsafe_allow_html=True)

    # 打字练习区
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<p class="instruction-text">✍️ {ui["typing_instruction"]}</p>', unsafe_allow_html=True)
    user_input = st.text_input("Typing Practice Input", placeholder="Type here...", label_visibility="collapsed")
    
    if user_input:
        res = '<div style="background:white; padding:8px 15px; border-radius:12px; border:2px solid #eee; margin-top:5px;">'
        max_l = max(len(full_plain_text), len(user_input))
        for i in range(max_l):
            if i < len(user_input) and i < len(full_plain_text):
                color = "#2ecc71" if user_input[i] == full_plain_text[i] else "#e74c3c"
                res += f'<span style="color:{color}; font-size:18px; font-weight:bold;">{user_input[i]}</span>'
            elif i < len(user_input):
                res += f'<span style="color:#e74c3c; font-size:18px;">{user_input[i]}</span>'
        st.markdown(res + '</div>', unsafe_allow_html=True)
        if user_input.strip() == full_plain_text.strip(): st.balloons()

if __name__ == "__main__":
    main()
