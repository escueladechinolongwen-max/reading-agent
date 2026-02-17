import streamlit as st
import asyncio
import edge_tts
import os
import time
import re
import base64
import json

# --- 1. 页面配置与 CSS 强化 ---
st.set_page_config(page_title="Long Wen AI Reading", page_icon="🐼", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FFFBF0; overflow: hidden !important; height: 100vh; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 0rem !important; max-width: 1200px !important; height: 100vh; display: flex; flex-direction: column; }
    
    /* 强制显示左上角按钮 */
    header[data-testid="stHeader"] { background-color: transparent !important; visibility: visible !important; z-index: 1000000 !important; }
    [data-testid="collapsedControl"] { background-color: white !important; border-radius: 0 10px 10px 0 !important; box-shadow: 2px 2px 10px rgba(0,0,0,0.1) !important; color: #BE185D !important; visibility: visible !important; display: flex !important; z-index: 1000001 !important; }
    #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"], footer { visibility: hidden; }

    .main-title { text-align: center; font-family: 'Noto Serif SC', serif; font-weight: 900; color: #334155; font-size: 1.6rem; margin-bottom: 5px; margin-top: -30px; }
    
    /* 阅读框锁定高度 */
    .reading-scroll-area {
        background-color: white; padding: 20px 30px; border-radius: 1.5rem; border: 2px solid #eee; overflow-y: auto !important; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.03); height: calc(100vh - 360px) !important; margin-bottom: 15px; scroll-behavior: smooth;
    }

    .line-container { display: flex; margin-bottom: 8px; align-items: flex-start; justify-content: space-between; padding: 10px; border-radius: 12px; transition: all 0.4s ease; border-bottom: 1px solid #fcfcfc;}
    .active-meimei { background-color: #f0fdf4 !important; border: 1px solid #4ade80 !important; }
    .active-dawei { background-color: #eff6ff !important; border: 1px solid #60a5fa !important; }
    
    .role-label { min-width: 50px; font-weight: 900; color: #BE185D; font-size: 1rem; padding-top: 6px; font-family: 'Noto Serif SC', serif; }
    ruby { ruby-position: under; padding: 0 2px; font-family: "Noto Serif SC", serif; font-size: 24px; font-weight: 900; color: #333; }
    rt { font-family: 'Noto Sans SC', sans-serif; font-size: 12px; color: #666; font-weight: 700; }
    
    .right-zone { width: 22%; background: #f8fafc; border-left: 3px solid #cbd5e1; padding: 6px 10px; border-radius: 8px; }
    .trans-text { font-size: 0.8rem; color: #64748b; font-weight: 700; }

    .typing-section { background: #fff; padding: 12px 20px; border-radius: 1rem; border: 2px solid #3B82F6; margin-bottom: 10px; box-shadow: 0 -4px 15px rgba(59, 130, 246, 0.1); }
    .instr-text { color: #1E40AF; font-size: 0.9em; font-weight: 800; margin-bottom: 5px; }
    .hide-pinyin rt { display: none !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. AI 核心逻辑 (模拟) ---
def ai_generate_lesson(topic):
    # 这里未来可以接入真正的 Gemini API
    # 模拟生成的对话数据
    return [
        {"r": "美美", "t": [("这里", "zhèlǐ"), ("的", "de"), ("景色", "jǐngsè"), ("真", "zhēn"), ("美", "měi"), ("！", "")] , "tr_es": "¡El paisaje aquí es hermoso!", "tr_en": "The scenery here is beautiful!"},
        {"r": "大卫", "t": [("是的", "shìde"), ("，", ""), ("我", "wǒ"), ("很", "hěn"), ("喜欢", "xǐhuan"), ("这里", "zhèlǐ"), ("。", "")] , "tr_es": "Sí, me gusta mucho este lugar.", "tr_en": "Yes, I like this place very much."}
    ]

# --- 3. 语音与时间戳逻辑 ---
async def make_audio_v28(lesson_data, filename):
    timestamps = []
    curr = 0.0
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(lesson_data):
            voice = "zh-CN-XiaoxiaoNeural" if line["r"] == "美美" else "zh-CN-YunxiNeural"
            raw = "".join([p[0] for p in line["t"]])
            clean = re.sub(r'[^\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef0-9]', '', raw)
            
            dur = len(clean) * 0.45 + 0.6
            timestamps.append({"start": curr, "end": curr + dur, "role": line["r"]})
            
            communicate = edge_tts.Communicate(clean, voice)
            temp_f = f"v28_{i}.mp3"
            await communicate.save(temp_f)
            with open(temp_f, 'rb') as f: final_file.write(f.read())
            os.remove(temp_f)
            curr += dur
    return timestamps

def get_audio_player_v28(file_path, ts):
    with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    return f"""
    <div style="display:flex; flex-direction:column; align-items:center; background:white; padding:8px; border-radius:12px; border:1px solid #e2e8f0; margin-bottom:10px;">
        <audio id="p" controls src="data:audio/mp3;base64,{b64}" style="width:100%; max-width:450px; height:32px;"></audio>
        <div style="margin-top:5px; display:flex; gap:10px;">
            <button onclick="p.playbackRate=0.8" style="cursor:pointer; border-radius:4px; border:1px solid #ddd; padding:2px 8px;">🐢 0.8x</button>
            <button onclick="p.playbackRate=1.0" style="cursor:pointer; border-radius:4px; border:1px solid #ddd; padding:2px 8px;">▶ 1.0x</button>
            <button onclick="p.playbackRate=1.2" style="cursor:pointer; border-radius:4px; border:1px solid #ddd; padding:2px 8px;">🐇 1.2x</button>
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
                        el.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
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
    if "data_v28" not in st.session_state: st.session_state.data_v28 = []
    if "audio_v28" not in st.session_state: st.session_state.audio_v28 = ""
    if "ts_v28" not in st.session_state: st.session_state.ts_v28 = []

    with st.sidebar:
        st.title("🐼 AI Workshop")
        mode = st.radio("Mode", ["Preset Lessons", "AI Generator 🤖"])
        
        if mode == "AI Generator 🤖":
            topic = st.text_input("Enter Topic (e.g. Shopping)", "Fruits")
            if st.button("Generate Lesson ✨"):
                st.session_state.data_v28 = ai_generate_lesson(topic)
                st.session_state.audio_v28 = "" # 强制更新音频
        else:
            # 原有的 Dialogue I 逻辑
            st.session_state.data_v28 = [
                {"r": "美美", "t": [("大卫", "Dàwèi"), ("，", ""), ("请问", "qǐngwèn"), ("今天", "jīntiān"), ("几号", "jǐ hào"), ("？", "")] , "tr_es": "¿Qué fecha es hoy?", "tr_en": "What date is today?"},
                {"r": "大卫", "t": [("今天", "jīntiān"), ("9月1号", "jiǔ yuè yī hào"), ("。", "")] , "tr_es": "1 de septiembre.", "tr_en": "September 1st."}
            ]

        st.divider()
        ui_lang = st.selectbox("Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        show_pinyin = st.toggle(ui["pinyin"], value=True)
        show_trans = st.toggle(ui["trans"], value=False)

    # 渲染
    st.markdown(f'<div class="main-title">{"AI Lesson" if mode != "Preset Lessons" else "Dialogue I"}</div>', unsafe_allow_html=True)
    
    if st.session_state.data_v28 and not st.session_state.audio_v28:
        fname = f"v28_{int(time.time())}.mp3"
        st.session_state.ts_v28 = asyncio.run(make_audio_v28(st.session_state.data_v28, fname))
        st.session_state.audio_v28 = fname
    
    if os.path.exists(st.session_state.audio_v28):
        st.components.v1.html(get_audio_player_v28(st.session_state.audio_v28, st.session_state.ts_v28), height=100)

    p_class = "" if show_pinyin else "hide-pinyin"
    html = f'<div class="reading-scroll-area {p_class}">'
    for idx, line in enumerate(st.session_state.data_v28):
        html += f'<div class="line-container" id="line-{idx}">'
        html += f'<div class="left-zone"><div class="role-label">{line["r"]}</div><div>'
        for char, py in line["t"]:
            html += f'<ruby>{char}<rt>{py}</rt></ruby>' if show_pinyin and py else f'<ruby style="line-height:1.4;">{char}</ruby>'
        html += '</div></div>'
        if show_trans:
            html += f'<div class="right-zone"><span class="trans-text">{line["tr_es"] if ui_lang=="Español" else line["tr_en"]}</span></div>'
        html += '</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)

    st.markdown(f'<div class="typing-section"><p class="instr-text">✍️ {ui["typing_instr"]}</p></div>', unsafe_allow_html=True)
    st.text_input("inp", placeholder="...", label_visibility="collapsed")

if __name__ == "__main__":
    main()
