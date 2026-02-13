import streamlit as st
import asyncio
import edge_tts
import os

st.set_page_config(page_title="阅读智能体", page_icon="📖", layout="centered")

# --- 1. CSS 注入：优化间距与设计 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;700;900&family=Noto+Sans+SC:wght@400;700;900&display=swap');
    .stApp { background-color: #FFFBF0; font-family: 'Noto Sans SC', sans-serif; }
    
    /* 标题样式 */
    h1 { color: #BE185D; font-family: 'Noto Serif SC', serif; font-weight: 900; padding-bottom: 20px; }

    /* 阅读卡片：增加行高，解决拼音挤在一起的问题 */
    .reading-card {
        background-color: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(15px);
        padding: 35px;
        border-radius: 2.5rem;
        border: 6px solid white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        font-family: "Noto Serif SC", serif;
        line-height: 3.5;  /* 👈 调大行高，给拼音留空间 */
        font-size: 26px;
        color: #333;
    }

    /* 拼音 rt 样式 */
    ruby { ruby-position: under; margin: 0 4px; }
    rt { 
        color: #888; 
        font-size: 13px; 
        font-weight: 700; 
        margin-top: 8px; /* 👈 增加拼音与汉字之间的垂直间距 */
        font-family: 'Noto Sans SC', sans-serif;
    }
    .hide-pinyin rt { visibility: hidden; }

    /* 语法贴纸效果 */
    a.grammar-link { text-decoration: none; display: inline-block; }
    .grammar-active {
        background-color: #FF9A9E;
        color: white !important;
        border: 2px solid white;
        transform: rotate(-3deg);
        padding: 0 8px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(255, 154, 158, 0.4);
    }
    .grammar-active rt { color: white; }

    /* 翻译框 */
    .trans-box { background: #E0F2F1; color: #0F766E; padding: 20px; border-radius: 1.5rem; border: 4px solid white; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 界面语言包 ---
UI_TEXT = {
    "Español": {
        "lang_label": "Idioma Interfaz",
        "settings": "Ajustes",
        "pinyin": "Mostrar Pinyin",
        "trans": "Traducción",
        "hint": "¡Haz clic en el carácter rosa para ver la gramática!",
        "typing": "✍️ Práctica de escritura",
        "vocab": "📚 Origen de las palabras (Units)"
    },
    "English": {
        "lang_label": "Interface Language",
        "settings": "Settings",
        "pinyin": "Show Pinyin",
        "trans": "Show Translation",
        "hint": "Click the pink character for grammar!",
        "typing": "✍️ Typing Practice",
        "vocab": "📚 Word Sources (Units)"
    }
}

# --- 3. 数据库 ---
DATABASE = {
    "title": "我的爱好 (My Hobbies)",
    "content": [
        {"char": "我", "pinyin": "wǒ", "unit": "U1"},
        {"char": "非常", "pinyin": "fēi cháng", "unit": "U2"},
        {"char": "喜欢", "pinyin": "xǐ huān", "unit": "U1"},
        {"char": "看书", "pinyin": "kàn shū", "unit": "U3"},
        {"char": "。", "pinyin": "", "unit": ""},
        {"char": "虽然", "pinyin": "suī rán", "unit": "U5"},
        {"char": "工作", "pinyin": "gōng zuò", "unit": "U2"},
        {"char": "很", "pinyin": "hěn", "unit": "U1"},
        {"char": "忙", "pinyin": "máng", "unit": "U2"},
        {"char": "，", "pinyin": "", "unit": ""},
        {"char": "但是", "pinyin": "dàn shì", "unit": "U5"},
        {
            "char": "的", 
            "pinyin": "de", 
            "unit": "Grammar",
            "link": "static/de.html" # 👈 修正路径
        },
        {"char": "生活", "pinyin": "shēng huó", "unit": "U4"},
        {"char": "很", "pinyin": "hěn", "unit": "U1"},
        {"char": "充实", "pinyin": "chōng shí", "unit": "U6"},
        {"char": "。", "pinyin": "", "unit": ""}
    ],
    "translation": {
        "es": "Me gusta mucho leer. Aunque el trabajo es muy ocupado, mi vida es muy plena.",
        "en": "I like reading very much. Although work is busy, my life is fulfilling."
    }
}

# --- 4. 功能逻辑 ---
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
            # 👈 这里使用相对路径跳转
            html += f'<a href="./{item["link"]}" target="_blank" class="grammar-link"><ruby class="grammar-active">{char}<rt>{item["pinyin"]}</rt></ruby></a>'
        else:
            html += ruby
    return html + '</div>', plain

# --- 5. 主程序 ---
def main():
    with st.sidebar:
        # 问题 2 修复：语言切换
        lang_select = st.selectbox("Interface Language", ["Español", "English"])
        ui = UI_TEXT[lang_select]
        
        st.divider()
        st.header(ui["settings"])
        show_pinyin = st.toggle(ui["pinyin"], True)
        show_trans = st.toggle(ui["trans"], False)
        st.warning(ui["hint"])

    st.title(DATABASE["title"])
    
    # 播放声音
    html, plain_text = build_html(DATABASE, show_pinyin)
    if "audio_ready" not in st.session_state:
        asyncio.run(get_audio(plain_text))
        st.session_state.audio_ready = True
    st.audio("audio.mp3")

    # 显示卡片
    st.markdown(html, unsafe_allow_html=True)

    # 翻译
    if show_trans:
        t = DATABASE["translation"]["es"] if lang_select == "Español" else DATABASE["translation"]["en"]
        st.markdown(f'<div class="trans-box"><b>{ui["trans"]}:</b> {t}</div>', unsafe_allow_html=True)

    # 问题 4 修复：单词单元来源列表
    st.divider()
    with st.expander(ui["vocab"]):
        vocab_list = [f"**{i['char']}** ({i['unit']})" for i in DATABASE["content"] if i['unit']]
        st.write(" / ".join(vocab_list))

    # 打字练习
    st.subheader(ui["typing"])
    user_input = st.text_area("...", label_visibility="collapsed")
    # (打字校验逻辑同前...)

if __name__ == "__main__":
    main()
