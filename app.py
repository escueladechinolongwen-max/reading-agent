import streamlit as st
import asyncio
import edge_tts
import os
import streamlit.components.v1 as components

# --- 1. 页面配置 ---
st.set_page_config(page_title="互动阅读 Pro", page_icon="📖", layout="centered")

# --- 2. 界面语言包 (Bilingual UI) ---
UI_TEXT = {
    "Español": {
        "settings": "Ajustes", "pinyin": "Mostrar Pinyin", "trans": "Traducción",
        "typing_title": "✍️ Práctica de Escritura", "typing_hint": "Escribe aquí...",
        "audio_gen": "Generando voz...", "grammar_lib": "📚 Biblioteca de Gramática",
        "perfect": "🎉 ¡Perfecto! Todo correcto."
    },
    "English": {
        "settings": "Settings", "pinyin": "Show Pinyin", "trans": "Translation",
        "typing_title": "✍️ Typing Practice", "typing_hint": "Type here...",
        "audio_gen": "Generating voice...", "grammar_lib": "📚 Grammar Library",
        "perfect": "🎉 Perfect! You got it."
    }
}

# --- 3. 语法图书馆 (HTML 内容嵌入) ---
# 注意：这里请粘贴您之前那 4 个 HTML 的内容
HTML_TIME = """ (粘贴 complementotime.html 内容) """
HTML_FECHAS = """ (粘贴 fechas.html 内容) """
HTML_QING = """ (粘贴 qing.html 内容) """
HTML_QU = """ (粘贴 qu.html 内容) """

GRAMMAR_LIB = {
    "time": "时间位置 (Time Position)",
    "fechas": "日期 (Dates)",
    "qing": "请 (Please)",
    "qu": "去 (Go)"
}

# --- 4. 视觉设计 (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    .stApp { background-color: #FFFBF0; }
    
    /* 聊天区域限宽 */
    .main-container { max-width: 650px; margin: 0 auto; }

    .chat-bubble {
        background-color: white;
        padding: 20px 25px;
        border-radius: 1.5rem;
        border: 3px solid #eee;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        line-height: 3.5; /* 拼音行高 */
    }

    .role-label { font-weight: 900; color: #BE185D; margin-bottom: 8px; display: block; font-size: 1.1em; }

    /* 核心排版：自动换行的 Ruby */
    ruby {
        ruby-position: under;
        padding: 0 4px;
        font-family: "Noto Serif SC", serif;
        font-size: 26px;
        font-weight: 900;
        color: #333;
        display: inline-block; /* 允许自动换行 */
    }

    rt {
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 13px;
        color: #888;
        font-weight: 700;
        padding-top: 8px;
    }

    .hide-pinyin rt { visibility: hidden; }
    
    /* 打字反馈样式 */
    .char-correct { color: #2ecc71; font-weight: bold; font-size: 20px; }
    .char-wrong { color: #e74c3c; text-decoration: line-through; font-size: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 5. 数据库 (完全补全) ---
LESSONS = {
    "Dialogue I": {
        "data": [
            {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("，", ""), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")]},
            {"r": "大卫", "t": [("今天", "jīntiān"), ("9月1号", "jiǔ yuè yī hào"), ("。", "")]},
            {"r": "美美", "t": [("今天", "jīntiān"), ("星期几", "xīngqī jǐ"), ("？", "")]},
            {"r": "大卫", "t": [("星期三", "xīngqī sān"), ("。", "")]},
            {"r": "美美", "t": [("明天", "míngtiān"), ("几月几号", "jǐ yuè jǐ hào"), ("？", "")]},
            {"r": "大卫", "t": [("明天", "míngtiān"), ("9月2号", "jiǔ yuè èr hào"), ("。", "")]},
            {"r": "美美", "t": [("昨天", "zuótiān"), ("呢", "ne"), ("？", "")]},
            {"r": "大卫", "t": [("昨天", "zuótiān"), ("是", "shì"), ("8月31号", "bā yuè sānshíyī hào"), ("。", "")]}
        ],
        "audio_script": [("Xiaoxiao", "大卫，请问，今天几号？"), ("Yunxi", "今天九月一号。"), ("Xiaoxiao", "今天星期几？"), ("Yunxi", "星期三。"), ("Xiaoxiao", "明天几月几号？"), ("Yunxi", "明天九月二号。"), ("Xiaoxiao", "昨天呢？"), ("Yunxi", "昨天是八月三十一号。")],
        "trans": "ES: David, disculpe, ¿qué fecha es hoy? David: Hoy es 1 de septiembre..."
    },
    "Dialogue II": {
        "data": [
            {"r": "美美", "t": [("明天", "míngtiān"), ("是", "shì"), ("星期六", "xīngqīliù"), ("，", ""), ("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("吗", "ma"), ("？", "")]},
            {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("。", "")]},
            {"r": "美美", "t": [("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("做", "zuò"), ("什么", "shénme"), ("？", "")]},
            {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("学校", "xuéxiào"), ("看书", "kànshū"), ("。", ""), ("你", "nǐ"), ("吗", "ma"), ("？", "")]},
            {"r": "美美", "t": [("我", "wǒ"), ("不", "bù"), ("去", "qù"), ("。", ""), ("我", "wǒ"), ("去", "qù"), ("我", "wǒ"), ("的", "de"), ("西班牙朋友", "Xībānyá péngyou"), ("家", "jiā"), ("看猫", "kàn māo"), ("。", "")]},
            {"r": "大卫", "t": [("是", "shì"), ("去", "qù"), ("西西", "Xīxi"), ("家", "jiā"), ("吗", "ma"), ("？", "")]},
            {"r": "美美", "t": [("是的", "shìde"), ("。", "")]},
            {"r": "大卫", "t": [("西西", "Xīxi"), ("家", "jiā"), ("有", "yǒu"), ("几", "jǐ"), ("只", "zhī"), ("猫", "māo"), ("？", "")]},
            {"r": "美美", "t": [("他", "tā"), ("有", "yǒu"), ("两", "liǎng"), ("只", "zhī"), ("猫", "māo"), ("。", "")]}
        ],
        "audio_script": [("Xiaoxiao", "明天是星期六，你去学校吗？"), ("Yunxi", "我去。"), ("Xiaoxiao", "你去学校做什么？"), ("Yunxi", "我去学校看书。你呢？"), ("Xiaoxiao", "我不去。我去我的西班牙朋友家看猫。"), ("Yunxi", "是去西西家吗？"), ("Xiaoxiao", "是的。"), ("Yunxi", "西西家有几只猫？"), ("Xiaoxiao", "他有两只猫。")],
        "trans": "ES: Mañana es sábado, ¿vas a la escuela? David: Sí, voy. Meimei: ¿A qué vas? David: A leer..."
    }
}

# --- 6. 核心逻辑：分角色配音 ---
async def make_audio(script):
    ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>"
    for voice, text in script:
        v_name = f"zh-CN-{voice}Neural"
        ssml += f"<voice name='{v_name}'>{text}</voice><break time='600ms'/>"
    ssml += "</speak>"
    await edge_tts.Communicate(ssml).save("pro_voice.mp3")

# --- 7. 主程序 ---
def main():
    with st.sidebar:
        st.title("⚙️ Settings")
        ui_lang = st.selectbox("Language / Idioma", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        st.divider()
        lesson_key = st.selectbox("Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle(ui["pinyin"], True)
        show_trans = st.toggle(ui["trans"], False)

    st.title(lesson_key)
    lesson = LESSONS[lesson_key]
    
    # 语音
    if "l_key" not in st.session_state or st.session_state.l_key != lesson_key:
        with st.spinner(ui["audio_gen"]):
            asyncio.run(make_audio(lesson["audio_script"]))
            st.session_state.l_key = lesson_key
    st.audio("pro_voice.mp3")

    # 文章渲染 (窄屏容器)
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    full_plain_text = ""
    p_class = "" if show_pinyin else "hide-pinyin"
    
    for line in lesson["data"]:
        html = f'<span class="role-label">{line["r"]}</span><div class="chat-bubble {p_class}">'
        for word, py in line["t"]:
            html += f'<ruby>{word}<rt>{py}</rt></ruby>'
            full_plain_text += word
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if show_trans:
        st.info(lesson["trans"])

    # 语法展示 (点击下方按钮展开，不破坏排版)
    st.divider()
    st.subheader(ui["grammar_lib"])
    g_cols = st.columns(len(GRAMMAR_LIB))
    for i, (gid, gname) in enumerate(GRAMMAR_LIB.items()):
        if g_cols[i].button(f"📘 {gname}", use_container_width=True):
            st.session_state.active_g = gid

    if "active_g" in st.session_state:
        g_id = st.session_state.active_g
        html_map = {"time": HTML_TIME, "fechas": HTML_FECHAS, "qing": HTML_QING, "qu": HTML_QU}
        components.html(html_map[g_id], height=600, scrolling=True)
        if st.button("❌ Close"):
            del st.session_state.active_g
            st.rerun()

    # 打字练习
    st.divider()
    st.subheader(ui["typing_title"])
    user_input = st.text_area(ui["typing_hint"], height=100, label_visibility="collapsed")
    if user_input:
        res_html = '<div style="background:white; padding:15px; border-radius:1rem; border:2px solid #eee;">'
        max_l = max(len(full_plain_text), len(user_input))
        for i in range(max_l):
            if i < len(user_input) and i < len(full_plain_text):
                if user_input[i] == full_plain_text[i]:
                    res_html += f'<span class="char-correct">{user_input[i]}</span>'
                else:
                    res_html += f'<span class="char-wrong">{user_input[i]}</span>'
            elif i < len(user_input):
                res_html += f'<span class="char-wrong">{user_input[i]}</span>'
            else:
                res_html += '<span style="color:#ddd;">_</span>'
        st.markdown(res_html + '</div>', unsafe_allow_html=True)
        if user_input.strip() == full_plain_text.strip():
            st.balloons()
            st.success(ui["perfect"])

if __name__ == "__main__":
    main()
