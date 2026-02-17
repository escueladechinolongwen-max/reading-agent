import streamlit as st
import asyncio
import edge_tts
import os
import time
import base64
import json
import google.generativeai as genai

# --- 1. 核心配置 ---
st.set_page_config(page_title="Long Wen Debugger", page_icon="🐞", layout="wide", initial_sidebar_state="expanded")

# 尝试获取 Key
MY_API_KEY = os.environ.get("GOOGLE_API_KEY")

# 样式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FFFBF0; }
    .stApp { max-width: 1000px; margin: 0 auto; }
    .error-box { background-color: #fef2f2; border: 2px solid #ef4444; color: #991b1b; padding: 20px; border-radius: 10px; font-weight: bold; margin-bottom: 20px; }
    .success-box { background-color: #f0fdf4; border: 2px solid #22c55e; color: #166534; padding: 10px; border-radius: 10px; margin-bottom: 10px; }
    
    /* 阅读区样式 */
    .reading-box { background: white; padding: 20px; border-radius: 15px; border: 1px solid #ddd; min-height: 200px; }
    .line-container { display: flex; margin-bottom: 10px; border-bottom: 1px solid #f0f0f0; padding-bottom: 5px; }
    .role { width: 60px; font-weight: bold; color: #BE185D; margin-right: 10px; }
    ruby { font-size: 22px; margin-right: 5px; }
    rt { font-size: 12px; color: #666; }
</style>
""", unsafe_allow_html=True)

# --- 2. 只有真 AI，没有假数据 ---
def call_real_ai_debug(topic, level, keywords):
    # 1. 检查 Key 是否存在
    if not MY_API_KEY:
        st.markdown('<div class="error-box">💀 FATAL ERROR: 环境变量 GOOGLE_API_KEY 未找到！请在 Render Dashboard 中检查拼写。</div>', unsafe_allow_html=True)
        return None
    
    try:
        # 2. 配置 AI
        genai.configure(api_key=MY_API_KEY)
        
        # 3. 使用最稳定的模型
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Generate a JSON list for a Chinese dialogue between '美美' and '大卫'.
        Topic: {topic}. Level: {level}. Keywords: {keywords}.
        Format: [{{"r":"美美", "t":[["你","nǐ"],["好","hǎo"]], "tr_es":"Hola", "tr_en":"Hi"}}]
        Output JSON ONLY.
        """
        
        # 4. 发送请求 (这是最容易报错的一步)
        response = model.generate_content(prompt)
        
        # 5. 解析
        text = response.text.strip()
        if "```" in text: text = text.replace("```json", "").replace("```", "")
        return json.loads(text)

    except Exception as e:
        # 🔥 关键：直接把 Python 的错误甩到脸上
        st.markdown(f'<div class="error-box">💥 API CRASHED (报错详情):<br>{str(e)}</div>', unsafe_allow_html=True)
        return None

# --- 3. 语音合成 ---
async def make_audio(data, fname):
    if not data: return []
    ts = []
    curr = 0
    with open(fname, 'wb') as f_out:
        for i, line in enumerate(data):
            voice = "zh-CN-XiaoxiaoNeural" if line['r'] == "美美" else "zh-CN-YunxiNeural"
            txt = "".join([x[0] for x in line['t']])
            comm = edge_tts.Communicate(txt, voice)
            temp = f"tmp_{i}.mp3"
            await comm.save(temp)
            with open(temp, 'rb') as f_temp: f_out.write(f_temp.read())
            ts.append({'start': curr, 'end': curr + len(txt)*0.3 + 1.0, 'role': line['r']})
            curr += len(txt)*0.3 + 1.0
            os.remove(temp)
    return ts

# --- 4. 主程序 ---
def main():
    st.title("🐼 Reading Pro: Debug Mode")
    
    # 状态自检栏
    if MY_API_KEY:
        masked_key = MY_API_KEY[:5] + "..." + MY_API_KEY[-3:]
        st.markdown(f'<div class="success-box">✅ API Key Detectado: {masked_key}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="error-box">❌ API Key NO DETECTADO (Missing)</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("控制台")
        topic = st.text_input("Topic", "School")
        if st.button("🔴 强制生成 (Force Generate)"):
            with st.spinner("Connecting to Google Gemini..."):
                st.session_state.data = call_real_ai_debug(topic, "HSK1", "你好")
                st.session_state.audio = ""
                st.rerun()

    # 显示结果
    if "data" in st.session_state and st.session_state.data:
        # 如果有数据，生成音频
        if not st.session_state.get("audio"):
            fname = f"audio_{int(time.time())}.mp3"
            asyncio.run(make_audio(st.session_state.data, fname))
            st.session_state.audio = fname
        
        # 播放器
        if os.path.exists(st.session_state.audio):
            with open(st.session_state.audio, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<audio controls src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)

        # 课文显示
        st.markdown('<div class="reading-box">', unsafe_allow_html=True)
        for line in st.session_state.data:
            html = f'<div class="line-container"><div class="role">{line["r"]}</div><div>'
            for char, py in line["t"]:
                html += f'<ruby>{char}<rt>{py}</rt></ruby>'
            html += f'</div></div>'
            st.markdown(html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
