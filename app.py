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

# 获取 Key
MY_API_KEY = os.environ.get("GOOGLE_API_KEY")

# 🔒 锁定成功的模型
TARGET_MODEL = 'models/gemini-2.5-flash'

# 🌍 语言包 (恢复)
UI_TEXT = {
    "Español": { 
        "pinyin": "Pinyin", "trans": "Traducción", "typing_instr": "✍️ Instrucción: Escribe el texto de arriba para practicar.", 
        "refresh": "Regenerar Audio", "gen_btn": "Generar Lección ✨", 
        "topic": "Tema", "level": "Nivel (HSK)", "keywords": "Palabras clave",
        "thinking": "Gemini 2.5 está pensando..."
    },
    "English": { 
        "pinyin": "Pinyin", "trans": "Translation", "typing_instr": "✍️ Instruction: Type the text above to practice.", 
        "refresh": "Regenerate Audio", "gen_btn": "Generate Lesson ✨", 
        "topic": "Topic", "level": "Level (HSK)", "keywords": "Keywords",
        "thinking": "Gemini 2.5 is thinking..."
    }
}

# 🎨 样式修复 (重点修复文字溢出)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] { background-color: #FFFBF0; }
    
    .main-title { 
        text-align: center; font-family: 'Noto Serif SC', serif; 
        font-weight: 900; color: #334155; font-size: 1.8rem; margin: 20px 0; 
    }
    
    .reading-scroll-area { 
        background-color: white; padding: 30px; border-radius: 1.5rem; 
        border: 2px solid #eee; min-height: 300px; margin-bottom: 20px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }
    
    /* 修复：行容器，确保对齐 */
    .line-container { 
        display: flex; flex-direction: row; 
        align-items: flex-start; /* 顶部对齐，防止高度塌陷 */
        margin-bottom: 25px; padding: 15px; 
        border-bottom: 1px dashed #f0f0f0; 
        border-radius: 10px;
        transition: all 0.3s ease;
    }

    /* 角色标签样式 */
    .role-label { 
        min-width: 60px; font-weight: 900; color: #BE185D; 
        font-size: 1.1rem; margin-top: 5px; /* 微调对齐 */
        margin-right: 15px;
    }
    
    /* 🔴 核心修复：文字包裹层 */
    .text-wrapper {
        display: flex; 
        flex-wrap: wrap; /* 允许换行！ */
        gap: 5px; /* 字与字之间的间距 */
        align-items: flex-end;
        width: 100%;
    }
    
    ruby { 
        ruby-position: under; 
        font-size: 26px; font-weight: 900; color: #333; 
        line-height: 2.2; /* 增加行高，防止拼音重叠 */
    }
    
    rt { 
        font-size: 13px; color: #666; font-weight: 700; 
        transform: translateY(-5px);
    }
    
    .trans-text {
        width: 100%; font-size: 0.95rem; color: #64748b; 
        margin-top: 8px; font-style: italic; display: block;
    }

    .typing-section { 
        background: #fff; padding: 15px 20px; border-radius: 1rem; 
        border: 2px solid #3B82F6; margin-top: 10px; 
    }
    
    .hide-pinyin rt { display: none !important; }
    
    /* 高亮样式 */
    .active-meimei { background-color: #dcfce7 !important; border-left: 5px solid #22c55e !important; }
    .active-dawei { background-color: #dbeafe !important; border-left: 5px solid #3b82f6 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. AI 调用 (Gemini 2.5 + 强制标点) ---
def call_ai(topic, level, keywords):
    if not MY_API_KEY: return None
    try:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel(TARGET_MODEL)
        
        safety = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # 🔴 提示词升级：强制要求标点符号
        prompt = f"""
        Act as a JSON API. Create a Chinese dialogue (4-6 lines) between '美美' (Female) and '大卫' (Male).
        Topic: {topic}. Level: {level}. Keywords: {keywords}.
        
        IMPORTANT RULES:
        1. Include standard punctuation (，。？！) in the text list.
        2. Punctuation should have an empty string "" as pinyin.
        3. STRICTLY OUTPUT JSON ARRAY. NO MARKDOWN.
        
        Format example: 
        [{{"r": "美美", "t": [["你", "nǐ"], ["好", "hǎo"], ["，", ""]], "tr_es": "Hola", "tr_en": "Hi"}}]
        """
        
        response = model.generate_content(prompt, safety_settings=safety)
        text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)

    except Exception as e:
        st.error(f"💥 Error: {str(e)}")
        return None

# --- 3. 语音合成 ---
async def make_audio(data, filename):
    ts = []
    curr = 0.0
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(data):
            voice = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
            raw = "".join([p[0] for p in line.get("t", [])])
            # 语速调整：0.3秒一个字 + 1.2秒缓冲
            dur = len(raw) * 0.3 + 1.2 
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

# --- 4. 播放器组件 ---
def get_player_html(file_path, ts):
    with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    return f"""
    <div style="display:flex; flex-direction:column; align-items:center; background:white; padding:10px; border-radius:12px; border:1px solid #e2e8f0; margin-bottom:20px;">
        <audio id="p" controls src="data:audio/mp3;base64,{b64}" style="width:100%; max-width:600px; height:40px;"></audio>
        <div style="margin-top:5px; display:flex; gap:10px;">
            <button onclick="p.playbackRate=0.8" style="cursor:pointer; padding:2px 10px; border:1px solid #ccc; border-radius:5px; background:#f8fafc;">🐢 0.8x</button>
            <button onclick="p.playbackRate=1.0" style="cursor:pointer; padding:2px 10px; border:1px solid #ccc; border-radius:5px; background:#f8fafc;">▶ 1.0x</button>
            <button onclick="p.playbackRate=1.2" style="cursor:pointer; padding:2px 10px; border:1px solid #ccc; border-radius:5px; background:#f8fafc;">🐇 1.2x</button>
        </div>
    </div>
    <script>
        const p = document.getElementById('p');
        const ts = {json.dumps(ts)};
        p.ontimeupdate = () => {{
            const cur = p.currentTime / p.playbackRate;
            ts.forEach((t, i) => {{
                const el = window.parent.document.getElementById('line-'+i);
                if (el) {{
                    if (cur >= t.start && cur < t.end) {{
                        el.classList.add(t.role === "美美" ? "active-meimei" : "active-dawei");
                        el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }} else {{
                        el.classList.remove("active-meimei", "active-dawei");
                    }}
                }}
            }});
        }};
    </script>
    """

def main():
    if "current_data" not in st.session_state: st.session_state.current_data = None
    if "audio_file" not in st.session_state: st.session_state.audio_file = ""

    # 侧边栏设置
    with st.sidebar:
        st.title("🐼 AI Settings")
        st.success(f"🚀 Model: {TARGET_MODEL}")
        
        # 🌍 语言选择 (找回来了！)
        ui_lang = st.selectbox("Interface Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        
        topic = st.text_input(ui["topic"], "Shopping")
        level = st.selectbox(ui["level"], ["HSK 1", "HSK 2", "HSK 3"])
        keys = st.text_input(ui["keywords"], "苹果, 多少钱")
        
        if st.button(ui["gen_btn"]):
            with st.spinner(ui["thinking"]):
                res = call_ai(topic, level, keys)
                if res:
                    st.session_state.current_data = res
                    st.session_state.audio_file = ""
                    st.rerun()
                    
        st.divider()
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=True)
        if st.button(f"🔄 {ui['refresh']}"):
            st.session_state.audio_file = ""
            st.rerun()

    # 主界面
    st.markdown('<div class="main-title">Reading Assistant Pro</div>', unsafe_allow_html=True)
    
    if st.session_state.current_data:
        # 1. 音频处理
        if not st.session_state.audio_file:
            fname = f"audio_{int(time.time())}.mp3"
            st.session_state.ts = asyncio.run(make_audio(st.session_state.current_data, fname))
            st.session_state.audio_file = fname
        
        if os.path.exists(st.session_state.audio_file):
            st.components.v1.html(get_player_html(st.session_state.audio_file, st.session_state.ts), height=120)

        # 2. 课文显示 (带换行修复)
        p_class = "" if show_pinyin else "hide-pinyin"
        
        html_content = f'<div class="reading-scroll-area {p_class}">'
        for idx, line in enumerate(st.session_state.current_data):
            # 每一行的容器
            html_content += f'<div class="line-container" id="line-{idx}">'
            # 角色标签
            html_content += f'<div class="role-label">{line["r"]}</div>'
            # 文字包裹层 (text-wrapper 负责换行)
            html_content += '<div class="text-wrapper">'
            
            for char, py in line.get("t", []):
                # 如果是标点，且拼音为空，依然渲染 ruby 结构以保持对齐，或者特殊处理
                html_content += f'<ruby>{char}<rt>{py}</rt></ruby>'
                
            html_content += '</div></div>' # 结束 text-wrapper 和 line-container
            
            # 翻译显示
            if show_trans:
                trans = line.get("tr_es", "") if ui_lang == "Español" else line.get("tr_en", "")
                html_content += f'<div class="trans-text" style="margin-left:75px; margin-bottom:15px;">{trans}</div>'
                
        html_content += '</div>'
        st.markdown(html_content, unsafe_allow_html=True)
        
        # 3. 打字练习区 (找回来了！)
        st.markdown(f'<div class="typing-section"><p style="color:#1E40AF; font-weight:bold;">{ui["typing_instr"]}</p></div>', unsafe_allow_html=True)
        st.text_input("input_area", placeholder="...", label_visibility="collapsed")
        
    else:
        st.info("👈 Please enter a topic and click 'Generate Lesson'")

if __name__ == "__main__":
    main()
