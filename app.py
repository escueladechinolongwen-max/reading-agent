import streamlit as st
import asyncio
import edge_tts
import os
import time
import random

# --- 1. 页面基本配置 ---
st.set_page_config(page_title="阅读智能体 Pro", page_icon="📖", layout="centered")

# --- 2. 界面 UI 语言包 (增加了详细的打字练习说明) ---
UI_TEXT = {
    "Español": {
        "pinyin": "Pinyin", 
        "trans": "Traducción", 
        "audio_gen": "Afinando voz...",
        "typing_title": "✍️ Práctica de Escritura",
        "typing_instruction": "Escribe el texto de arriba aquí para mejorar tu habilidad de escritura.",
        "perfect": "🎉 ¡Excelente trabajo!"
    },
    "English": {
        "pinyin": "Pinyin", 
        "trans": "Translation", 
        "audio_gen": "Fine-tuning voice...",
        "typing_title": "✍️ Typing Practice",
        "typing_instruction": "Type the text above here to practice your typing skills.",
        "perfect": "🎉 Perfect work!"
    }
}

# --- 3. 视觉设计 (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    .stApp { background-color: #FFFBF0; }
    
    .reading-card {
        background-color: white;
        padding: 15px 25px;
        border-radius: 2rem;
        border: 4px solid white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        max-width: 700px;
        margin: 0 auto;
    }

    .line-container { display: flex; margin-bottom: 2px; align-items: flex-start; padding-bottom: 2px; }

    .role-label {
        min-width: 60px;
        font-weight: 900;
        color: #BE185D; /* 角色：胭脂红 */
        font-size: 1.05em;
        padding-top: 10px;
        font-family: 'Noto Serif SC', serif;
    }

    .text-content { flex: 1; line-height: 2.7; }

    ruby {
        ruby-position: under;
        padding: 0 3px;
        font-family: "Noto Serif SC", serif;
        font-size: 23px; 
        font-weight: 900;
        color: #333;
    }

    rt {
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 12px;
        color: #27ae60 !important; /* 拼音：绿色 */
        font-weight: 700;
        padding-top: 6px !important;
    }

    .trans-text { 
        font-size: 0.85em; 
        color: #1d4ed8; /* 翻译：蓝色 */
        font-family: 'Noto Sans SC', sans-serif;
        font-weight: 600;
        font-style: italic; 
        margin-left: 10px;
        opacity: 0.9;
    }

    .hide-pinyin rt { display: none !important; }
    .hide-pinyin .text-content { line-height: 1.6 !important; }
    .hide-pinyin .role-label { padding-top: 4px !important; }

    .block-container { padding-top: 1.5rem !important; }
    
    /* 专门为练习说明设计的样式 */
    .instruction-text {
        font-size: 0.9em;
        color: #666;
        margin-bottom: 5px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. 数据库：包含精准的双语翻译 ---
LESSONS = {
    "Dialogue I": {
        "data": [
            {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("，", ""), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , 
             "tr_es": "David, ¿qué fecha es hoy?", "tr_en": "David, excuse me, what's the date today?"},
            {"r": "大卫", "t": [("今天", "jīntiān"), ("9月1号", "jiǔ yuè yī hào"), ("。", "")] , 
             "tr_es": "Hoy es 1 de septiembre.", "tr_en": "Today is September 1st."},
            {"r": "美美", "t": [("今天", "jīntiān"), ("星期几", "xīngqī jǐ"), ("？", "")] , 
             "tr_es": "¿Qué día es hoy?", "tr_en": "What day of the week is today?"},
            {"r": "大卫", "t": [("星期三", "xīngqī sān"), ("。", "")] , 
             "tr_es": "Miércoles.", "tr_en": "Wednesday."},
            {"r": "美美", "t": [("明天", "míngtiān"), ("几月几号", "jǐ yuè jǐ hào"), ("？", "")] , 
             "tr_es": "¿Qué fecha es mañana?", "tr_en": "What's the date tomorrow?"},
            {"r": "大卫", "t": [("明天", "míngtiān"), ("9月2号", "jiǔ yuè èr hào"), ("。", "")] , 
             "tr_es": "Mañana es 2 de sept.", "tr_en": "Tomorrow is September 2nd."},
            {"r": "美美", "t": [("昨天", "zuótiān"), ("呢", "ne"), ("？", "")] , 
             "tr_es": "¿Y ayer?", "tr_en": "And yesterday?"},
            {"r": "大卫", "t": [("昨天", "zuótiān"), ("是", "shì"), ("8月31号", "bā yuè sānshíyī hào"), ("。", "")] , 
             "tr_es": "Ayer fue 31 de agosto.", "tr_en": "Yesterday was August 31st."}
        ],
        "audio": [("Xiaoxiao", "大卫，请问，今天几号？"), ("Yunxi", "今天九月一号。"), ("Xiaoxiao", "今天星期几？"), ("Yunxi", "星期三。"), ("Xiaoxiao", "明天几月几号？"), ("Yunxi", "明天九月二号。"), ("Xiaoxiao", "昨天呢？"), ("Yunxi", "昨天是八月三十一号。")]
    },
    "Dialogue II": {
        "data": [
            {"r": "美美", "t": [("明天", "míngtiān"), ("是", "shì"), ("星期六", "xīngqīliù"), ("，", ""), ("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("吗", "ma"), ("？", "")] , 
             "tr_es": "¿Vas a la escuela mañana?", "tr_en": "Tomorrow is Saturday, are you going to school?"},
            {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("。", "")] , 
             "tr_es": "Sí, voy.", "tr_en": "Yes, I am."},
            {"r": "美美", "t": [("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("做", "zuò"), ("什么", "shénme"), ("？", "")] , 
             "tr_es": "¿A qué vas?", "tr_en": "What are you going to do at school?"},
            {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("学校", "xuéxiào"), ("看书", "kànshū"), ("。", ""), ("你", "nǐ"), ("吗", "ma"), ("？", "")] , 
             "tr_es": "A leer. ¿Y tú?", "tr_en": "I'm going to read books. And you?"},
            {"r": "美美", "t": [("我", "wǒ"), ("不", "bù"), ("去", "qù"), ("。", ""), ("我", "wǒ"), ("去", "qù"), ("我", "wǒ"), ("的", "de"), ("西班牙朋友", "Xībānyá péngyou"), ("家", "jiā"), ("看猫", "kàn māo"), ("。", "")] , 
             "tr_es": "No voy. Voy a casa de mi amigo.", "tr_en": "I'm not going. I'm going to my Spanish friend's house to see the cat."},
            {"r": "大卫", "t": [("是", "shì"), ("去", "qù"), ("西西", "Xīxi"), ("家", "jiā"), ("吗", "ma"), ("？", "")] , 
             "tr_es": "¿A casa de Xixi?", "tr_en": "Are you going to Xixi's house?"},
            {"r": "美美", "t": [("是的", "shìde"), ("。", "")] , 
             "tr_es": "Sí.", "tr_en": "Yes."},
            {"r": "大卫", "t": [("西西", "Xīxi"), ("家", "jiā"), ("有", "yǒu"), ("几", "jǐ"), ("只", "zhī"), ("猫", "māo"), ("？", "")] , 
             "tr_es": "¿Cuántos gatos?", "tr_en": "How many cats does Xixi have?"},
            {"r": "美美", "t": [("他", "tā"), ("有", "yǒu"), ("两", "liǎng"), ("只", "zhī"), ("猫", "māo"), ("。", "")] , 
             "tr_es": "Tiene dos.", "tr_en": "He has two cats."}
        ],
        "audio": [("Xiaoxiao", "明天是星期六，你去学校吗？"), ("Yunxi", "我去。"), ("Xiaoxiao", "你去学校做什么？"), ("Yunxi", "我去学校看书。你呢？"), ("Xiaoxiao", "我不去。我去我的西班牙朋友家看猫真实版。"), ("Yunxi", "是去西西家吗？"), ("Xiaoxiao", "是的。"), ("Yunxi", "西西家有几只猫？"), ("Xiaoxiao", "他有两只猫。")]
    }
}

# --- 5. 音频逻辑 ---
async def make_voice(script, filename):
    ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>"
    for voice, text in script:
        v_name = f"zh-CN-{voice}Neural"
        ssml += f"<voice name='{v_name}'>{text}</voice><break time='350ms'/>"
    ssml += "</speak>"
    await edge_tts.Communicate(ssml).save(filename)

# --- 6. 主程序 ---
def main():
    if "audio_file" not in st.session_state: st.session_state.audio_file = ""

    with st.sidebar:
        ui_lang = st.selectbox("Language / Idioma", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        lesson_key = st.selectbox("Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)

    st.subheader(lesson_key)
    lesson = LESSONS[lesson_key]
    
    # 语音生成
    if "current_l" not in st.session_state or st.session_state.current_l != lesson_key:
        fname = f"voice_{int(time.time())}.mp3"
        with st.spinner(ui["audio_gen"]):
            asyncio.run(make_voice(lesson["audio"], fname))
            st.session_state.audio_file = fname
            st.session_state.current_l = lesson_key
    
    st.audio(st.session_state.audio_file)
    
    p_class = "" if show_pinyin else "hide-pinyin"
    full_plain_text = ""
    
    # 渲染大卡片
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

    # 打字练习指令说明
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<p class="instruction-text">✍️ {ui["typing_instruction"]}</p>', unsafe_allow_html=True)
    
    user_input = st.text_input(ui["typing_title"], placeholder="Type here...", label_visibility="collapsed")
    
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
