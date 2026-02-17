import streamlit as st
import asyncio
import edge_tts
import os
import time
import re
import base64
import json
import google.generativeai as genai  # 引入 AI 库

# --- 1. 配置与样式 ---
st.set_page_config(page_title="Long Wen Reading Pro", page_icon="🐼", layout="wide", initial_sidebar_state="expanded")

# 🔑 请在这里填入您的 API KEY (等会我教您怎么申请) 🔑
# 如果没有 Key，请保持为空，系统会使用模拟数据
MY_API_KEY = ""  # <--- 把 Key 粘贴在这里

UI_TEXT = {
    "Español": { "pinyin": "Pinyin", "trans": "Traducción", "typing_instr": "Instrucción: Sigue el texto de arriba para practicar.", "refresh": "Regenerar Audio", "gen_btn": "Generar Lección ✨", "topic": "Tema", "level": "Nivel (HSK)", "keywords": "Palabras clave" },
    "English": { "pinyin": "Pinyin", "trans": "Translation", "typing_instr": "Instruction: Follow the text above to practice.", "refresh": "Regenerate Audio", "gen_btn": "Generate Lesson ✨", "topic": "Topic", "level": "Level (HSK)", "keywords": "Keywords" }
}

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FFFBF0; overflow: hidden !important; height: 100vh; }
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; max-width: 1200px !important; height: 100vh; display: flex; flex-direction: column; }
    
    header[data-testid="stHeader"] { background-color: transparent !important; visibility: visible !important; height: 0px !important; z-index: 100; }
    [data-testid="collapsedControl"] { visibility: visible !important; display: flex !important; background-color: #BE185D !important; color: white !important; border-radius: 50% !important; padding: 0.5rem !important; top: 60px !important; left: 20px !important; box-shadow: 2px 2px 10px rgba(0,0,0,0.2) !important; z-index: 999999 !important; transition: transform 0.2s; }
    [data-testid="collapsedControl"]:hover { transform: scale(1.1); }
    #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"], footer { visibility: hidden; }

    .main-title { text-align: center; font-family: 'Noto Serif SC', serif; font-weight: 900; color: #334155; font-size: 1.6rem; margin-bottom: 5px; margin-top: -10px; }
    .reading-scroll-area { background-color: white; padding: 20px 30px; border-radius: 1.5rem; border: 2px solid #eee; overflow-y: auto !important; box-shadow: 0 4px 15px rgba(0,0,0,0.03); height: calc(100vh - 380px) !important; margin-bottom: 15px; scroll-behavior: smooth; }
    .line-container { display: flex; margin-bottom: 8px; padding: 10px; border-radius: 12px; transition: all 0.2s ease; border-bottom: 1px solid #fcfcfc;} /* 动画加速 */
    
    /* 变色样式 */
    .active-meimei { background-color: #dcfce7 !important; border-left: 5px solid #22c55e !important; transform: scale(1.005); }
    .active-dawei { background-color: #dbeafe !important; border-left: 5px solid #3b82f6 !important; transform: scale(1.005); }
    
    .role-label { min-width: 50px; font-weight: 900; color: #BE185D; font-size: 1rem; padding-top: 6px; }
    ruby { ruby-position: under; padding: 0 2px; font-size: 24px; font-weight: 900; color: #333; }
    rt { font-size: 12px; color: #666; font-weight: 700; }
    .typing-section { background: #fff; padding: 12px 20px; border-radius: 1rem; border: 2px solid #3B82F6; margin-bottom: 10px; }
    .instr-text { color: #1E40AF; font-size: 0.9em; font-weight: 800; margin-bottom: 5px; }
    .hide-pinyin rt { display: none !important; }
</style>
""", unsafe_allow_html=True)

LESSONS = {
    "Dialogue I": [
        {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , "tr_es": "¿Qué fecha es hoy?", "tr_en": "What date is today?"},
        {"r": "大卫", "t": [("今天", "jīntiān"), ("9月1号", "jiǔ yuè yī hào"), ("。", "")] , "tr_es": "1 de septiembre.", "tr_en": "September 1st."}
    ]
}

# --- 2. 真实的 AI 调用逻辑 ---
def call_real_ai(topic, level, keywords):
    if not MY_API_KEY:
        # 没填 Key 时返回假数据
        return [
            {"r": "System", "t": [("请", "qǐng"), ("配置", "pèizhì"), ("API", ""), ("Key", ""), ("。", "")] , "tr_es": "Por favor configure la clave API.", "tr_en": "Please configure API Key."}
        ]
    
    try:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Act as a Chinese teacher. Create a short dialogue (4-6 lines) between '美美' (Meimei, female) and '大卫' (David, male).
        Topic: {topic}
        HSK Level: {level}
        Must include keywords: {keywords}
        
        Output STRICT JSON format:
        [
          {{"r": "美美", "t": [["汉", "hàn"], ["字", "zì"]], "tr_es": "Spanish trans", "tr_en": "English trans"}},
          ...
        ]
        Make sure 't' is a list of [character, pinyin] pairs. Use empty string for punctuation pinyin.
        """
        response = model.generate_content(prompt)
        # 清理返回的 JSON 字符串 (有些 AI 会带 ```json ```)
        clean_json = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_json)
    except Exception as e:
        return [{"r": "Error", "t": [("出错", "chūcuò"), ("了", "le")], "tr_es": str(e), "tr_en": str(e)}]

# --- 3. 语音生成 (修正时间公式) ---
async def make_audio_v30(lesson_data, filename):
    timestamps = []
    curr = 0.0
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(lesson_data):
            voice = "zh-CN-XiaoxiaoNeural" if line["r"] in ["美美", "System", "Error"] else "zh-CN-YunxiNeural"
            raw = "".join([p[0] for p in line["t"]])
            
            # ⚡ 极速公式: 字数 * 0.28s + 0s (无缓冲)
            dur = len(raw) * 0.28
            if dur < 1.0: dur = 1.0 # 最少给1秒，防止短句闪太快
            
            timestamps.append({"start": curr, "end": curr + dur, "role": line["r"]})
            
            # 错误处理
            if not raw.strip(): raw = "空" 
            
            communicate = edge_tts.Communicate(raw, voice)
            temp_f = f"temp_{i}.mp3"
            await communicate.save(temp_f)
            with open(temp_f, 'rb') as f: final_file.write(f.read())
            os.remove(temp_f)
            curr += dur
    return timestamps

def get_player_html(file_path, ts):
    with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    return f"""
    <div style="display:flex; flex-direction:column; align-items:center; background:white; padding:8px; border-radius:12px; border:1px solid #e2e8f0; margin-bottom:10px;">
        <audio id="p" controls src="data:audio/mp3;base64,{b64}" style="width:100%; max-width:450px; height:32px;"></audio>
        <div style="margin-top:5px; display:flex; gap:10px;">
            <button onclick="p.playbackRate=0.8" style="cursor:pointer; padding:2px 8px; border:1px solid #ccc; border-radius:4px;">🐢 0.8x</button>
            <button onclick="p.playbackRate=1.0" style="cursor:pointer; padding:2px 8px; border:1px solid #ccc; border-radius:4px;">▶ 1.0x</button>
            <button onclick="p.playbackRate=1.2" style="cursor:pointer; padding:2px 8px; border:1px solid #ccc; border-radius:4px;">🐇 1.2x</button>
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
                    // 更精准的判定区间
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

# --- 4. 主程序 ---
def main():
    if "data_v30" not in st.session_state: st.session_state.data_v30 = LESSONS["Dialogue I"]
    if "audio_v30" not in st.session_state: st.session_state.audio_v30 = ""
    if "ts_v30" not in st.session_state: st.session_state.ts_v30 = []

    with st.sidebar:
        st.title("🐼 AI Workshop")
        mode = st.radio("Mode", ["Preset Lessons", "AI Generator 🤖"])
        
        ui_lang = st.selectbox("UI Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]

        if mode == "AI Generator 🤖":
            # 🔴 这里是您要求的限定条件输入框
            topic = st.text_input(ui["topic"], "Shopping / Comprar")
            col1, col2 = st.columns(2)
            with col1:
                level = st.selectbox(ui["level"], ["HSK 1", "HSK 2", "HSK 3"])
            with col2:
                keywords = st.text_input(ui["keywords"], "多少钱, 苹果")
            
            if st.button(ui["gen_btn"]):
                with st.spinner("AI is thinking..."):
                    st.session_state.data_v30 = call_real_ai(topic, level, keywords)
                    st.session_state.audio_v30 = "" # 强制更新
                    st.rerun()
        else:
            lesson_key = st.selectbox("Lección", list(LESSONS.keys()))
            if st.session_state.get("last_key") != lesson_key:
                st.session_state.data_v30 = LESSONS[lesson_key]
                st.session_state.audio_v30 = ""
                st.session_state.last_key = lesson_key
        
        st.divider()
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)
        if st.button(f"🔄 {ui['refresh']}"):
            st.session_state.audio_v30 = ""
            st.rerun()

    st.markdown(f'<div class="main-title">Reading Assistant</div>', unsafe_allow_html=True)
    
    # 自动生成音频
    if not st.session_state.audio_v30:
        fname = f"v30_{int(time.time())}.mp3"
        st.session_state.ts_v30 = asyncio.run(make_audio_v30(st.session_state.data_v30, fname))
        st.session_state.audio_v30 = fname
    
    if os.path.exists(st.session_state.audio_v30):
        st.components.v1.html(get_player_html(st.session_state.audio_v30, st.session_state.ts_v30), height=100)

    p_class = "" if show_pinyin else "hide-pinyin"
    html = f'<div class="reading-scroll-area {p_class}">'
    for idx, line in enumerate(st.session_state.data_v30):
        html += f'<div class="line-container" id="line-{idx}">'
        html += f'<div style="display:flex; flex:1;"><div class="role-label">{line["r"]}</div><div>'
        for char, py in line["t"]:
            html += f'<ruby>{char}<rt>{py}</rt></ruby>' if show_pinyin and py else f'<ruby>{char}</ruby>'
        html += '</div></div>'
        if show_trans:
            html += f'<div class="right-zone"><span style="font-size:0.8rem;">{line["tr_es"] if ui_lang=="Español" else line["tr_en"]}</span></div>'
        html += '</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)

    st.markdown(f'<div class="typing-section"><p class="instr-text">✍️ {ui["typing_instr"]}</p></div>', unsafe_allow_html=True)
    st.text_input("inp", placeholder="...", label_visibility="collapsed")

if __name__ == "__main__":
    main()
