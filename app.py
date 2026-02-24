import streamlit as st
import asyncio
import edge_tts
import os
import time
import base64
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig

# --- 1. 核心配置 ---
st.set_page_config(page_title="Long Wen Reading Pro", page_icon="🐼", layout="wide", initial_sidebar_state="expanded")
MY_API_KEY = os.environ.get("GOOGLE_API_KEY")
TARGET_MODEL = 'models/gemini-2.5-flash'

# 📚 HSK 1 官方标准教材词汇表
HSK1_VOCAB = {
    1: ["我", "你", "他", "她", "您", "们", "好", "再见"],
    2: ["谢谢", "不客气", "对不起", "没关系", "不"],
    3: ["叫", "什么", "名字", "是", "老师", "吗", "学生", "人", "中国", "美国", "西班牙"],
    4: ["谁", "的", "汉语", "语", "哪", "国", "呢", "同学", "朋友", "也"],
    5: ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "家", "有", "口", "女儿", "几", "岁", "了", "今年", "多", "大", "两", "猫", "狗"],
    6: ["会", "说", "妈妈", "菜", "很", "好吃", "做", "写", "汉字", "字", "怎么", "读"],
    7: ["请", "问", "今天", "号", "月", "星期", "昨天", "明天", "去", "学校", "看", "书"],
    8: ["想", "喝", "茶", "吃", "米饭", "下午", "商店", "买", "个", "杯子", "这", "多少", "钱", "那", "块"],
    9: ["小", "在", "那儿", "椅子", "下面", "哪儿", "工作", "儿子", "医院", "医生", "爸爸"],
    10: ["桌子", "上", "电脑", "和", "本", "里", "前面", "后面", "没有", "能", "坐", "这儿"],
    11: ["现在", "点", "分", "中午", "吃饭", "时候", "回", "电影", "住", "前", "北京"],
    12: ["天气", "怎么样", "太", "热", "冷", "下雨", "下", "雨", "小姐", "来", "身体", "爱", "些", "水果", "水"],
    13: ["喂", "也", "学习", "上午", "睡觉", "电视", "喜欢", "给", "打电话", "吧"],
    14: ["东西", "一点儿", "苹果", "看见", "先生", "开", "车", "开车", "回来", "分钟", "后", "衣服", "漂亮", "啊", "少", "不少", "都"],
    15: ["认识", "年", "大学", "饭店", "出租车", "一起", "高兴", "听", "飞机"]
}

UI_TEXT = {
    "Español": { 
        "instr": "✍️ Escribe aquí para practicar...", 
        "gen_btn": "Generar Lección ✨", 
        "topic": "Tema", "level": "Nivel", "keywords": "Palabras",
        "lines": "Líneas (Longitud)",
        "unit": "Límite de Unidad (HSK 1)",
        "loading": "✨ Creando magia...",
        "show_py": "Mostrar Pinyin", 
        "show_tr": "Mostrar Traducción",
        "refresh": "Regenerar Audio",
        "mode": "Modo", "dialogue": "Diálogo 🗣️", "story": "Historia 📖", "podcast": "Podcast 🎧",
        "dl_btn": "📥 Descargar Podcast (MP3)"
    },
    "English": { 
        "instr": "✍️ Type here to practice...", 
        "gen_btn": "Generate Lesson ✨", 
        "topic": "Topic", "level": "Level", "keywords": "Keywords",
        "lines": "Lines (Length)",
        "unit": "Unit Limit (HSK 1)",
        "loading": "✨ Creating magic...",
        "show_py": "Show Pinyin", 
        "show_tr": "Show Translation",
        "refresh": "Regenerate Audio",
        "mode": "Mode", "dialogue": "Dialogue 🗣️", "story": "Story 📖", "podcast": "Podcast 🎧",
        "dl_btn": "📥 Download Podcast (MP3)"
    }
}

# --- 2. 🎨 CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&family=Nunito:wght@700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFBF0 !important; font-family: 'Nunito', 'Noto Sans SC', sans-serif;
        overflow: hidden !important; height: 100vh !important; margin: 0; padding: 0;
    }
    
    .block-container { padding-top: 30px !important; padding-bottom: 0px !important; max-width: 100% !important; height: 100vh !important; overflow: hidden !important; }
    .main-title { text-align: center; color: #5D5650; font-weight: 800; font-size: 2rem; letter-spacing: 1px; margin-bottom: 20px; text-shadow: 2px 2px 0px #FFEaa7; }

    .scroll-container {
        background: #FFFFFF; border-radius: 25px; padding: 30px 40px; box-sizing: border-box; 
        box-shadow: 0 8px 20px rgba(235, 212, 180, 0.4); border: 2px solid #FFF5E0;
        height: calc(100vh - 300px); overflow-y: auto !important; 
        display: flex; flex-direction: column; gap: 15px; width: 90%; max-width: 800px; margin: 0 auto;
    }
    .scroll-container::-webkit-scrollbar { width: 8px; }
    .scroll-container::-webkit-scrollbar-track { background: transparent; }
    .scroll-container::-webkit-scrollbar-thumb { background-color: #FFE5B4; border-radius: 10px; }

    .cute-row { display: flex; align-items: flex-start; padding: 15px; border-bottom: 2px dashed #FFF0D4; transition: all 0.3s ease; border-radius: 12px; }
    .cute-avatar {
        background-color: #FFD166; color: #fff; width: 40px; height: 40px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; margin-right: 15px; flex-shrink: 0; box-shadow: 2px 2px 0px #F4B860;
    }
    .avatar-dawei { background-color: #6FCF97; box-shadow: 2px 2px 0px #27AE60; }
    .avatar-narrator { background-color: #B28DFF; box-shadow: 2px 2px 0px #8758FF; font-size: 16px;}
    .cute-chinese { flex: 1; display: flex; flex-wrap: wrap; gap: 2px; align-items: flex-end; }
    
    .story-content { padding: 10px 0; }
    .story-chinese { line-height: 2.8; text-align: justify; }
    .story-sentence { border-radius: 8px; transition: background 0.3s ease; padding: 4px 2px; }
    .story-trans { margin-top: 40px; padding-top: 25px; border-top: 2px dashed #FFF0D4; color: #94A3B8; font-size: 1rem; line-height: 1.8; text-align: justify; }
    .story-trans-sentence { transition: color 0.3s ease, background-color 0.3s ease; border-radius: 6px; padding: 2px 4px; margin-right: 5px; }

    .podcast-card {
        background: linear-gradient(135deg, #FF9F1C 0%, #FFD166 100%);
        border-radius: 20px; padding: 20px; text-align: center; color: white;
        box-shadow: 0 10px 20px rgba(255, 159, 28, 0.3); margin-bottom: 20px;
    }
    .podcast-title { font-size: 1.6rem; font-weight: 800; margin: 0; letter-spacing: 1px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .podcast-subtitle { font-size: 0.9rem; opacity: 0.9; margin: 5px 0 0 0; }

    ruby { font-size: 24px; font-weight: 700; color: #4A4A4A; ruby-position: under; line-height: 2.0; margin-right: 2px;}
    rt { font-size: 12px; color: #FF8BA7; font-weight: 600; font-family: sans-serif; }
    .cute-trans { width: 35%; padding-left: 20px; color: #AAB7B8; font-size: 0.9rem; font-style: italic; border-left: 2px solid #F0F3F4; display: flex; align-items: center; line-height: 1.4; }

    audio::-webkit-media-controls-enclosure { border-radius: 20px; }
    audio::-internal-media-controls-overflow-button { display: none !important; }
    .speed-btn { background: #FFFBF0; border: 2px solid #FFE5B4; border-radius: 15px; padding: 5px 15px; cursor: pointer; color: #5D5650; font-weight: 700; font-size: 0.9rem; transition: all 0.2s; outline: none; }
    .speed-btn:hover { background: #FFEaa7; transform: translateY(-2px); }

    section[data-testid="stMain"] div[data-testid="stTextInput"] {
        margin: 20px auto 0 auto !important; width: 90% !important; max-width: 800px !important; box-sizing: border-box !important; background-color: #FFFFFF !important; padding: 5px 20px !important; border-radius: 50px !important; box-shadow: 0 10px 25px rgba(255, 159, 28, 0.2) !important; border: 3px solid #FFE5B4 !important;
    }
    section[data-testid="stMain"] div[data-testid="stTextInput"] input { border: none !important; background-color: transparent !important; font-size: 1.1rem !important; color: #5D5650 !important; box-shadow: none !important; padding: 10px !important; }
    section[data-testid="stMain"] div[data-testid="stTextInput"]:focus-within { border-color: #FFD166 !important; box-shadow: 0 10px 30px rgba(255, 159, 28, 0.3) !important; transform: translateY(-2px) !important; transition: all 0.3s ease; }
    section[data-testid="stMain"] div[data-testid="stTextInput"] label { display: none !important; }

    .hide-pinyin rt { display: none !important; }
    .hide-trans .cute-trans, .hide-trans .story-trans { display: none !important; }
    .active-meimei { background-color: #FFF8E1 !important; border-radius: 12px; transition: background 0.2s; } 
    .active-dawei { background-color: #E8F8F5 !important; border-radius: 12px; transition: background 0.2s; }
    .active-story { background-color: #F4EFFF !important; } 
    .active-story-trans { color: #8758FF !important; background-color: #F4EFFF !important; font-weight: bold; } 
</style>
""", unsafe_allow_html=True)

# --- 3. AI 逻辑 ---
def call_ai(topic, level, keywords, num_lines, unit_limit, mode_type):
    if not MY_API_KEY: return None
    try:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel(TARGET_MODEL)
        safety = {HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE}
        gen_config = GenerationConfig(temperature=0.75)

        allowed_vocab = []
        if level == "HSK 1":
            for i in range(1, unit_limit + 1):
                allowed_vocab.extend(HSK1_VOCAB.get(i, []))
        
        vocab_instruction = ""
        if allowed_vocab:
            vocab_str = ", ".join(allowed_vocab)
            vocab_instruction = f"""
            STRICT VOCABULARY LIMIT: You MUST ONLY use Chinese words from this list: [{vocab_str}]. 
            You may also use the user-provided keywords: [{keywords}]. DO NOT use any other words.
            """
            
        # 🌟 核心升级 1：动态场景分配！如果用户没给主题，强行根据滑块分配高级主题！
        if not topic:
            if unit_limit >= 14:
                topic_instruction = "Topic: You MUST write about taking a taxi, taking an airplane, eating at a hotel/restaurant (饭店), or university life."
            elif unit_limit >= 11:
                topic_instruction = "Topic: You MUST write about the weather (raining, hot/cold), watching a movie, or seeing a doctor at the hospital."
            elif unit_limit >= 8:
                topic_instruction = "Topic: You MUST write about shopping for clothes/things, or drinking tea in the afternoon."
            else:
                topic_instruction = "Topic: A specific and interesting daily life scenario."
        else:
            topic_instruction = f"Topic: {topic}."

        # 🌟 核心升级 2：严打废话，强制使用高级词汇
        common_rules = f"""
        CRITICAL CONTENT & QUALITY RULES:
        1. MAXIMIZE ADVANCED VOCABULARY: You MUST heavily use the most advanced words from the allowed list! Do NOT just repeat basic words like "我, 你, 好, 学校".
        2. NO FILLER GREETINGS: Do NOT waste lines on boring greetings like "你好", "你呢", "谢谢", "很高兴认识你". Jump immediately into a rich, detailed plot or specific discussion!
        3. NATURAL FLOW WITHOUT CHINGLISH: The text MUST be perfectly native. If you don't have the exact grammar word (e.g., missing "要" for time duration), break it into natural, shorter sentences (e.g. "我们坐出租车去饭店。二十分钟。").
        4. QUANTITY RULE: Use "两" (liǎng) for quantities/time (e.g., "两点"). NEVER use "二点".
        5. YOU MUST INCLUDE PUNCTUATION (，。？！).
        6. OUTPUT JSON ARRAY ONLY! EXACT KEYS: "r", "t", "tr_es", "tr_en".
        """

        if mode_type == "story":
            prompt = f"""
            {topic_instruction} Level: {level}. Keywords: {keywords}.
            {common_rules}
            ADDITIONAL STORY RULES:
            - The text MUST be exactly {num_lines} sentences.
            - ALL lines MUST use the exact role name "旁白" (Narrator).
            {vocab_instruction}
            MANDATORY FORMAT: [{{"r": "旁白", "t": [["这", "zhè"], ["是", "shì"], ["。", ""]], "tr_es": "Esto es.", "tr_en": "This is."}}]
            """
        elif mode_type == "podcast":
            prompt = f"""
            {topic_instruction} Level: {level}. Keywords: {keywords}.
            {common_rules}
            ADDITIONAL PODCAST RULES:
            - The text MUST be exactly {num_lines} lines long.
            - Create an engaging PODCAST hosted by '美美' and '大卫'.
            - The first 1 line MUST be a quick intro. The last line MUST be an outro (e.g., "谢谢大家，再见！").
            - The middle lines MUST have high information density. Disagree with each other or discuss specific details.
            {vocab_instruction}
            MANDATORY FORMAT: [{{"r": "美美", "t": [["大", "dà"], ["家", "jiā"], ["好", "hǎo"], ["！", ""]], "tr_es": "¡Hola a todos!", "tr_en": "Hello everyone!"}}]
            """
        else: # dialogue
            prompt = f"""
            {topic_instruction} Level: {level}. Keywords: {keywords}.
            {common_rules}
            ADDITIONAL DIALOGUE RULES:
            - Dialogue MUST be exactly {num_lines} lines long.
            - Create a dense, engaging conversation between '美美' and '大卫'.
            {vocab_instruction}
            MANDATORY FORMAT: [{{"r": "美美", "t": [["你", "nǐ"], ["好", "hǎo"], ["！", ""]], "tr_es": "¡Hola!", "tr_en": "Hello!"}}]
            """

        response = model.generate_content(prompt, safety_settings=safety, generation_config=gen_config)
        text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)
    except Exception as e:
        st.error(f"AI Generation Error: {str(e)}")
        return None

# --- 4. 音频 ---
async def make_audio(data, filename):
    ts = []
    curr = 0.0
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(data):
            role = line.get("r", "美美") 
            if role == "大卫": voice = "zh-CN-YunxiNeural"
            elif role == "美美": voice = "zh-CN-XiaoxiaoNeural"
            else: voice = "zh-CN-XiaoyiNeural" 

            raw = "".join([p[0] for p in line.get("t", [])])
            dur = len(raw) * 0.25 + 0.35 
            ts.append({"start": curr, "end": curr + dur, "role": role})
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
def get_player_html(file_path, ts, mode_type):
    with open(file_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    is_podcast_str = "true" if mode_type == "podcast" else "false"
    is_story_str = "true" if mode_type == "story" else "false"
    
    return f"""
    <div style="width:100%; display:flex; flex-direction:column; align-items:center; margin-bottom:20px; position:relative; z-index:50;">
        <audio id="p" controls src="data:audio/mp3;base64,{b64}" style="width:100%; max-width:400px; outline:none; margin-bottom:10px;"></audio>
        <audio id="bgm" src="https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3" preload="auto" loop></audio>
        <div style="display:flex; gap:10px;">
            <button class="speed-btn" onclick="document.getElementById('p').playbackRate=0.8">🐢 0.8x</button>
            <button class="speed-btn" onclick="document.getElementById('p').playbackRate=1.0">▶ 1.0x</button>
            <button class="speed-btn" onclick="document.getElementById('p').playbackRate=1.2">🐇 1.2x</button>
        </div>
    </div>
    <script>
        const p = document.getElementById('p');
        const bgm = document.getElementById('bgm');
        const ts = {json.dumps(ts)};
        const isStoryMode = {is_story_str};
        const isPodcastMode = {is_podcast_str};
        
        if (isPodcastMode && bgm) {{
            bgm.volume = 0.12;
            p.addEventListener('play', () => bgm.play().catch(e => console.log('BGM wait')));
            p.addEventListener('pause', () => bgm.pause());
            p.addEventListener('ended', () => bgm.pause());
        }}
        
        p.ontimeupdate = () => {{
            const cur = p.currentTime;
            ts.forEach((t, i) => {{
                const el = window.parent.document.getElementById('row-'+i);
                const transEl = window.parent.document.getElementById('trans-'+i);
                if (el) {{
                    if (cur >= t.start && cur < t.end) {{
                        if (isStoryMode) {{
                            el.classList.add("active-story");
                            if (transEl) transEl.classList.add("active-story-trans");
                        }} else {{
                            el.classList.remove("active-meimei", "active-dawei");
                            if (t.role === "大卫") el.classList.add("active-dawei");
                            else el.classList.add("active-meimei"); 
                        }}
                        el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }} else {{
                        if (isStoryMode) {{
                            el.classList.remove("active-story");
                            if (transEl) transEl.classList.remove("active-story-trans");
                        }} else {{
                            el.classList.remove("active-meimei", "active-dawei");
                        }}
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
        
        selected_mode_label = st.radio(ui["mode"], [ui["dialogue"], ui["story"], ui["podcast"]], horizontal=True)
        if selected_mode_label == ui["story"]: mode_type = "story"
        elif selected_mode_label == ui["podcast"]: mode_type = "podcast"
        else: mode_type = "dialogue"

        topic = st.text_input(ui["topic"], "") 
        level = st.selectbox(ui["level"], ["HSK 1", "HSK 2", "HSK 3"])
        
        unit_limit = 15
        if level == "HSK 1": unit_limit = st.slider(ui["unit"], min_value=1, max_value=15, value=15)
            
        keys = st.text_input(ui["keywords"], "") 
        num_lines = st.slider(ui["lines"], min_value=4, max_value=12, value=10, step=1)
        
        if st.button(ui["gen_btn"]):
            with st.spinner(ui["loading"]):
                res = call_ai(topic, level, keys, num_lines, unit_limit, mode_type)
                if res:
                    st.session_state.current_data = res
                    st.session_state.audio_file = ""
                    st.session_state.rendered_mode = mode_type 
                    st.rerun()
        
        st.divider()
        show_pinyin = st.toggle(ui["show_py"], value=True)
        show_trans = st.toggle(ui["show_tr"], value=True)
        if st.button(f"🔄 {ui['refresh']}"):
            st.session_state.audio_file = ""
            st.rerun()

    st.markdown('<div class="main-title">Reading Assistant Pro</div>', unsafe_allow_html=True)

    if st.session_state.current_data:
        current_view_mode = st.session_state.get("rendered_mode", mode_type)
        
        if not st.session_state.audio_file:
            fname = f"audio_{int(time.time())}.mp3"
            st.session_state.ts = asyncio.run(make_audio(st.session_state.current_data, fname))
            st.session_state.audio_file = fname
        
        if current_view_mode == "podcast":
            st.markdown('<div class="podcast-card"><p class="podcast-title">🎙️ 中文学习播客 (Chinese Learning Podcast)</p><p class="podcast-subtitle">Escucha y aprende</p></div>', unsafe_allow_html=True)
            
        if os.path.exists(st.session_state.audio_file):
            st.components.v1.html(get_player_html(st.session_state.audio_file, st.session_state.ts, current_view_mode), height=100)
            
            if current_view_mode == "podcast":
                with open(st.session_state.audio_file, "rb") as file:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.download_button(label=ui["dl_btn"], data=file, file_name="chinese_podcast.mp3", mime="audio/mpeg", use_container_width=True)

        container_class = "scroll-container"
        if not show_pinyin: container_class += " hide-pinyin"
        if not show_trans: container_class += " hide-trans"

        html_str = f'<div class="{container_class}">'
        
        if current_view_mode == "story":
            html_str += '<div class="story-content"><div class="story-chinese">'
            trans_html = '<div class="story-trans">'
            for idx, line in enumerate(st.session_state.current_data):
                trans = line.get("tr_es", "") if ui_lang == "Español" else line.get("tr_en", "")
                hanzi_html = "".join([f'<ruby>{char}<rt>{py}</rt></ruby>' for char, py in line.get("t", [])])
                html_str += f'<span class="story-sentence" id="row-{idx}">{hanzi_html}</span> '
                trans_html += f'<span class="story-trans-sentence" id="trans-{idx}">{idx+1}. {trans} </span>'
            html_str += f'</div>{trans_html}</div></div>'
            
        else:
            for idx, line in enumerate(st.session_state.current_data):
                role = line.get("r", "美美")
                trans = line.get("tr_es", "") if ui_lang == "Español" else line.get("tr_en", "")
                
                if role == "大卫":
                    avatar_class = "cute-avatar avatar-dawei"
                    avatar_char = "大"
                elif role == "美美":
                    avatar_class = "cute-avatar"
                    avatar_char = "美"
                else: 
                    avatar_class = "cute-avatar avatar-narrator"
                    avatar_char = "🎙️" if current_view_mode == "podcast" else "📖"

                hanzi_html = "".join([f'<ruby>{char}<rt>{py}</rt></ruby>' for char, py in line.get("t", [])])
                html_str += f'<div class="cute-row" id="row-{idx}"><div class="{avatar_class}">{avatar_char}</div><div class="cute-chinese">{hanzi_html}</div><div class="cute-trans">{trans}</div></div>'
        
        html_str += '</div>'
        st.markdown(html_str, unsafe_allow_html=True)
        st.text_input("practice_input", label_visibility="collapsed", placeholder=ui["instr"])

    else:
        st.info("👈 Please enter settings and click Generate")

if __name__ == "__main__":
    main()
