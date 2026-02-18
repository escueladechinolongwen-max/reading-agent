import streamlit as st
import asyncio
import edge_tts
import os
import time
import base64
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- 1. 核心配置 ---
st.set_page_config(page_title="Long Wen Reading Pro", page_icon="🐼", layout="wide", initial_sidebar_state="expanded")
MY_API_KEY = os.environ.get("GOOGLE_API_KEY")
TARGET_MODEL = 'models/gemini-2.5-flash'

# 🌍 语言包
UI_TEXT = {
    "Español": { 
        "instr": "✍️ Escribe aquí para practicar...", 
        "gen_btn": "Generar Lección ✨", 
        "topic": "Tema", "level": "Nivel", "keywords": "Palabras",
        "loading": "Creando lección...",
        "show_py": "Mostrar Pinyin", "show_tr": "Mostrar Traducción"
    },
    "English": { 
        "instr": "✍️ Type here to practice...", 
        "gen_btn": "Generate Lesson ✨", 
        "topic": "Topic", "level": "Level", "keywords": "Keywords",
        "loading": "Creating lesson...",
        "show_py": "Show Pinyin", "show_tr": "Show Translation"
    }
}

# --- 2. CSS 美化 (分栏 + 颜色 + 固定底部) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #f8fafc;
        overflow: hidden !important; 
        height: 100vh;
    }
    
    /* 调整顶部间距 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 100px !important; /* 给底部打字框留位置 */
        max-width: 95% !important;
        height: 100vh;
        overflow-y: auto !important; /* 允许主区域滚动 */
    }

    .main-title { 
        text-align: center; font-family: 'Noto Serif SC', serif; 
        font-weight: 900; color: #334155; font-size: 1.8rem; margin-bottom: 20px; 
    }

    /* 行容器：左右布局 */
    .row-container {
        display: flex;
        border-bottom: 1px dashed #e2e8f0;
        padding: 15px 0;
        align-items: flex-start;
    }

    /* 左侧：翻译 (绿色，独立) */
    .left-box {
        width: 30%;
        padding-right: 20px;
        border-right: 3px solid #e2e8f0;
        color: #059669; /* 鲜艳的绿色 */
        font-weight: 600;
        font-size: 1rem;
        font-style: italic;
        text-align: right;
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }

    /* 右侧：汉字 (黑色) + 拼音 (蓝色) */
    .right-box {
        width: 70%;
        padding-left: 20px;
        display: flex;
        flex-wrap: wrap; 
        gap: 8px; /* 字间距 */
        align-items: flex-end;
    }

    /* 汉字样式 */
    ruby { 
        font-size: 32px; font-weight: 900; color: #1e293b; /* 深黑色 */
        ruby-position: under; line-height: 2.0; 
    }
    
    /* 拼音样式 */
    rt { 
        font-size: 14px; color: #3b82f6; /* 亮蓝色 */
        font-weight: 700; transform: translateY(-8px);
        font-family: sans-serif;
    }
    
    /* 角色标签 */
    .role-tag {
        font-size: 0.8rem; background: #cbd5e1; color: #475569;
        padding: 4px 8px; border-radius: 6px; margin-right: 12px;
        font-weight: bold; height: fit-content; margin-top: 12px;
    }

    /* 底部固定打字区 (醒目) */
    .fixed-bottom {
        position: fixed; 
        bottom: 0; 
        left: 0; 
        width: 100%;
        background: white; 
        padding: 20px; 
        border-top: 4px solid #3b82f6; /* 醒目的蓝条 */
        z-index: 9999;
        box-shadow: 0 -10px 20px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    /* 隐藏/显示控制类 */
    .hide-pinyin rt { display: none !important; }
    .hide-trans .left-box { opacity: 0; } /* 隐藏文字但保留占位 */

    .highlight-active { background-color: #fffbeb; transition: background 0.3s; }
</style>
""", unsafe_allow_html=True)

# --- 3. AI 逻辑 ---
def call_ai(topic, level, keywords):
    if not MY_API_KEY: return None
    try:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel(TARGET_MODEL)
        safety = {HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE}

        prompt = f"""
        Act as a JSON API. Create a Chinese dialogue (4-6 lines) between '美美' (Female) and '大卫' (Male).
        Topic: {topic}. Level: {level}. Keywords: {keywords}.
        
        RULES:
        1. Include standard punctuation (，。？！).
        2. Output JSON ARRAY only.
        Format: [{{"r": "美美", "t": [["你", "nǐ"], ["好", "hǎo"], ["，", ""]], "tr_es": "Hola", "tr_en": "Hi"}}]
        """
        response = model.generate_content(prompt, safety_settings=safety)
        text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)
    except Exception as e:
        st.error(str(e))
        return None

# --- 4. 音频 ---
async def make_audio(data, filename):
    ts = []
    curr = 0.0
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(data):
            voice = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
            raw = "".join([p[0] for p in line.get("t", [])])
            dur = len(raw) * 0.26 + 0.5 
            ts.append({"start": curr, "end": curr + dur, "role": line["r"]})
            try:
                comm = edge_tts.Communicate(raw, voice)
                temp_f = f"tmp_{int(time.time())}_{i}.mp3"
                await comm.save(temp_f)
                with open(temp_f, 'rb') as f: final_file.write(f.read())
                os.remove(temp_f)
            except: pass
            curr += dur
    return ts

# --- 5. 播放器 ---
def get_player_html(file_path, ts):
    with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    return f"""
    <div style="width:100%; position:sticky; top:0; background:#f8fafc; z-index:100; padding:10px 0; text-align:center;">
        <audio id="p" controls src="data:audio/mp3;base64,{b64}" style="width:500px; height:40px; border-radius:20px; box-shadow:0 4px 6px rgba(0,0,0,0.1);"></audio>
    </div>
    <script>
        const p = document.getElementById('p');
        const ts = {json.dumps(ts)};
        p.ontimeupdate = () => {{
            const cur = p.currentTime;
            ts.forEach((t, i) => {{
                const el = window.parent.document.getElementById('row-'+i);
                if (el) {{
                    if (cur >= t.start && cur < t.end) {{
                        el.classList.add("highlight-active");
                        el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }} else {{
                        el.classList.remove("highlight-active");
                    }}
                }}
            }});
        }};
    </script>
    """

def main():
    if "current_data" not in st.session_state: st.session_state.current_data = None
    if "audio_file" not in st.session_state: st.session_state.audio_file = ""

    with st.sidebar:
        st.header("🐼 Settings")
        ui_lang = st.selectbox("Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        
        topic = st.text_input(ui["topic"], "School")
        level = st.selectbox(ui["level"], ["HSK 1", "HSK 2", "HSK 3"])
        keys = st.text_input(ui["keywords"], "书, 学习")
        
        if st.button(ui["gen_btn"]):
            with st.spinner(ui["loading"]):
                res = call_ai(topic, level, keys)
                if res:
                    st.session_state.current_data = res
                    st.session_state.audio_file = ""
                    st.rerun()
        
        st.divider()
        # ✨ 开关回归
        show_pinyin = st.toggle(ui["show_py"], value=True)
        show_trans = st.toggle(ui["show_tr"], value=True)
        
        if st.button(f"🔄 {ui['refresh']}"):
            st.session_state.audio_file = ""
            st.rerun()

    st.markdown('<div class="main-title">Reading Assistant Pro</div>', unsafe_allow_html=True)

    if st.session_state.current_data:
        if not st.session_state.audio_file:
            fname = f"audio_{int(time.time())}.mp3"
            st.session_state.ts = asyncio.run(make_audio(st.session_state.current_data, fname))
            st.session_state.audio_file = fname
        
        if os.path.exists(st.session_state.audio_file):
            st.components.v1.html(get_player_html(st.session_state.audio_file, st.session_state.ts), height=80)

        # 构建 class，控制显示隐藏
        container_class = ""
        if not show_pinyin: container_class += " hide-pinyin"
        if not show_trans: container_class += " hide-trans"

        # 拼接 HTML (无缩进，防止代码裸奔)
        html_str = f'<div class="{container_class}">'
        for idx, line in enumerate(st.session_state.current_data):
            trans = line.get("tr_es", "") if ui_lang == "Español" else line.get("tr_en", "")
            
            # 汉字拼音部分
            hanzi_html = ""
            for char, py in line.get("t", []):
                hanzi_html += f'<ruby>{char}<rt>{py}</rt></ruby>'
            
            # 组合一行
            html_str += f'<div class="row-container" id="row-{idx}"><div class="left-box">{trans}</div><div class="right-box"><span class="role-tag">{line["r"]}</span>{hanzi_html}</div></div>'
        
        html_str += '</div>'
        
        # 渲染主内容
        st.markdown(html_str, unsafe_allow_html=True)
        
        # 底部固定打字框 (使用 JS 移动到 .fixed-bottom)
        st.markdown(f'<div class="fixed-bottom"><div style="color:#3b82f6; font-weight:bold; margin-bottom:5px;">{ui["instr"]}</div></div>', unsafe_allow_html=True)
        st.text_input("user_input", label_visibility="collapsed", placeholder="...")
        
        # JS 魔法：把输入框搬到固定底部
        st.markdown("""
        <script>
            const inputEl = window.parent.document.querySelector('.stTextInput');
            const footerEl = window.parent.document.querySelector('.fixed-bottom');
            if(inputEl && footerEl) { footerEl.appendChild(inputEl); }
        </script>
        """, unsafe_allow_html=True)

    else:
        st.info("👈 Please enter settings and click Generate")

if __name__ == "__main__":
    main()
