import streamlit as st
import asyncio
import edge_tts
import os
import streamlit.components.v1 as components

# --- 1. 页面设置 ---
st.set_page_config(page_title="互动阅读 Pro", page_icon="📚", layout="centered")

# =========================================================
# --- 2. 语法图书馆 (已嵌入你提供的 4 个 HTML 源代码) ---
# =========================================================

# 1. 对应 complementotime.html
HTML_TIME = """
{time_content}
"""

# 2. 对应 fechas.html
HTML_FECHAS = """
{fechas_content}
"""

# 3. 对应 qing.html
HTML_QING = """
{qing_content}
"""

# 4. 对应 qu.html
HTML_QU = """
{qu_content}
"""

# 组织成字典，方便程序调用
GRAMMAR_LIB = {
    "time": {"name": "时间位置 (Time Position)", "html": HTML_TIME},
    "fechas": {"name": "日期 (Dates)", "html": HTML_FECHAS},
    "qing": {"name": "请 (Please)", "html": HTML_QING},
    "qu": {"name": "去 (Go)", "html": HTML_QU}
}

# =========================================================
# --- 3. 视觉设计 (CSS) - 奶油色背景 + 完美对齐 ---
# =========================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    .stApp { background-color: #FFFBF0; }
    
    .role-label { font-weight: 900; color: #BE185D; margin-bottom: 5px; font-size: 1.1em; margin-top: 20px; }

    /* 汉字拼音容器：确保绝对整齐且间距舒适 */
    .char-unit {
        display: inline-flex;
        flex-direction: column-reverse;
        align-items: center;
        margin: 0 4px;
        height: 95px;
        vertical-align: bottom;
    }

    .pinyin-text {
        color: #888;
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 12px; /* 👈 拼音与汉字的呼吸间距 */
        font-family: 'Noto Sans SC', sans-serif;
    }

    .hanzi-text {
        font-family: "Noto Serif SC", serif;
        font-size: 26px;
        font-weight: 900;
        color: #333;
    }

    /* 语法按钮样式 */
    .stButton > button {
        background-color: #FF9A9E !important;
        color: white !important;
        border-radius: 10px !important;
        border: 2px solid white !important;
        box-shadow: 0 4px 8px rgba(255,154,158,0.3) !important;
        font-weight: 900 !important;
        transform: rotate(-2deg);
        padding: 0px 8px !important;
        height: 38px;
    }
    
    .stButton > button:hover {
        background-color: #BE185D !important;
        transform: scale(1.1) rotate(0deg);
    }

    .hide-pinyin .pinyin-text { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# --- 4. 数据库：Dialogue I & II (根据你的图片录入) ---
# =========================================================
LESSONS = {
    "Dialogue I (Dates & Time)": [
        {"role": "美美", "words": [
            {"c":"大卫","p":"Dàwèi"}, {"c":"，","p":""}, 
            {"c":"请问","p":"qǐngwèn","g":"qing"}, 
            {"c":"，","p":""}, 
            {"c":"今天","p":"jīntiān","g":"time"}, 
            {"c":"几号","p":"jǐ hào","g":"fechas"}, {"c":"？","p":""}
        ]},
        {"role": "大卫", "words": [
            {"c":"今天","p":"jīntiān","g":"time"}, 
            {"c":"9月1号","p":"jiǔ yuè yī hào","g":"fechas"}, {"c":"。","p":""}
        ]},
        {"role": "美美", "words": [
            {"c":"今天","p":"jīntiān","g":"time"}, 
            {"c":"星期几","p":"xīngqī jǐ","g":"fechas"}, {"c":"？","p":""}
        ]},
        {"role": "大卫", "words": [
            {"c":"星期三","p":"xīngqī sān","g":"fechas"}, {"c":"。","p":""}
        ]}
    ],
    "Dialogue II (Go & Action)": [
        {"role": "美美", "words": [
            {"c":"明天","p":"míngtiān","g":"time"}, {"c":"是","p":"shì"}, 
            {"c":"星期六","p":"xīngqīliù","g":"fechas"}, {"c":"，","p":""}, 
            {"c":"你","p":"nǐ"}, 
            {"c":"去","p":"qù","g":"qu"}, 
            {"c":"学校","p":"xuéxiào"}, {"c":"吗","p":"ma"}, {"c":"？","p":""}
        ]},
        {"role": "大卫", "words": [{"c":"我","p":"wǒ"}, {"c":"去","p":"qù","g":"qu"}, {"c":"。","p":""}]},
        {"role": "美美", "words": [
            {"c":"你","p":"nǐ"}, {"c":"去","p":"qù","g":"qu"}, 
            {"c":"学校","p":"xuéxiào"}, {"c":"做","p":"zuò"}, {"c":"什么","p":"shénme"}, {"c":"？","p":""}
        ]},
        {"role": "大卫", "words": [
            {"c":"我","p":"wǒ"}, {"c":"去","p":"qù","g":"qu"}, 
            {"c":"学校","p":"xuéxiào"}, {"c":"看书","p":"kànshū"}, 
            {"c":"。","p":""}, {"c":"你","p":"nǐ"}, {"c":"吗","p":"ma"}, {"c":"？","p":""}
        ]},
        {"role": "美美", "words": [
            {"c":"我","p":"wǒ"}, {"c":"不","p":"bù"}, {"c":"去","p":"qù","g":"qu"}, {"c":"。","p":""},
            {"c":"我","p":"wǒ"}, {"c":"去","p":"qù","g":"qu"}, 
            {"c":"我","p":"wǒ"}, {"c":"的","p":"de"}, # 这里没有设置语法跳转，仅显示
            {"c":"西班牙朋友","p":"Xībānyá péngyou"}, {"c":"家","p":"jiā"}, {"c":"看猫","p":"kàn māo"}, {"c":"。","p":""}
        ]}
    ]
}

# --- 5. 双声音合成逻辑 (美美: 晓晓, 大卫: 云希) ---
async def generate_dialogue_audio(content):
    ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>"
    for line in content:
        voice = "zh-CN-XiaoxiaoNeural" if line["role"] == "美美" else "zh-CN-YunxiNeural"
        text = "".join([w["c"] for w in line["words"]])
        ssml += f"<voice name='{voice}'>{line['role']}：{text}</voice><break time='600ms'/>"
    ssml += "</speak>"
    await edge_tts.Communicate(ssml).save("lesson_voice.mp3")

# --- 6. 主程序 ---
def main():
    with st.sidebar:
        st.title("⚙️ Ajustes")
        lesson_key = st.selectbox("Seleccionar Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle("Mostrar Pinyin", True)
        st.info("🎙️ Personajes:\n- 美美 (Xiaoxiao)\n- 大卫 (Yunxi)")

    st.title(lesson_key)
    lesson_data = LESSONS[lesson_key]

    # 音频播放
    if "last_l" not in st.session_state or st.session_state.last_l != lesson_key:
        with st.spinner("Generando audio..."):
            asyncio.run(generate_dialogue_audio(lesson_data))
            st.session_state.last_l = lesson_key
    st.audio("lesson_voice.mp3")

    # 渲染卡片
    p_class = "" if show_pinyin else "hide-pinyin"
    for idx_line, line in enumerate(lesson_data):
        st.markdown(f'<div class="role-label">{line["role"]}</div>', unsafe_allow_html=True)
        # 拆分文字，实现按钮与普通字的对齐
        cols = st.columns(len(line["words"]) + 2)
        for idx_word, word in enumerate(line["words"]):
            with cols[idx_word]:
                if "g" in word:
                    if st.button(word["c"], key=f"btn_{lesson_key}_{idx_line}_{idx_word}"):
                        st.session_state.active_g = word["g"]
                    st.markdown(f'<div class="{p_class} char-unit"><span class="pinyin-text">{word["p"]}</span></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                    <div class="{p_class} char-unit">
                        <span class="hanzi-text">{word['c']}</span>
                        <span class="pinyin-text">{word['p']}</span>
                    </div>
                    ''', unsafe_allow_html=True)

    # --- 语法展示区 ---
    if "active_g" in st.session_state:
        g_id = st.session_state.active_g
        st.divider()
        st.success(f"📘 Estudiando: {GRAMMAR_LIB[g_id]['name']}")
        components.html(GRAMMAR_LIB[g_id]['html'], height=850, scrolling=True)
        if st.button("❌ Cerrar Lección"):
            del st.session_state.active_g
            st.rerun()

if __name__ == "__main__":
    main()
