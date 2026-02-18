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

# 获取环境变量
MY_API_KEY = os.environ.get("GOOGLE_API_KEY")

# 强制注入 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FFFBF0; }
    .main-title { text-align: center; font-family: 'Noto Serif SC', serif; font-weight: 900; color: #334155; font-size: 1.8rem; margin: 20px 0; }
    .reading-scroll-area { background-color: white; padding: 30px; border-radius: 1.5rem; border: 2px solid #eee; min-height: 300px; margin-bottom: 20px; }
    .line-container { display: flex; margin-bottom: 12px; padding: 10px; border-radius: 12px; }
    .active-meimei { background-color: #dcfce7 !important; border-left: 5px solid #22c55e !important; }
    .active-dawei { background-color: #dbeafe !important; border-left: 5px solid #3b82f6 !important; }
    .role-label { min-width: 60px; font-weight: 900; color: #BE185D; }
    ruby { ruby-position: under; padding: 0 3px; font-size: 26px; font-weight: 900; color: #333; }
    rt { font-size: 13px; color: #666; font-weight: 700; }
    /* 错误提示框 */
    .error-box { background-color: #FEF2F2; border: 1px solid #EF4444; color: #B91C1C; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- 2. 只有真 AI 调用 (使用最稳定的 1.5 Flash) ---
def call_stable_ai(topic, level, keywords):
    if not MY_API_KEY:
        st.error("❌ Key missing in Environment Variables")
        return None
    try:
        genai.configure(api_key=MY_API_KEY)
        
        # 💡 关键修改：使用 gemini-1.5-flash (正式版，最稳定)
        # 不要用 2.0-flash-exp 了，那个不稳定
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 彻底关闭安全拦截
        safety = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        prompt = f"""
        Act as a Chinese teacher. Create a dialogue (4-6 sentences) between '美美' (Female) and '大卫' (Male).
        Topic: {topic}. Level: {level}. Keywords: {keywords}.
        
        STRICTLY OUTPUT JSON ARRAY. No markdown.
        Format: [{{"r": "美美", "t": [["你", "nǐ"], ["好", "hǎo"]], "tr_es": "Hola", "tr_en": "Hi"}}]
        """
        
        response = model.generate_content(prompt, safety_settings=safety)
        text = response.text.strip()
        if "```" in text: text = text.replace("```json", "").replace("```", "")
        return json.loads(text)

    except Exception as e:
        # 如果出错，直接把真实错误显示出来
        st.markdown(f'<div class="error-box">💥 AI Error Log:<br>{str(e)}</div>', unsafe_allow_html=True)
        return None

# --- 3. 语音合成 ---
async def make_audio(data, filename):
    ts = []
    curr = 0.0
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(data):
            voice = "zh-CN-XiaoxiaoNeural" if line["r"] in ["美美", "System"] else "zh-CN-YunxiNeural"
            raw = "".join([p[0] for p in line.get("t", [])])
            if not raw: continue
            
            dur = len(raw) * 0.28
            if dur < 1.0: dur = 1.0
            
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

# --- 4. 主程序 ---
def main():
    st.markdown('<div class="main-title">Reading Assistant Pro</div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.title("🐼 AI Settings")
        if MY_API_KEY: 
            st.success(f"✅ Key Loaded (US Server)")
        else: 
            st.error("❌ Key Missing")
            
        topic = st.text_input("Topic", "Shopping")
        level = st.selectbox("Level", ["HSK 1", "HSK 2", "HSK 3"])
        keys = st.text_input("Keywords", "苹果, 多少钱")
        
        if st.button("Generate Lesson ✨"):
            with st.spinner("AI is creating lesson..."):
                res = call_stable_ai(topic, level, keys)
                if res:
                    st.session_state.current_data = res
                    st.session_state.audio_file = ""
                    st.rerun()

    if "current_data" in st.session_state:
        # 自动生成语音
        if not st.session_state.get("audio_file"):
            fname = f"audio_{int(time.time())}.mp3"
            st.session_state.ts = asyncio.run(make_audio(st.session_state.current_data, fname))
            st.session_state.audio_file = fname
        
        # 显示播放器
        if os.path.exists(st.session_state.audio_file):
            with open(st.session_state.audio_file, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<audio controls src="data:audio/mp3;base64,{b64}" style="width:100%"></audio>', unsafe_allow_html=True)
        
        # 显示课文
        st.markdown('<div class="reading-scroll-area">', unsafe_allow_html=True)
        for idx, line in enumerate(st.session_state.current_data):
            html = f'<div class="line-container" id="line-{idx}"><div class="role-label">{line["r"]}</div><div>'
            for char, py in line.get("t", []): html += f'<ruby>{char}<rt>{py}</rt></ruby>'
            html += f'</div></div><div style="font-size:0.9rem; color:gray; margin-bottom:15px; margin-left:60px;">{line.get("tr_es","")}</div>'
            st.markdown(html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("👈 Please enter a topic and click 'Generate Lesson'")

if __name__ == "__main__":
    main()
