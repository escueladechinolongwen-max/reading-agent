import streamlit as st
import asyncio
import edge_tts
import os
import streamlit.components.v1 as components

# --- 1. 页面基本设置 ---
st.set_page_config(page_title="互动阅读 Pro", page_icon="📖", layout="centered")

# =========================================================
# --- 2. 语法图书馆 (在此处粘贴你的 HTML 代码) ---
# =========================================================
# 提示：请将文件的内容贴在两个 """ 之间。
# 这三个双引号 """ 是 Python 包裹长文本的专用符号。

HTML_FECHAS = """ (在这里粘贴 fechas.html 的全部内容) """
HTML_QU = """ (在这里粘贴 qu.html 的全部内容) """
HTML_QING = """ (在这里粘贴 qing.html 的全部内容) """
HTML_TIME = """ (在这里粘贴 complementotime.html 的全部内容) """

# 备用：如果以后需要 '的'，粘贴在这里
HTML_DE = "" 

GRAMMAR_LIB = {
    "qing": {"name": "请 (Please)", "html": HTML_QING},
    "fechas": {"name": "日期 (Dates)", "html": HTML_FECHAS},
    "qu": {"name": "去 (Go)", "html": HTML_QU},
    "time": {"name": "时间位置 (Time Position)", "html": HTML_TIME}
}

# =========================================================
# --- 3. 视觉设计 (CSS) - 奶油底色 + 彻底解决乱版 ---
# =========================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    .stApp { background-color: #FFFBF0; }
    
    /* 核心阅读卡片 */
    .reading-card {
        background-color: white;
        padding: 30px;
        border-radius: 2rem;
        border: 4px solid #eee;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        line-height: 4.5; /* 👈 增加行高，给拼音留足空间 */
    }

    .role-label {
        font-weight: 900;
        color: #BE185D;
        font-size: 1.2em;
        margin-top: 15px;
        display: block;
    }

    /* 汉字+拼音单元：使用 Ruby 标准 */
    ruby {
        ruby-position: under; /* 👈 拼音在汉字下面 */
        padding: 0 5px;
        font-family: "Noto Serif SC", serif;
        font-size: 28px;
        font-weight: 900;
        color: #333;
    }

    rt {
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 14px;
        color: #888;
        font-weight: 700;
        padding-top: 8px; /* 👈 汉字与拼音的垂直间距 */
    }

    .hide-pinyin rt { visibility: hidden; }

    /* 语法高亮色 */
    .grammar-highlight { color: #BE185D; text-decoration: underline; text-decoration-color: #FF9A9E; text-decoration-thickness: 3px; }

</style>
""", unsafe_allow_html=True)

# =========================================================
# --- 4. 数据库 ---
# =========================================================
LESSONS = {
    "Dialogue I (Dates)": [
        {"role": "美美", "words": "大卫，请问，今天几号？", "plain": "大卫，请问，今天几号？"},
        {"role": "大卫", "words": "今天9月1号。", "plain": "今天九月一号。"},
        {"role": "美美", "words": "今天星期几？", "plain": "今天星期几？"},
        {"role": "大卫", "words": "星期三。", "plain": "星期三。"}
    ],
    "Dialogue II (Action)": [
        {"role": "美美", "words": "明天是星期六，你去学校吗？", "plain": "明天是星期六，你去学校吗？"},
        {"role": "大卫", "words": "我去。", "plain": "我去。"},
        {"role": "美美", "words": "你去学校做什么？", "plain": "你去学校做什么？"},
        {"role": "大卫", "words": "我去学校看书。你吗？", "plain": "我去学校看书。你吗？"},
        {"role": "美美", "words": "我不去。我去我的西班牙朋友家看猫。", "plain": "我不去。我去我的西班牙朋友家看猫。"}
    ]
}

# --- 渲染阅读文本的函数 ---
def render_ruby_text(role, text, show_pinyin):
    # 这里是一个简单的分词映射（实际应用中建议使用字典）
    mapping = {
        "大卫": "Dàwèi", "请问": "qǐngwèn", "今天": "jīntiān", "几号": "jǐ hào", "星期几": "xīngqī jǐ",
        "9月1号": "jiǔ yuè yī hào", "星期三": "xīngqī sān", "明天": "míngtiān", "是": "shì", "星期六": "xīngqīliù",
        "你": "nǐ", "去": "qù", "学校": "xuéxiào", "吗": "ma", "我": "wǒ", "做": "zuò", "什么": "shénme",
        "看书": "kànshū", "不": "bù", "西班牙朋友": "Xībānyá péngyou", "家": "jiā", "看猫": "kàn māo", "的": "de"
    }
    
    p_class = "" if show_pinyin else "hide-pinyin"
    html = f'<span class="role-label">{role}</span>'
    html += f'<div class="reading-card {p_class}">'
    
    # 简单的分词渲染逻辑
    import re
    tokens = re.findall(r'[\u4e00-\u9fa5]+|[0-9]+[月号]+|[，。？,.\?]', text)
    for t in tokens:
        p = mapping.get(t, "")
        html += f'<ruby>{t}<rt>{p}</rt></ruby>'
    html += '</div>'
    return html

# --- 5. 音频逻辑 (修复 SSML) ---
async def generate_voice(lesson_key):
    content = LESSONS[lesson_key]
    ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>"
    for line in content:
        # 美美 -> Xiaoxiao, 大卫 -> Yunxi
        voice = "zh-CN-XiaoxiaoNeural" if line["role"] == "美美" else "zh-CN-YunxiNeural"
        ssml += f"<voice name='{voice}'>{line['role']}说：{line['plain']}</voice><break time='600ms'/>"
    ssml += "</speak>"
    
    await edge_tts.Communicate(ssml).save("dialogue.mp3")

# --- 6. 主程序 ---
def main():
    with st.sidebar:
        st.title("⚙️ Ajustes")
        l_key = st.selectbox("Lección", list(LESSONS.keys()))
        show_pinyin = st.toggle("Mostrar Pinyin", True)
        st.divider()
        st.info("🎙️ Personajes:\n- 美美 (Xiaoxiao)\n- 大卫 (Yunxi)")

    st.title(l_key)

    # 音频播放
    if "current_l" not in st.session_state or st.session_state.current_l != l_key:
        with st.spinner("Generando audio..."):
            asyncio.run(generate_voice(l_key))
            st.session_state.current_l = l_key
    st.audio("dialogue.mp3")

    # 渲染文本
    for line in LESSONS[l_key]:
        st.markdown(render_ruby_text(line["role"], line["words"], show_pinyin), unsafe_allow_html=True)

    # 语法教学区
    st.divider()
    st.subheader("📚 Lecciones de Gramática")
    
    cols = st.columns(4)
    for i, (gid, info) in enumerate(GRAMMAR_LIB.items()):
        if cols[i].button(f"📖 {info['name']}", key=f"btn_{gid}"):
            st.session_state.active_g = gid

    if "active_g" in st.session_state:
        g_id = st.session_state.active_g
        st.success(f"Estudiando: {GRAMMAR_LIB[g_id]['name']}")
        components.html(GRAMMAR_LIB[g_id]['html'], height=800, scrolling=True)
        if st.button("❌ Cerrar"):
            del st.session_state.active_g
            st.rerun()

if __name__ == "__main__":
    main()
