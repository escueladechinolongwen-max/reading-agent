import streamlit as st
import asyncio
import edge_tts
import os
import time
import random

# --- 1. 页面基本配置 ---
st.set_page_config(page_title="阅读智能体 Pro", page_icon="📖", layout="centered")

# --- 2. 界面 UI 语言包 (含练习说明) ---
UI_TEXT = {
    "Español": {
        "pinyin": "Pinyin", "trans": "Traducción", "audio_gen": "Generando diálogo...",
        "typing_title": "✍️ Práctica de Escritura",
        "typing_instr": "Escribe el texto de arriba aquí para mejorar tu habilidad de escritura.",
        "perfect": "🎉 ¡Excelente!"
    },
    "English": {
        "pinyin": "Pinyin", "trans": "Translation", "audio_gen": "Generating dialogue...",
        "typing_title": "✍️ Typing Practice",
        "typing_instr": "Type the text above here to practice your typing skills.",
        "perfect": "🎉 Perfect!"
    }
}

# --- 3. 视觉设计 (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    .stApp { background-color: #FFFBF0; }
    .reading-card {
        background-color: white; padding: 15px 25px; border-radius: 2rem;
        border: 4px solid white; box-shadow: 0 10px 30px rgba(0,0,0,0.04);
        max-width: 700px; margin: 0 auto;
    }
    .line-container { display: flex; margin-bottom: 5px; align-items: flex-start; }
    .role-label {
        min-width: 60px; font-weight: 900; color: #BE185D; 
        font-size: 1.05em; padding-top: 10px; font-family: 'Noto Serif SC', serif;
    }
    .text-content { flex: 1; line-height: 2.8; }
    ruby { ruby-position: under; padding: 0 3px; font-family: "Noto Serif SC", serif; font-size: 24px; font-weight: 900; color: #333; }
    rt { font-family: 'Noto Sans SC', sans-serif; font-size: 12px; color: #27ae60 !important; font-weight: 700; padding-top: 8px !important; }
    .trans-text { font-size: 0.85em; color: #1d4ed8; font-family: 'Noto Sans SC', sans-serif; font-weight: 600; font-style: italic; margin-left: 10px; }
    .instr { font-size: 0.85em; color: #666; font-weight: 700; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 4. 数据库 (完全补全 Dialogue I & II) ---
LESSONS = {
    "Dialogue I": [
        {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("，", ""), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , "tr_es": "David, disculpe, ¿qué fecha es hoy?", "tr_en": "David, excuse me, what is the date today?"},
        {"r": "大卫", "t": [("今天", "jīntiān"), ("9月1号", "jiǔ yuè yī hào"), ("。", "")] , "tr_es": "Hoy es 1 de septiembre.", "tr_en": "Today is September 1st."},
        {"r": "美美", "t": [("今天", "jīntiān"), ("星期几", "xīngqī jǐ"), ("？", "")] , "tr_es": "¿Qué día es hoy?", "tr_en": "What day of the week is today?"},
        {"r": "大卫", "t": [("星期三", "xīngqī sān"), ("。", "")] , "tr_es": "Miércoles.", "tr_en": "Wednesday."},
        {"r": "美美", "t": [("明天", "míngtiān"), ("几月几号", "jǐ yuè jǐ hào"), ("？", "")] , "tr_es": "¿Qué fecha es mañana?", "tr_en": "What's the date tomorrow?"},
        {"r": "大卫", "t": [("明天", "míngtiān"), ("9月2号", "jiǔ yuè èr hào"), ("。", "")] , "tr_es": "Mañana es 2 de sept.", "tr_en": "Tomorrow is September 2nd."},
        {"r": "美美", "t": [("昨天", "zuótiān"), ("呢", "ne"), ("？", "")] , "tr_es": "¿Y ayer?", "tr_en": "And yesterday?"},
        {"r": "大卫", "t": [("昨天", "zuótiān"), ("是", "shì"), ("8月31号", "bā yuè sānshíyī hào"), ("。", "")] , "tr_es": "Ayer fue 31 de agosto.", "tr_en": "Yesterday was August 31st."}
    ],
    "Dialogue II": [
        {"r": "美美", "t": [("明天", "míngtiān"), ("是", "shì"), ("星期六", "xīngqīliù"), ("，", ""), ("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("吗", "ma"), ("？", "")] , "tr_es": "¿Vas a la escuela mañana?", "tr_en": "Tomorrow is Saturday, are you going to school?"},
        {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("。", "")] , "tr_es": "Sí, voy.", "tr_en": "Yes, I am."},
        {"r": "美美", "t": [("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("做", "zuò"), ("什么", "shénme"), ("？", "")] , "tr_es": "¿A qué vas?", "tr_en": "What are you going to do at school?"},
        {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("学校", "xuéxiào"), ("看书", "kànshū"), ("。", ""), ("你", "nǐ"), ("吗", "ma"), ("？", "")] , "tr_es": "A leer. ¿Y tú?", "tr_en": "To read. And you?"},
        {"r": "美美", "t": [("我", "wǒ"), ("不", "bù"), ("去", "qù"), ("。", ""), ("我", "wǒ"), ("去", "qù"), ("我", "wǒ"), ("的", "de"), ("西班牙朋友", "Xībānyá péngyou"), ("家", "jiā"), ("看猫", "kàn māo"), ("。", "")] , "tr_es": "No, voy a casa de mi amigo.", "tr_en": "I'm going to my friend's house to see the cat."},
        {"r": "大卫", "t": [("是", "shì"), ("去", "qù"), ("西西", "Xīxi"), ("家", "jiā"), ("吗", "ma"), ("？", "")] , "tr_es": "¿A casa de Xixi?", "tr_en": "Are you going to Xixi's house?"},
        {"r": "美美", "t": [("是的", "shìde"), ("。", "")] , "tr_es": "Sí.", "tr_en": "Yes."},
        {"r": "大卫", "t": [("西西", "Xīxi"), ("家", "jiā"), ("有", "yǒu"), ("几", "jǐ"), ("只", "zhī"), ("猫", "māo"), ("？", "")] , "tr_es": "¿Cuántos gatos?", "tr_en": "How many cats does Xixi have?"},
        {"r": "美美", "t": [("他", "tā"), ("有", "yǒu"), ("两", "liǎng"), ("只", "zhī"), ("猫", "māo"), ("。", "")] , "tr_es": "Tiene dos.", "tr_en": "He has two cats."}
    ]
}

# --- 5. 语音合成核心逻辑 (修复 SSML，男女声对话) ---
async def make_dialogue_audio(lesson_data, filename):
    ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>"
    for line in lesson_data:
        # 美美 -> 晓晓 (Female), 大卫 -> 云希 (Male)
        v_name = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
        # 只提取中文汉字，防止读出翻译或拼音
        plain_text = "".join([pair[0] for pair in line["t"]])
        ssml += f"<voice name='{v_name}'>{line['r']}说：{plain_text}</voice><break time='500ms'/>"
    ssml += "</speak>"
    await edge_tts.Communicate(ssml).save(filename)

# --- 6. 主程序渲染逻辑 ---
def main():
    if "a_file" not in st.session_state: st.session_state.a_file = ""

    with st.sidebar:
        ui_lang = st.selectbox("Language / Idioma", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        l_key = st.selectbox("Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)

    st.subheader(l_key)
    lesson_data = LESSONS[l_key]
    
    # 音频播放器 (放在顶部固定位置)
    if "curr_l" not in st.session_state or st.session_state.curr_l != l_key:
        fname = f"voice_{int(time.time())}.mp3"
        with st.spinner(ui["audio_gen"]):
            asyncio.run(make_dialogue_audio(lesson_data, fname))
            st.session_state.a_file = fname
            st.session_state.curr_l = l_key
    st.audio(st.session_state.a_file)
    
    # 渲染对话大卡片
    full_plain_text = ""
    html_card = f'<div class="reading-card">'
    for line in lesson_data:
        html_card += f'<div class="line-container"><div class="role-label">{line["r"]}</div><div class="text-content">'
        for char, py in line["t"]:
            # 拼音开关修复逻辑：如果 show_pinyin 为 False，则不生成 rt 标签
            if show_pinyin and py:
                html_card += f'<ruby>{char}<rt>{py}</rt></ruby>'
            else:
                html_card += f'<ruby style="line-height:1.4;">{char}</ruby>'
            full_plain_text += char
        
        # 翻译逻辑修复：根据侧边栏选择加载对应语言
        if show_trans:
            t_content = line["tr_en"] if ui_lang == "English" else line["tr_es"]
            html_card += f'<span class="trans-text">{t_content}</span>'
        html_card += '</div></div>'
    html_card += '</div>'
    st.markdown(html_card, unsafe_allow_html=True)

    # 打字练习区
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<p class="instr">✍️ {ui["typing_instr"]}</p>', unsafe_allow_html=True)
    user_input = st.text_input(ui["typing_title"], placeholder="Type here...", label_visibility="collapsed")
    
    if user_input:
        res_html = '<div style="background:white; padding:8px 15px; border-radius:12px; border:2px solid #eee; margin-top:5px;">'
        max_l = max(len(full_plain_text), len(user_input))
        for i in range(max_l):
            if i < len(user_input) and i < len(full_plain_text):
                color = "#2ecc71" if user_input[i] == full_plain_text[i] else "#e74c3c"
                res_html += f'<span style="color:{color}; font-size:18px; font-weight:bold;">{user_input[i]}</span>'
            elif i < len(user_input):
                res_html += f'<span style="color:#e74c3c; font-size:18px;">{user_input[i]}</span>'
        st.markdown(res_html + '</div>', unsafe_allow_html=True)
        if user_input.strip() == full_plain_text.strip(): st.balloons()

if __name__ == "__main__":
    main()
