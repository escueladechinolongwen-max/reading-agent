import streamlit as st
import asyncio
import edge_tts
import os
import time
import random
import re

# --- 1. 页面基本配置 ---
st.set_page_config(
    page_title="阅读 Pro - V23 强制重录版", 
    page_icon="🛡️", 
    layout="wide"
)

# --- 2. 界面双语语言包 ---
UI_TEXT = {
    "Español": {
        "pinyin": "Pinyin", "trans": "Traducción", "audio_gen": "Generando audio nuevo...",
        "typing_title": "✍️ Práctica", "typing_instr": "Escribe el texto de arriba aquí.", 
        "perfect": "🎉 ¡Correcto!", "refresh": "🔄 Regenerar Audio"
    },
    "English": {
        "pinyin": "Pinyin", "trans": "Translation", "audio_gen": "Generating fresh audio...",
        "typing_title": "✍️ Practice", "typing_instr": "Type the text above here.", 
        "perfect": "🎉 Correct!", "refresh": "🔄 Regenerate Audio"
    }
}

# --- 3. 视觉设计 (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    .stApp { background-color: #FFFBF0; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 1000px !important; }

    /* 智能阅读框 */
    .reading-scroll-area {
        background-color: white; padding: 15px 25px; border-radius: 1.5rem;
        border: 2px solid #eee; overflow-y: auto; margin-bottom: 10px; transition: height 0.3s ease;
    }
    @media (min-height: 901px) { .reading-scroll-area { height: 60vh; } }
    @media (max-height: 900px) { .reading-scroll-area { height: 50vh; } }
    @media (max-height: 700px) { .reading-scroll-area { height: 40vh; } }

    .line-container { display: flex; margin-bottom: 6px; align-items: flex-start; justify-content: space-between; padding-bottom: 6px; border-bottom: 1px solid #fcfcfc; }
    .left-zone { display: flex; flex: 1; align-items: flex-start; max-width: 75%; }
    .role-label { min-width: 50px; font-weight: 900; color: #BE185D; font-size: 0.95em; padding-top: 8px; font-family: 'Noto Serif SC', serif; }
    .text-content { line-height: 2.6; }
    ruby { ruby-position: under; padding: 0 2px; font-family: "Noto Serif SC", serif; font-size: 22px; font-weight: 900; color: #333; }
    rt { font-family: 'Noto Sans SC', sans-serif; font-size: 11px; color: #15803D !important; font-weight: 700; padding-top: 5px !important; }
    .right-zone { width: 22%; background: #EFF6FF; border-left: 3px solid #3B82F6; padding: 5px 10px; border-radius: 8px; margin-top: 5px; }
    .trans-text { font-size: 0.8rem; color: #1D4ED8; font-family: 'Noto Sans SC', sans-serif; font-weight: 700; line-height: 1.2; }
    .typing-section { background: #fff; padding: 8px 20px; border-radius: 1rem; border: 2px solid #eee; box-shadow: 0 -4px 10px rgba(0,0,0,0.02); }
    .instr-text { color: #666; font-size: 0.8em; font-weight: 700; margin-bottom: 2px; }
    .hide-pinyin rt { display: none !important; }
    .hide-pinyin .text-content { line-height: 1.4 !important; }
    .main-header { font-family: 'Noto Serif SC', serif; font-weight: 900; color: #333; font-size: 1.5rem; text-align: center; margin-bottom: 0px; }
    .version-tag { background-color: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: bold; border: 1px solid #f87171; }
</style>
""", unsafe_allow_html=True)

# --- 4. 数据库 ---
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

# --- 5. 语音合成核心逻辑 (V23 白名单机制) ---
async def make_audio_v23(lesson_data, filename):
    # 创建文件
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(lesson_data):
            # 1. 强制角色
            voice = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
            
            # 2. 提取文本
            raw = "".join([pair[0] for pair in line["t"]])
            # 修正数字
            txt = raw.replace("9月", "九月").replace("1号", "一号").replace("2号", "二号").replace("8月", "八月").replace("31号", "三十一号")
            
            # 3. 🛡️ 白名单过滤：只允许汉字、中文标点、数字。其他全部杀掉。
            # 这行代码保证了 "xml", "slash", "equals" 根本无法进入 TTS 引擎
            clean = re.sub(r'[^\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef0-9]', '', txt)
            
            # 4. 生成片段
            temp_f = f"t_{i}_{int(time.time())}.mp3"
            try:
                # 纯文本模式，无任何 SSML 标签
                communicate = edge_tts.Communicate(clean, voice)
                await communicate.save(temp_f)
                with open(temp_f, 'rb') as chunk:
                    final_file.write(chunk.read())
            except:
                pass
            finally:
                if os.path.exists(temp_f): os.remove(temp_f)

# --- 6. 主程序 ---
def main():
    # ⚠️ 更改状态变量名，强制让 Streamlit 认为这是第一次运行
    if "audio_v23" not in st.session_state: st.session_state.audio_v23 = ""
    if "lesson_v23" not in st.session_state: st.session_state.lesson_v23 = ""

    with st.sidebar:
        st.markdown('<div class="version-tag">🔴 V23.0 强制刷新版</div>', unsafe_allow_html=True)
        st.caption("现在是最新版本！")
        st.divider()
        
        st.title("Settings")
        ui_lang = st.selectbox("Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        
        # 🔄 手动刷新按钮
        if st.button(ui["refresh"], type="primary"):
            st.session_state.lesson_v23 = "" # 清空记录，强制重录
            st.rerun()

        st.divider()
        lesson_key = st.selectbox("Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)

    st.markdown(f'<div class="main-header">{lesson_key}</div>', unsafe_allow_html=True)
    
    lesson_data = LESSONS[lesson_key]
    
    # 逻辑：如果当前课文 != 缓存的课文，或者缓存为空，则重新生成
    if st.session_state.lesson_v23 != lesson_key:
        fname = f"audio_v23_{int(time.time())}.mp3"
        with st.spinner(ui["audio_gen"]):
            asyncio.run(make_audio_v23(lesson_data, fname))
            st.session_state.audio_v23 = fname
            st.session_state.lesson_v23 = lesson_key
    
    st.audio(st.session_state.audio_v23)
    
    # 渲染
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

    # 底部
    st.markdown(f'<div class="typing-section"><p class="instr-text">✍️ {ui["typing_instr"]}</p></div>', unsafe_allow_html=True)
    user_input = st.text_input("inp", placeholder="Type here...", label_visibility="collapsed")
    
    full_text = "".join(["".join([p[0] for p in l["t"]]) for l in lesson_data])
    
    if user_input:
        res = '<div style="background:white; padding:8px 15px; border-radius:10px; border:2px solid #ddd; margin-top:5px;">'
        max_l = max(len(full_text), len(user_input))
        for i in range(max_l):
            if i < len(user_input) and i < len(full_text):
                color = "#2ecc71" if user_input[i] == full_text[i] else "#e74c3c"
                res += f'<span style="color:{color}; font-size:18px; font-weight:bold;">{user_input[i]}</span>'
            elif i < len(user_input):
                res += f'<span style="color:#e74c3c; font-size:18px;">{user_input[i]}</span>'
        st.markdown(res + '</div>', unsafe_allow_html=True)
        if user_input.strip() == full_text.strip(): st.balloons()

if __name__ == "__main__":
    main()
