import streamlit as st
import asyncio
import edge_tts
import os

# --- 1. 页面基本配置 ---
st.set_page_config(page_title="互动阅读 Pro", page_icon="📖", layout="centered")

# --- 2. 界面语言包 (Bilingual UI) ---
UI_TEXT = {
    "Español": {
        "settings": "Ajustes", "pinyin": "Mostrar Pinyin", "trans": "Traducción",
        "audio_btn": "🔊 Reproducir Audio", "audio_gen": "Generando voz...",
        "typing_title": "✍️ Práctica de Escritura", "perfect": "🎉 ¡Perfecto!"
    },
    "English": {
        "settings": "Settings", "pinyin": "Show Pinyin", "trans": "Show Translation",
        "audio_btn": "🔊 Play Audio", "audio_gen": "Generating voice...",
        "typing_title": "✍️ Typing Practice", "perfect": "🎉 Perfect!"
    }
}

# --- 3. 视觉设计 (CSS) - 奶油底色 + 紧凑排版 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    .stApp { background-color: #FFFBF0; }
    
    /* 核心阅读大卡片 */
    .reading-card {
        background-color: white;
        padding: 30px 40px;
        border-radius: 2rem;
        border: 4px solid #eee;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        max-width: 650px;
        margin: 0 auto;
    }

    /* 角色与文字的对齐 */
    .line-container {
        display: flex;
        margin-bottom: 25px;
        align-items: flex-start;
    }

    .role-label {
        min-width: 70px;
        font-weight: 900;
        color: #BE185D;
        font-size: 1.1em;
        padding-top: 15px;
    }

    /* 汉字+拼音单元 */
    .text-content {
        flex: 1;
        line-height: 3.8; /* 控制拼音与下一行的行距 */
    }

    ruby {
        ruby-position: under;
        padding: 0 4px;
        font-family: "Noto Serif SC", serif;
        font-size: 26px;
        font-weight: 900;
        color: #333;
    }

    rt {
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 13px;
        color: #888;
        font-weight: 700;
        padding-top: 8px; /* 汉字与拼音的垂直间距 */
    }

    .hide-pinyin rt { visibility: hidden; }

    /* 翻译样式 */
    .trans-text {
        font-size: 0.9em;
        color: #666;
        font-style: italic;
        margin-top: 5px;
        display: block;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. 数据库 (补全 Dialogue I & II) ---
LESSONS = {
    "Dialogue I": [
        {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("，", ""), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , "tr": "David, disculpe, ¿qué fecha es hoy?"},
        {"r": "大卫", "t": [("今天", "jīntiān"), ("9月1号", "jiǔ yuè yī hào"), ("。", "")] , "tr": "Hoy es 1 de septiembre."},
        {"r": "美美", "t": [("今天", "jīntiān"), ("星期几", "xīngqī jǐ"), ("？", "")] , "tr": "¿Qué día de la semana es hoy?"},
        {"r": "大卫", "t": [("星期三", "xīngqī sān"), ("。", "")] , "tr": "Miércoles."},
        {"r": "美美", "t": [("明天", "míngtiān"), ("几月几号", "jǐ yuè jǐ hào"), ("？", "")] , "tr": "¿Qué fecha es mañana?"},
        {"r": "大卫", "t": [("明天", "míngtiān"), ("9月2号", "jiǔ yuè èr hào"), ("。", "")] , "tr": "Mañana es 2 de septiembre."},
        {"r": "美美", "t": [("昨天", "zuótiān"), ("呢", "ne"), ("？", "")] , "tr": "¿Y ayer?"},
        {"r": "大卫", "t": [("昨天", "zuótiān"), ("是", "shì"), ("8月31号", "bā yuè sānshíyī hào"), ("。", "")] , "tr": "Ayer fue 31 de agosto."}
    ],
    "Dialogue II": [
        {"r": "美美", "t": [("明天", "míngtiān"), ("是", "shì"), ("星期六", "xīngqīliù"), ("，", ""), ("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("吗", "ma"), ("？", "")] , "tr": "Mañana es sábado, ¿vas a la escuela?"},
        {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("。", "")] , "tr": "Sí, voy."},
        {"r": "美美", "t": [("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("做", "zuò"), ("什么", "shénme"), ("？", "")] , "tr": "¿A qué vas a la escuela?"},
        {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("学校", "xuéxiào"), ("看书", "kànshū"), ("。", ""), ("你", "nǐ"), ("吗", "ma"), ("？", "")] , "tr": "Voy a leer. ¿Y tú?"},
        {"r": "美美", "t": [("我", "wǒ"), ("不", "bù"), ("去", "qù"), ("。", ""), ("我", "wǒ"), ("去", "qù"), ("我", "wǒ"), ("的", "de"), ("西班牙朋友", "Xībānyá péngyou"), ("家", "jiā"), ("看猫", "kàn māo"), ("。", "")] , "tr": "No voy. Voy a casa de mi amigo español a ver el gato."},
        {"r": "大卫", "t": [("是", "shì"), ("去", "qù"), ("西西", "Xīxi"), ("家", "jiā"), ("吗", "ma"), ("？", "")] , "tr": "¿Vas a casa de Xixi?"},
        {"r": "美美", "t": [("是的", "shìde"), ("。", "")] , "tr": "Sí."},
        {"r": "大卫", "t": [("西西", "Xīxi"), ("家", "jiā"), ("有", "yǒu"), ("几", "jǐ"), ("只", "zhī"), ("猫", "māo"), ("？", "")] , "tr": "¿Cuántos gatos tiene Xixi?"},
        {"r": "美美", "t": [("他", "tā"), ("有", "yǒu"), ("两", "liǎng"), ("只", "zhī"), ("猫", "māo"), ("。", "")] , "tr": "Tiene dos gatos."}
    ]
}

# --- 5. 核心逻辑：语音生成 ---
async def generate_dialogue_audio(lesson_data):
    ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>"
    for line in lesson_data:
        # 美美 (Xiaoxiao) / 大卫 (Yunxi)
        voice = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
        # 提取纯文本用于朗读
        text = "".join([pair[0] for pair in line["t"]])
        ssml += f"<voice name='{voice}'>{text}</voice><break time='600ms'/>"
    ssml += "</speak>"
    await edge_tts.Communicate(ssml).save("dialogue.mp3")

# --- 6. 主程序 ---
def main():
    with st.sidebar:
        st.title("⚙️ Ajustes")
        ui_lang = st.selectbox("Language / Idioma", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        st.divider()
        lesson_key = st.selectbox("Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle(ui["pinyin"], True)
        show_trans = st.toggle(ui["trans"], False)

    st.title(lesson_key)
    lesson_data = LESSONS[lesson_key]

    # 音频播放
    if "l_key" not in st.session_state or st.session_state.l_key != lesson_key:
        with st.spinner(ui["audio_gen"]):
            asyncio.run(generate_dialogue_audio(lesson_data))
            st.session_state.l_key = lesson_key
    st.audio("dialogue.mp3")

    # 渲染单一大卡片
    p_class = "" if show_pinyin else "hide-pinyin"
    full_plain_text = ""
    
    st.markdown(f'<div class="reading-card {p_class}">', unsafe_allow_html=True)
    for line in lesson_data:
        html = f'<div class="line-container"><div class="role-label">{line["r"]}</div><div class="text-content">'
        for char, py in line["t"]:
            html += f'<ruby>{char}<rt>{py}</rt></ruby>'
            full_plain_text += char
        if show_trans:
            html += f'<span class="trans-text">{line["tr"]}</span>'
        html += '</div></div>'
        st.markdown(html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 打字练习回归
    st.divider()
    st.subheader(ui["typing_title"])
    user_input = st.text_area("Type here...", label_visibility="collapsed")
    if user_input:
        res = '<div style="background:white; padding:20px; border-radius:1rem; border:2px solid #eee; line-height:2;">'
        max_l = max(len(full_plain_text), len(user_input))
        for i in range(max_l):
            if i < len(user_input) and i < len(full_plain_text):
                color = "#2ecc71" if user_input[i] == full_plain_text[i] else "#e74c3c; text-decoration:line-through;"
                res += f'<span style="color:{color}; font-size:22px; font-weight:bold;">{user_input[i]}</span>'
            elif i < len(user_input):
                res += f'<span style="color:#e74c3c; font-size:22px;">{user_input[i]}</span>'
            else:
                res += '<span style="color:#ddd; font-size:22px;">_</span>'
        st.markdown(res + '</div>', unsafe_allow_html=True)
        if user_input.strip() == full_plain_text.strip():
            st.balloons()
            st.success(ui["perfect"])

if __name__ == "__main__":
    main()
