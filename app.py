import streamlit as st
import asyncio
import edge_tts
import os
import time
import random
import html

# --- 1. Pro 模式页面配置 ---
st.set_page_config(
    page_title="互动阅读 Pro - 专业教学模式", 
    page_icon="🎓", 
    layout="centered"
)

# --- 2. 专业版双语语言包 ---
UI_TEXT = {
    "Español": {
        "pinyin": "Pinyin", 
        "trans": "Traducción", 
        "audio_gen": "Preparando voces profesionales...",
        "typing_title": "✍️ Centro de Práctica de Escritura",
        "typing_instr": "Instrucción: Por favor, escriba el texto superior aquí siguiendo los caracteres para mejorar su precisión al escribir.",
        "perfect": "✨ ¡Excelente! Has completado el ejercicio."
    },
    "English": {
        "pinyin": "Pinyin", 
        "trans": "Translation", 
        "audio_gen": "Generating pro voices...",
        "typing_title": "✍️ Writing Practice Center",
        "typing_instr": "Instruction: Please type the text above here word by word to master your typing skills.",
        "perfect": "✨ Perfect! Exercise completed successfully."
    }
}

# --- 3. 大师级视觉设计 (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    .stApp { background-color: #FFFBF0; }
    
    /* 模仿 complementotime.html 的大师级卡片 */
    .reading-card {
        background-color: white; 
        padding: 25px 35px; 
        border-radius: 2.5rem;
        border: 4px solid #fff; 
        box-shadow: 0 15px 45px rgba(0,0,0,0.06);
        max-width: 750px; 
        margin: 0 auto;
        position: relative;
    }

    .line-container { 
        display: flex; 
        margin-bottom: 8px; 
        align-items: flex-start;
        padding: 5px 0;
        border-bottom: 1px solid #f9f9f9;
    }

    /* 角色标签：胭脂红 (Pro版色深) */
    .role-label {
        min-width: 65px; 
        font-weight: 900; 
        color: #BE185D; 
        font-size: 1.1em; 
        padding-top: 12px; 
        font-family: 'Noto Serif SC', serif;
    }

    .text-content { flex: 1; line-height: 2.9; }

    /* 汉字显示：深灰 (#333) */
    ruby { 
        ruby-position: under; 
        padding: 0 4px; 
        font-family: "Noto Serif SC", serif; 
        font-size: 25px; 
        font-weight: 900; 
        color: #333; 
    }

    /* 拼音：清新绿 (符合 fechas.html 标准) */
    rt { 
        font-family: 'Noto Sans SC', sans-serif; 
        font-size: 13px; 
        color: #15803D !important; 
        font-weight: 700; 
        padding-top: 10px !important; 
    }

    /* 翻译：深邃蓝 (符合 complementotime.html 标准) */
    .trans-text { 
        font-size: 0.9em; 
        color: #1D4ED8; 
        font-family: 'Noto Sans SC', sans-serif; 
        font-weight: 700;
        font-style: normal; 
        margin-left: 12px;
        opacity: 0.9;
    }

    /* 紧凑模式 */
    .hide-pinyin rt { display: none !important; }
    .hide-pinyin .text-content { line-height: 1.6 !important; }

    /* 说明文字样式 */
    .instruction-box {
        background: rgba(191, 219, 254, 0.2);
        padding: 10px 20px;
        border-radius: 1rem;
        border-left: 5px solid #1D4ED8;
        font-size: 0.95em;
        font-weight: 700;
        color: #1e40af;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. 数据库：内容完整对齐 PPT 截图 ---
LESSONS = {
    "Dialogue I": [
        {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("，", ""), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , "tr_es": "David, disculpe, ¿qué fecha es hoy?", "tr_en": "David, excuse me, what's the date today?"},
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
        {"r": "美美", "t": [("你", "nǐ"), ("去", "qù"), ("学校", "xuéxiào"), ("做", "zuò"), ("什么", "shénme"), ("？", "")] , "tr_es": "¿A qué vas?", "tr_en": "What will you do at school?"},
        {"r": "大卫", "t": [("我", "wǒ"), ("去", "qù"), ("学校", "xuéxiào"), ("看书", "kànshū"), ("。", ""), ("你", "nǐ"), ("吗", "ma"), ("？", "")] , "tr_es": "A leer. ¿Y tú?", "tr_en": "To read. And you?"},
        {"r": "美美", "t": [("我", "wǒ"), ("不", "bù"), ("去", "qù"), ("。", ""), ("我", "wǒ"), ("去", "qù"), ("我", "wǒ"), ("的", "de"), ("西班牙朋友", "Xībānyá péngyou"), ("家", "jiā"), ("看猫", "kàn māo"), ("。", "")] , "tr_es": "Voy a casa de mi amigo.", "tr_en": "I'm going to my friend's house to see the cat."},
        {"r": "大卫", "t": [("是", "shì"), ("去", "qù"), ("西西", "Xīxi"), ("家", "jiā"), ("吗", "ma"), ("？", "")] , "tr_es": "¿A casa de Xixi?", "tr_en": "Are you going to Xixi's house?"},
        {"r": "美美", "t": [("是的", "shìde"), ("。", "")] , "tr_es": "Sí.", "tr_en": "Yes."},
        {"r": "大卫", "t": [("西西", "Xīxi"), ("家", "jiā"), ("有", "yǒu"), ("几", "jǐ"), ("只", "zhī"), ("猫", "māo"), ("？", "")] , "tr_es": "¿Cuántos gatos?", "tr_en": "How many cats does Xixi have?"},
        {"r": "美美", "t": [("他", "tā"), ("有", "yǒu"), ("两", "liǎng"), ("只", "zhī"), ("猫", "māo"), ("。", "")] , "tr_es": "Tiene dos.", "tr_en": "He has two cats."}
    ]
}

# --- 5. Pro 模式语音合成 (SSML 强制纯净逻辑) ---
async def make_pro_audio(lesson_data, filename):
    # 构建绝对严谨的 SSML，确保没有多余的空格或非法字符引起“读代码”
    ssml = "<?xml version='1.0' encoding='UTF-8'?>"
    ssml += "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>"
    for line in lesson_data:
        # 强制指派角色
        voice = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
        # 纯净文本处理：只取汉字
        text = "".join([pair[0] for pair in line["t"]])
        # 处理数字发音
        text = text.replace("9月", "九月").replace("1号", "一号").replace("2号", "二号").replace("8月", "八月").replace("31号", "三十一号")
        # 构造节点
        ssml += f"<voice name='{voice}'>{html.escape(text)}</voice><break time='600ms'/>"
    ssml += "</speak>"
    
    communicate = edge_tts.Communicate(ssml)
    await communicate.save(filename)

# --- 6. 主程序 ---
def main():
    if "p_audio" not in st.session_state: st.session_state.p_audio = ""

    with st.sidebar:
        st.title("Pro Settings")
        ui_lang = st.selectbox("Interface Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        st.divider()
        lesson_key = st.selectbox("Lesson / Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)

    st.subheader(lesson_key)
    lesson_data = LESSONS[lesson_key]
    
    # 语音处理 (缓存穿透修复)
    if "last_l" not in st.session_state or st.session_state.last_l != lesson_key:
        # 生成带时间戳的随机文件名，彻底解决旧音频缓存问题
        new_fname = f"audio_{int(time.time() * 1000)}.mp3"
        with st.spinner(ui["audio_gen"]):
            asyncio.run(make_pro_audio(lesson_data, new_fname))
            st.session_state.p_audio = new_fname
            st.session_state.last_l = lesson_key
    
    # 显示播放器
    st.audio(st.session_state.p_audio)
    
    # 渲染大师卡片
    full_plain_text = ""
    p_class = "" if show_pinyin else "hide-pinyin"
    
    html_card = f'<div class="reading-card {p_class}">'
    for line in lesson_data:
        html_card += f'<div class="line-container"><div class="role-label">{line["r"]}</div><div class="text-content">'
        for char, py in line["t"]:
            if show_pinyin and py:
                html_card += f'<ruby>{char}<rt>{py}</rt></ruby>'
            else:
                html_card += f'<ruby style="line-height:1.4;">{char}</ruby>'
            full_plain_text += char
        
        # 翻译修复逻辑：严格区分 Eng 和 Esp
        if show_trans:
            t_content = line["tr_en"] if ui_lang == "English" else line["tr_es"]
            html_card += f'<span class="trans-text">{t_content}</span>'
            
        html_card += '</div></div>'
    html_card += '</div>'
    
    st.markdown(html_card, unsafe_allow_html=True)

    # 打字练习区：Pro 指令版
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div class="instruction-box">💡 {ui["typing_instr"]}</div>', unsafe_allow_html=True)
    
    user_input = st.text_input(ui["typing_title"], placeholder="Start typing...", label_visibility="collapsed")
    
    if user_input:
        res_html = '<div style="background:white; padding:12px 20px; border-radius:1rem; border:2px solid #ddd; margin-top:5px;">'
        max_l = max(len(full_plain_text), len(user_input))
        for i in range(max_l):
            if i < len(user_input) and i < len(full_plain_text):
                color = "#22c55e" if user_input[i] == full_plain_text[i] else "#ef4444"
                res_html += f'<span style="color:{color}; font-size:20px; font-weight:bold;">{user_input[i]}</span>'
            elif i < len(user_input):
                res_html += f'<span style="color:#ef4444; font-size:20px;">{user_input[i]}</span>'
        st.markdown(res_html + '</div>', unsafe_allow_html=True)
        if user_input.strip() == full_plain_text.strip():
            st.balloons()
            st.success(ui["perfect"])

if __name__ == "__main__":
    main()
