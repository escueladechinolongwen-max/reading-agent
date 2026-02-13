import streamlit as st
import asyncio
import edge_tts
import os
import time
import random

# --- 1. 页面基本配置 ---
st.set_page_config(page_title="阅读 Pro", page_icon="📖", layout="centered")

# --- 2. 界面语言包 ---
UI_TEXT = {
    "Español": {
        "pinyin": "Pinyin", "trans": "Traducción", "audio_gen": "Cargando...",
        "typing": "✍️ Práctica", "perfect": "🎉 ¡Excelente!"
    },
    "English": {
        "pinyin": "Pinyin", "trans": "Translation", "audio_gen": "Loading...",
        "typing": "✍️ Practice", "perfect": "🎉 Perfect!"
    }
}

# --- 3. 视觉设计 (CSS) - 极致紧凑版 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    .stApp { background-color: #FFFBF0; }
    
    /* 大卡片：缩小内边距 */
    .reading-card {
        background-color: white;
        padding: 10px 20px;
        border-radius: 1.2rem;
        border: 1px solid #eee;
        max-width: 680px;
        margin: 0 auto;
    }

    /* 对话行：极致压缩间距 */
    .line-container {
        display: flex;
        margin-bottom: 2px;
        align-items: flex-start;
    }

    .role-label {
        min-width: 50px;
        font-weight: 900;
        color: #BE185D;
        font-size: 0.9em;
        margin-right: 8px;
        padding-top: 10px;
    }

    .text-content { flex: 1; line-height: 2.0; }

    /* 汉字与拼音：进一步缩小字号以适配屏幕 */
    ruby {
        ruby-position: under;
        padding: 0 1px;
        font-family: "Noto Serif SC", serif;
        font-size: 19px; 
        font-weight: 900;
        color: #333;
    }

    rt {
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 11px;
        color: #999;
        font-weight: 700;
        padding-top: 0px;
    }

    /* 拼音开关强制生效逻辑 */
    .hide-pinyin rt { visibility: hidden !important; height: 0px !important; display: block !important; }
    .hide-pinyin ruby { line-height: 1.2 !important; }

    .trans-text { font-size: 0.8em; color: #888; font-style: italic; margin-left: 5px; }
    
    /* 隐藏 Streamlit 默认的多余间距 */
    .block-container { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. 数据库 ---
LESSONS = {
    "Dialogue I": {
        "data": [
            {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("，", ""), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , "tr": "David, ¿qué fecha es hoy?"},
            {"r": "大卫", "t": [("今天", "jīntiān"), ("9月1号", "jiǔ yuè yī hào"), ("。", "")] , "tr": "Hoy es 1 de sept."},
            {"r": "美美", "t": [("今天", "jīntiān"), ("星期几", "xīngqī jǐ"), ("？", "")] , "tr": "¿Qué día es?"},
            {"r": "大卫", "t": [("星期三", "xīngqī sān"), ("。", "")] , "tr": "Miércoles."},
            {"r": "美美", "t": [("明天", "míngtiān"), ("几月几号", "jǐ yuè jǐ hào"), ("？", "")] , "tr": "¿Fecha de mañana?"},
            {"r": "大卫", "t": [("明天", "míngtiān"), ("9月2号", "jiǔ yuè èr hào"), ("。", "")] , "tr": "Mañana 2 sept."},
            {"r": "美美", "t": [("昨天", "zuótiān"), ("呢", "ne"), ("？", "")] , "tr": "¿Y ayer?"},
            {"r": "大卫", "t": [("昨天", "zuótiān"), ("是", "shì"), ("8月31号", "bā yuè sānshíyī hào"), ("。", "")] , "tr": "Ayer fue 31 ago."}
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
            {"r": "大卫", "t": [("西西", "Xīxi"), ("家", "jiā"), ("有", "yǒu"), ("几", "jǐ"), ("只", "zhī"), ("猫", "māo"), ("？", "")] , "tr": "¿Cuántas gatas?"},
            {"r": "美美", "t": [("他", "tā"), ("有", "yǒu"), ("两", "liǎng"), ("只", "zhī"), ("猫", "māo"), ("。", "")] , "tr": "Tiene dos."}
        ],
        "audio": [("Xiaoxiao", "明天是星期六，你去学校吗？"), ("Yunxi", "我去。"), ("Xiaoxiao", "你去学校做什么？"), ("Yunxi", "我去学校看书。你呢？"), ("Xiaoxiao", "我不去。我去我的西班牙朋友家看猫。"), ("Yunxi", "是去西西家吗？"), ("Xiaoxiao", "是的。"), ("Yunxi", "西西家有几只猫？"), ("Xiaoxiao", "他有两只猫。")]
    }
}

# --- 5. 音频逻辑 (解决 Cloud 报错) ---
async def make_voice(script, filename):
    ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>"
    for voice, text in script:
        v_name = f"zh-CN-{voice}Neural"
        ssml += f"<voice name='{v_name}'>{text}</voice><break time='300ms'/>"
    ssml += "</speak>"
    await edge_tts.Communicate(ssml).save(filename)

# --- 6. 主程序 ---
def main():
    # 初始化状态
    if "audio_file" not in st.session_state:
        st.session_state.audio_file = ""

    with st.sidebar:
        ui_lang = st.selectbox("Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        lesson_key = st.selectbox("Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)

    lesson = LESSONS[lesson_key]
    
    # 语音处理：使用随机名防止缓存/读取冲突
    if "current_l" not in st.session_state or st.session_state.current_l != lesson_key:
        fname = f"voice_{int(time.time())}_{random.randint(1,100)}.mp3"
        with st.spinner(ui["audio_gen"]):
            asyncio.run(make_voice(lesson["audio"], fname))
            st.session_state.audio_file = fname
            st.session_state.current_l = lesson_key
    
    # 紧凑布局渲染
    st.audio(st.session_state.audio_file)
    
    p_class = "" if show_pinyin else "hide-pinyin"
    full_plain_text = ""
    
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

    # 底部打字区
    user_input = st.text_input(ui["typing"], placeholder="Type here...")
    if user_input:
        res = '<div style="background:white; padding:8px 15px; border-radius:10px; border:1px solid #eee; margin-top:5px;">'
        max_l = max(len(full_plain_text), len(user_input))
        for i in range(max_l):
            if i < len(user_input) and i < len(full_plain_text):
                color = "#2ecc71" if user_input[i] == full_plain_text[i] else "#e74c3c"
                res += f'<span style="color:{color}; font-size:18px; font-weight:bold;">{user_input[i]}</span>'
            elif i < len(user_input):
                res += f'<span style="color:#e74c3c; font-size:18px;">{user_input[i]}</span>'
        st.markdown(res + '</div>', unsafe_allow_html=True)
        if user_input.strip() == full_plain_text.strip():
            st.balloons()

if __name__ == "__main__":
    main()
