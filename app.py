import streamlit as st
import asyncio
import edge_tts
import os

st.set_page_config(page_title="阅读智能体", page_icon="📖", layout="centered")

# --- CSS 注入：复刻您的大师级 HTML 设计 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;700;900&family=Noto+Sans+SC:wght@400;700;900&display=swap');
    .stApp { background-color: #FFFBF0; font-family: 'Noto Sans SC', sans-serif; }
    h1 { color: #BE185D; font-family: 'Noto Serif SC', serif; font-weight: 900; }
    
    /* 隐藏右上角菜单 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 核心阅读卡片 */
    .reading-card {
        background-color: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(20px);
        padding: 25px;
        border-radius: 20px;
        border: 4px solid white;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        font-family: "Noto Serif SC", serif;
        line-height: 2.8;
        font-size: 22px;
        color: #333;
    }

    /* 拼音样式 */
    ruby { ruby-position: under; margin: 0 2px; padding: 2px; border-radius: 6px; }
    rt { color: #999; font-size: 12px; font-weight: normal; font-family: 'Noto Sans SC', sans-serif; }
    .hide-pinyin rt { visibility: hidden; }

    /* --- 核心：粉色语法贴纸样式 --- */
    a.grammar-link { text-decoration: none; display: inline-block; }
    .grammar-active {
        background-color: #FF9A9E; /* Soft Pink */
        color: white !important;
        border: 2px solid white;
        box-shadow: 0 4px 10px rgba(255, 154, 158, 0.4);
        transform: rotate(-3deg); /* 俏皮倾斜 */
        padding: 0 5px;
        transition: all 0.3s;
    }
    .grammar-active rt { color: rgba(255,255,255,0.95); font-weight: bold; }
    .grammar-active:hover { transform: scale(1.15) rotate(0deg); background-color: #BE185D; z-index: 10; }

    /* 按钮与打字区 */
    .stButton button { border-radius: 50px; background: linear-gradient(to right, #FF9A9E, #BE185D); color: white; border:none; font-weight:bold; }
    .stTextArea textarea { border-radius: 15px; border: 2px solid #FF9A9E; padding: 15px; }
    .trans-box { background: #E0F2F1; color: #0F766E; padding: 15px; border-radius: 15px; border: 3px solid white; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 数据库 ---
DATABASE = {
    "title": "我的爱好 (My Hobbies)",
    "content": [
        {"char": "我", "pinyin": "wǒ"},
        {"char": "非常", "pinyin": "fēi cháng"},
        {"char": "喜欢", "pinyin": "xǐ huān"},
        {"char": "看书", "pinyin": "kàn shū"},
        {"char": "。", "pinyin": ""},
        {"char": "虽然", "pinyin": "suī rán"},
        {"char": "工作", "pinyin": "gōng zuò"},
        {"char": "很", "pinyin": "hěn"},
        {"char": "忙", "pinyin": "máng"},
        {"char": "，", "pinyin": ""},
        {"char": "但是", "pinyin": "dàn shì"},
        # ▼▼▼ 关键点：链接到 static 文件夹 ▼▼▼
        {
            "char": "的", 
            "pinyin": "de", 
            # Streamlit Cloud 默认把 static 文件夹映射到 app/static/ 路径下
            "link": "app/static/de.html" 
        },
        # ▲▲▲ 结束 ▲▲▲
        {"char": "生活", "pinyin": "shēng huó"},
        {"char": "很", "pinyin": "hěn"},
        {"char": "充实", "pinyin": "chōng shí"},
        {"char": "。", "pinyin": ""}
    ],
    "translation": "Me gusta mucho leer. Aunque el trabajo es muy ocupado, mi vida es muy plena."
}

# --- 功能函数 ---
async def get_audio(text):
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save("audio.mp3")

def build_html(data, show_pinyin):
    html = '<div class="reading-card">' if show_pinyin else '<div class="reading-card hide-pinyin">'
    plain = ""
    for item in data["content"]:
        char = item["char"]
        plain += char
        ruby = f"<ruby>{char}<rt>{item['pinyin']}</rt></ruby>"
        if "link" in item:
            # target="_blank" 让它在新标签页打开
            html += f'<a href="{item["link"]}" target="_blank" class="grammar-link" title="点击查看语法课件"><ruby class="grammar-active">{char}<rt>{item["pinyin"]}</rt></ruby></a>'
        else:
            html += ruby
    html += '</div>'
    return html, plain

def check_typing(original, typed):
    res = '<div style="background:white; padding:15px; border-radius:12px; margin-top:10px; border: 2px solid #eee;">'
    for i in range(max(len(original), len(typed))):
        if i < len(typed) and i < len(original):
            color = "#2ecc71" if typed[i] == original[i] else "#e74c3c; text-decoration:line-through"
            res += f'<span style="color:{color}; font-size:20px; margin-right:2px; font-weight:bold;">{typed[i]}</span>'
        elif i < len(typed):
            res += f'<span style="color:#e74c3c;">{typed[i]}</span>'
        else:
            res += '<span style="color:#ddd;">_</span>'
    return res + '</div>'

# --- 主程序 ---
def main():
    with st.sidebar:
        st.header("⚙️ Settings")
        show_pinyin = st.toggle("拼音 / Pinyin", True)
        show_trans = st.toggle("翻译 / Translation", False)
        st.info("💡 提示：点击粉色的字查看语法！")

    st.title(DATABASE["title"])
    html, plain_text = build_html(DATABASE, show_pinyin)
    
    # 音频生成
    if "audio_ready" not in st.session_state:
        asyncio.run(get_audio(plain_text))
        st.session_state.audio_ready = True
    if os.path.exists("audio.mp3"):
        st.audio("audio.mp3")

    st.markdown(html, unsafe_allow_html=True)

    if show_trans:
        st.markdown(f'<div class="trans-box"><b>ES:</b> {DATABASE["translation"]}</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("✍️ 打字练习")
    user_input = st.text_area("请在这里跟读打字...", height=80)
    if user_input:
        st.markdown(check_typing(plain_text, user_input), unsafe_allow_html=True)
        if user_input.strip() == plain_text.strip():
            st.balloons()

if __name__ == "__main__":
    main()