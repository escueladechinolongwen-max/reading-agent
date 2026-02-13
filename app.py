import streamlit as st
import asyncio
import edge_tts
import os
import time
import random

# --- 1. 页面基本配置 ---
st.set_page_config(page_title="阅读智能体 Pro", page_icon="📖", layout="centered")

# --- 2. 界面语言包 ---
UI_TEXT = {
    "Español": {
        "pinyin": "Pinyin", "trans": "Traducción", "audio_gen": "Afinando voz...",
        "typing": "✍️ Práctica de Escritura", "perfect": "🎉 ¡Excelente trabajo!"
    },
    "English": {
        "pinyin": "Pinyin", "trans": "Translation", "audio_gen": "Fine-tuning voice...",
        "typing": "✍️ Typing Practice", "perfect": "🎉 Perfect work!"
    }
}

# --- 3. 视觉设计 (CSS) - 复刻大师级审美 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    /* 全局背景：奶油色 */
    .stApp { background-color: #FFFBF0; }
    
    /* 核心阅读大卡片 */
    .reading-card {
        background-color: white;
        padding: 20px 30px;
        border-radius: 2.5rem;
        border: 4px solid white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        max-width: 680px;
        margin: 0 auto;
    }

    /* 对话容器 */
    .line-container {
        display: flex;
        margin-bottom: 5px;
        align-items: flex-start;
        border-bottom: 1px solid #FAF5F5; /* 极淡的分割线 */
        padding-bottom: 5px;
    }

    /* 角色标签：胭脂红 */
    .role-label {
        min-width: 60px;
        font-weight: 900;
        color: #BE185D; 
        font-size: 1.1em;
        padding-top: 12px;
        font-family: 'Noto Serif SC', serif;
    }

    .text-content { flex: 1; line-height: 2.8; }

    /* 汉字与拼音的设计逻辑 */
    ruby {
        ruby-position: under;
        padding: 0 4px; /* 横向间距 */
        font-family: "Noto Serif SC", serif;
        font-size: 24px; 
        font-weight: 900;
        color: #333; /* 汉字：深色 */
    }

    rt {
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 12px;
        color: #999; /* 拼音：浅灰色 */
        font-weight: 700;
        padding-top: 10px !important; /* 👈 关键：拉开拼音和汉字的垂直距离 */
    }

    /* 拼音开关强制生效 */
    .hide-pinyin rt { display: none !important; }
    .hide-pinyin .text-content { line-height: 1.8 !important; }

    /* 翻译文本：深青色 */
    .trans-text { 
        font-size: 0.85em; 
        color: #0F766E; 
        font-family: 'Noto Sans SC', sans-serif;
        font-weight: 600;
        font-style: italic; 
        margin-left: 8px;
        opacity: 0.8;
    }

    /* 隐藏 Streamlit 默认边距 */
    .block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. 数据库 ---
LESSONS = {
    "Dialogue I": {
        "data": [
            {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("，", ""), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , "tr": "David, ¿qué fecha es hoy?"},
            {"r": "大卫", "t": [("今天", "jīntiān"), ("9月1号", "jiǔ yuè yī hào"), ("。", "")] , "tr": "Hoy es 1 de septiembre."},
            {"r": "美美", "t": [("今天", "jīntiān"), ("星期几", "xīngqī jǐ"), ("？", "")] , "tr": "¿Qué día de la semana es?"},
            {"r": "大卫", "t": [("星期三", "xīngqī sān"), ("。", "")] , "tr": "Miércoles."},
            {"r": "美美", "t": [("明天", "míngtiān"), ("几月几号", "jǐ yuè jǐ hào"), ("？", "")] , "tr": "¿Qué fecha es mañana?"},
            {"r": "大卫", "t": [("明天", "míngtiān"), ("9月2号", "jiǔ yuè èr hào"), ("。", "")] , "tr": "Mañana es 2 de sept."},
            {"r": "美美", "t": [("昨天", "zuótiān"), ("呢", "ne"), ("？", "")] , "tr": "¿Y ayer?"},
            {"r": "大卫", "t": [("昨天", "zuótiān"), ("是", "shì"), ("8月31号", "bā yuè sānshíyī hào"), ("。", "")] , "tr": "Ayer fue 31 de agosto."}
        ],
        "audio": [("Xiaoxiao", "大卫，请问，今天几号？"), ("Yunxi", "今天九月一号。"), ("Xiaoxiao", "今天星期几？"), ("Yunxi", "星期三。"), ("Xiaoxiao", "明天几月几号？"), ("Yunxi", "明天九月二号。"), ("Xiaoxiao", "昨天呢？"), ("Yunxi", "昨天是八月三十一号。")]
    },
    "Dialogue II": {
        "data": [
            {"r": "美美", "t": [("明天", "míngtiān"), ("是", "shì"), ("星期六", "xīngqīliù"), ("，", ""), ("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("吗", "ma"), ("？", "")] , "tr": "¿Vas a la escuela mañana?"},
            {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("。", "")] , "tr": "Sí, voy."},
            {"r": "美美", "t": [("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("做", "zuò"), ("什么", "shénme"), ("？", "")] , "tr": "¿A qué vas?"},
            {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("学校", "xuéxiào"), ("看书", "kànshū"), ("。", ""), ("你", "nǐ"), ("吗", "ma"), ("？", "")] , "tr": "A leer. ¿Y tú?"},
            {"r": "美美", "t": [("我", "wǒ"), ("不", "bù"), ("去", "qù"), ("。", ""), ("我", "wǒ"), ("去", "qù"), ("我", "wǒ"), ("的", "de"), ("西班牙朋友", "Xībānyá péngyou"), ("家", "jiā"), ("看猫", "kàn māo"), ("。", "")] , "tr": "Voy a casa de mi amigo."},
            {"r": "大卫", "t": [("是", "shì"), ("去", "qù"), ("西西", "Xīxi"), ("家", "jiā"), ("吗", "ma"), ("？", "")] , "tr": "¿A casa de Xixi?"},
            {"r": "美美", "t": [("是的", "shìde"), ("。", "")] , "tr": "Sí."},
            {"r": "大卫", "t": [("西西", "Xīxi"), ("家", "jiā"), ("有", "yǒu"), ("几", "jǐ"), ("只", "zhī"), ("猫", "māo"), ("？", "")] , "tr": "¿Cuántos gatos?"},
            {"r": "美美", "t": [("他", "tā"), ("有", "yǒu"), ("两", "liǎng"), ("只", "zhī"), ("猫", "māo"), ("。", "")] , "tr": "Tiene dos."}
        ],
        "audio": [("Xiaoxiao", "明天是星期六，你去学校吗？"), ("Yunxi", "我去。"), ("Xiaoxiao", "你去学校做什么？"), ("Yunxi", "我去学校看书。你呢？"), ("Xiaoxiao", "我不去。我去我的西班牙朋友家看猫。"), ("Yunxi", "是去西西家吗？"), ("Xiaoxiao", "是的。"), ("Yunxi", "西西家有几只猫？"), ("Xiaoxiao", "他有两只猫。")]
    }
}

# --- 5. 核心逻辑：语音生成 (随机名方案) ---
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
        ui_lang = st.selectbox("Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        lesson_key = st.selectbox("Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)

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
    
    # 核心渲染卡片
    html_all = f'<div class="reading-card {p_class}">'
    for line in lesson["data"]:
        html_all += f'<div class="line-container"><div class="role-label">{line["r"]}</div><div class="text-content">'
        for char, py in line["t"]:
            html_all += f'<ruby>{char}<rt>{py}</rt></ruby>'
            full_plain_text += char
        if show_trans:
            html_all += f'<span class="trans-text">{line["tr"]}</span>'
        html_all += '</div></div>'
    html_all += '</div>'
    
    st.markdown(html_all, unsafe_allow_html=True)

    # 打字区：极简紧凑
    st.markdown("<br>", unsafe_allow_html=True)
    user_input = st.text_input(ui["typing"], placeholder="Type here...")
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
