import streamlit as st
import asyncio
import edge_tts
import os
import time
import base64
import json
import random
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig

# --- 1. 核心配置 ---
st.set_page_config(page_title="Long Wen Reading Pro", page_icon="🐼", layout="wide", initial_sidebar_state="expanded")
MY_API_KEY = os.environ.get("GOOGLE_API_KEY") 
TARGET_MODEL = 'models/gemini-2.0-flash' 

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
        "instr": "✍️ Escribe aquí para practicar...", "gen_btn": "Generar Lección ✨", 
        "topic": "Tema", "level": "Nivel", "keywords": "Palabras", "lines": "Líneas (Exactas)",
        "unit": "Límite de Unidad (HSK 1)", "loading": "✨ Procesando lógica de la historia...",
        "show_py": "Mostrar Pinyin", "show_tr": "Mostrar Traducción", "refresh": "Regenerar Audio",
        "mode": "Modo", "dialogue": "Diálogo 🗣️", "story": "Historia 📖", "podcast": "Podcast 🎧",
        "dl_btn": "📥 Descargar Podcast (MP3)"
    },
    "English": { 
        "instr": "✍️ Type here to practice...", "gen_btn": "Generate Lesson ✨", 
        "topic": "Topic", "level": "Level", "keywords": "Keywords", "lines": "Lines (Exact)",
        "unit": "Unit Limit (HSK 1)", "loading": "✨ Processing story logic...",
        "show_py": "Show Pinyin", "show_tr": "Show Translation", "refresh": "Regenerate Audio",
        "mode": "Mode", "dialogue": "Dialogue 🗣️", "story": "Story 📖", "podcast": "Podcast 🎧",
        "dl_btn": "📥 Download Podcast (MP3)"
    }
}

# --- 2. 🎨 CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&family=Nunito:wght@700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FFFBF0 !important; font-family: 'Nunito', 'Noto Sans SC', sans-serif; overflow: hidden !important; height: 100vh !important; margin: 0; padding: 0; }
    .block-container { padding-top: 30px !important; padding-bottom: 0px !important; max-width: 100% !important; height: 100vh !important; overflow: hidden !important; }
    .main-title { text-align: center; color: #5D5650; font-weight: 800; font-size: 2rem; letter-spacing: 1px; margin-bottom: 20px; text-shadow: 2px 2px 0px #FFEaa7; }
    .scroll-container { background: #FFFFFF; border-radius: 25px; padding: 30px 40px; box-sizing: border-box; box-shadow: 0 8px 20px rgba(235, 212, 180, 0.4); border: 2px solid #FFF5E0; height: calc(100vh - 300px); overflow-y: auto !important; display: flex; flex-direction: column; gap: 15px; width: 90%; max-width: 800px; margin: 0 auto; }
    .scroll-container::-webkit-scrollbar { width: 8px; }
    .scroll-container::-webkit-scrollbar-thumb { background-color: #FFE5B4; border-radius: 10px; }
    .cute-row { display: flex; align-items: flex-start; padding: 15px; border-bottom: 2px dashed #FFF0D4; transition: all 0.3s ease; border-radius: 12px; }
    .cute-avatar { background-color: #FFD166; color: #fff; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; margin-right: 15px; flex-shrink: 0; box-shadow: 2px 2px 0px #F4B860; }
    .avatar-dawei { background-color: #6FCF97; box-shadow: 2px 2px 0px #27AE60; }
    .avatar-narrator { background-color: #B28DFF; box-shadow: 2px 2px 0px #8758FF; font-size: 16px;}
    .avatar-host { background-color: #FF6B6B; box-shadow: 2px 2px 0px #C92A2A; font-size: 16px;}
    .cute-chinese { flex: 1; display: flex; flex-wrap: wrap; gap: 2px; align-items: flex-end; }
    .story-chinese { line-height: 2.8; text-align: justify; }
    .story-sentence { border-radius: 8px; transition: background 0.3s ease; padding: 4px 2px; }
    .story-trans { margin-top: 40px; padding-top: 25px; border-top: 2px dashed #FFF0D4; color: #94A3B8; font-size: 1rem; line-height: 1.8; text-align: justify; }
    .story-trans-sentence { transition: color 0.3s ease, background-color 0.3s ease; border-radius: 6px; padding: 2px 4px; margin-right: 5px; }
    .podcast-card { background: linear-gradient(135deg, #FF9F1C 0%, #FFD166 100%); border-radius: 20px; padding: 20px; text-align: center; color: white; box-shadow: 0 10px 20px rgba(255, 159, 28, 0.3); margin-bottom: 20px; }
    
    ruby { font-size: 24px; font-weight: 700; color: #4A4A4A; ruby-position: under; line-height: 2.0; margin-right: 2px;}
    rt { font-size: 12px; color: #FF8BA7; font-weight: 600; font-family: sans-serif; }
    
    .oov-word { color: #D35400 !important; border-bottom: 2px dotted #D35400; cursor: help; position: relative;}
    .oov-star { color: #E74C3C; font-size: 14px; position: relative; top: -10px; margin-left: 2px;}
    
    .cute-trans { width: 35%; padding-left: 20px; color: #AAB7B8; font-size: 0.9rem; font-style: italic; border-left: 2px solid #F0F3F4; display: flex; align-items: center; line-height: 1.4; }
    audio::-webkit-media-controls-enclosure { border-radius: 20px; }
    audio::-internal-media-controls-overflow-button { display: none !important; }
    .speed-btn { background: #FFFBF0; border: 2px solid #FFE5B4; border-radius: 15px; padding: 5px 15px; cursor: pointer; color: #5D5650; font-weight: 700; font-size: 0.9rem; transition: all 0.2s; outline: none; }
    .speed-btn:hover { background: #FFEaa7; transform: translateY(-2px); }
    section[data-testid="stMain"] div[data-testid="stTextInput"] { margin: 20px auto 0 auto !important; width: 90% !important; max-width: 800px !important; box-sizing: border-box !important; background-color: #FFFFFF !important; padding: 5px 20px !important; border-radius: 50px !important; box-shadow: 0 10px 25px rgba(255, 159, 28, 0.2) !important; border: 3px solid #FFE5B4 !important; }
    section[data-testid="stMain"] div[data-testid="stTextInput"] input { border: none !important; background-color: transparent !important; font-size: 1.1rem !important; color: #5D5650 !important; box-shadow: none !important; padding: 10px !important; }
    .hide-pinyin rt { display: none !important; }
    .hide-trans .cute-trans, .hide-trans .story-trans { display: none !important; }
    .active-meimei { background-color: #FFF8E1 !important; border-radius: 12px; } .active-dawei { background-color: #E8F8F5 !important; border-radius: 12px; }
    .active-story { background-color: #F4EFFF !important; } .active-story-trans { color: #8758FF !important; background-color: #F4EFFF !important; font-weight: bold; } 
    .active-host { background-color: #FFF0F6 !important; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# --- 3. AI 逻辑 ---
def call_ai(topic, level, keywords, num_lines, unit_limit, mode_type, ui_lang):
    if not MY_API_KEY: return None
    try:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel(TARGET_MODEL)
        safety = {HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE}
        
        # 🚀 绝杀手段：直接启用 API 的原生 JSON 模式，彻底杜绝丢逗号、格式写错等低级错误！
        gen_config = GenerationConfig(
            temperature=0.8,
            response_mime_type="application/json" 
        )

        allowed_vocab = []
        if level == "HSK 1":
            for i in range(1, unit_limit + 1): allowed_vocab.extend(HSK1_VOCAB.get(i, []))
        
        vocab_instruction = f"""
        VOCABULARY RULE: Primarily use Chinese words from this list: [{', '.join(allowed_vocab)}]. 
        NATURALNESS EXCEPTION (OOV): To make the dialogue flow naturally, you are allowed to use a MAXIMUM of 3 Out-Of-Vocabulary (OOV) words (e.g., 绿茶, 红茶, 手机).
        """ if allowed_vocab else ""
            
        if not topic:
            topics_pool = ["去饭店吃饭点菜", "打车去医院看朋友", "下雨天在家喝茶看电影", "计划明天去买漂亮衣服"]
            topic_instruction = f"Topic: '{random.choice(topics_pool)}'."
        else:
            topic_instruction = f"Topic: {topic}."

        common_rules = f"""
        CRITICAL FORMAT & QUALITY RULES:
        1. YOU MUST OUTPUT A VALID JSON ARRAY OF OBJECTS. NO markdown blocks.
        2. ARRAY FORMAT: The 't' array MUST contain nested lists. DO NOT output flat strings.
           - Standard word: ["word", "pinyin"]
           - Punctuation: ["punc", ""]
           - OOV Word (Out-of-vocabulary): MUST format as a 3-item list ["word", "pinyin", "Translation in {ui_lang}"].
        3. EXACT LENGTH: Generate EXACTLY {num_lines} objects.
        4. NO ROBOTIC REPETITION: Do NOT repeat the same sentence patterns. Omit verbs/nouns that were just said.
        5. OUTPUT JSON ARRAY ONLY! EXACT KEYS: "r", "t", "tr_es", "tr_en".
        """

        if mode_type == "story":
            prompt = f"""
            {topic_instruction} Level: {level}. 
            Create a descriptive Chinese STORY. EXACTLY {num_lines} sentences.
            - "r" MUST always be "旁白" (Narrator).
            - ABSOLUTELY NO DIALOGUE! Do NOT use A/B format. Write pure narrative prose.
            {vocab_instruction} {common_rules}
            """
        elif mode_type == "podcast":
            school_es, school_en = "Escuela de chino Long Wen", "Long Wen Chinese School"
            intro_text = f"Hello everyone! Welcome to the {school_en} podcast. Let's start!" if ui_lang == "English" else f"¡Hola a todos! Bienvenidos al podcast de la {school_es}. ¡Empecemos!"
            outro_text = f"That's all for today! Thanks for listening to {school_en}!" if ui_lang == "English" else f"¡Eso es todo por hoy! ¡Gracias por escuchar a {school_es}!"
            
            prompt = f"""
            {topic_instruction} Level: {level}. Professional PODCAST. EXACTLY {num_lines} lines.
            - Line 1: "r" is "主持人". Text in {ui_lang}. Example: "t": [["{intro_text}", ""]]
            - Middle Lines: Dialogue between "美美" and "大卫". USE NATURAL OMISSIONS.
            - Line {num_lines}: "r" is "主持人". Text in {ui_lang}. Example: "t": [["{outro_text}", ""]]
            {vocab_instruction} {common_rules}
            """
        else: # dialogue
            prompt = f"{topic_instruction} Level: {level}. Conversation between '美美' and '大卫'. EXACTLY {num_lines} lines. NO REPETITION of full sentences. {vocab_instruction} {common_rules}"

        response = model.generate_content(prompt, safety_settings=safety, generation_config=gen_config)
        
        # 既然开启了 json mode，出来的文本 100% 是 json
        raw_text = response.text.strip()
        return json.loads(raw_text)
            
    except Exception as e:
        st.error(f"AI Generation Error: {str(e)}")
        return None

# --- 4. 音频 ---
async def make_audio(data, filename, ui_lang):
    ts = []
    curr = 0.0
    with open(filename, 'wb') as final_file:
        for i, line in enumerate(data):
            role_raw = str(line.get("r", "美美"))
            role = re.sub(r'[^\w]', '', role_raw)
            
            if "大卫" in role: voice = "zh-CN-YunxiNeural"
            elif "主持人" in role: voice = ("es-ES-AbrilNeural" if ui_lang == "Español" else "en-US-AvaNeural")
            elif "旁白" in role: voice = "zh-CN-XiaoyiNeural"
            else: voice = "zh-CN-XiaoxiaoNeural" 

            raw = "".join([str(item[0]) if isinstance(item, list) else str(item) for item in line.get("t", [])])
            
            if not raw.strip() and "主持人" in role:
                raw = "¡Bienvenidos!" if ui_lang == "Español" else "Welcome!"
            if not raw: continue
            
            raw_tts = re.sub(r'[^\w\s\u4e00-\u9fa5，。？！.,!?¡¿\']', '', raw)
            dur = len(raw) * (0.07 if "主持人" in role else 0.25) + 0.5 
            
            ts.append({"start": curr, "end": curr + dur, "role": role})
            try:
                comm = edge_tts.Communicate(raw_tts, voice)
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
    is_podcast = "true" if mode_type == "podcast" else "false"
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
        const p = document.getElementById('p'); const bgm = document.getElementById('bgm'); const ts = {json.dumps(ts)};
        if ({is_podcast} && bgm) {{ bgm.volume = 0.12; p.addEventListener('play', () => bgm.play()); p.addEventListener('pause', () => bgm.pause()); }}
        p.ontimeupdate = () => {{
            const cur = p.currentTime;
            ts.forEach((t, i) => {{
                const el = window.parent.document.getElementById('row-'+i);
                if (el) {{
                    if (cur >= t.start && cur < t.end) {{
                        el.classList.add(t.role.includes("大卫") ? "active-dawei" : (t.role.includes("主持人") ? "active-host" : (t.role.includes("旁白") ? "active-story" : "active-meimei")));
                        el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }} else {{
                        el.classList.remove("active-meimei", "active-dawei", "active-host", "active-story");
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
        ui_lang = st.selectbox("Language", ["Español", "English"])
        ui = UI_TEXT[ui_lang]
        mode_label = st.radio(ui["mode"], [ui["dialogue"], ui["story"], ui["podcast"]], horizontal=True)
        mode_type = "story" if mode_label == ui["story"] else ("podcast" if mode_label == ui["podcast"] else "dialogue")
        topic, level = st.text_input(ui["topic"], ""), st.selectbox(ui["level"], ["HSK 1", "HSK 2", "HSK 3"])
        unit_limit = st.slider(ui["unit"], 1, 15, 15) if level == "HSK 1" else 15
        keys, num_lines = st.text_input(ui["keywords"], ""), st.slider(ui["lines"], 4, 24, 12, 2)
        if st.button(ui["gen_btn"]):
            with st.spinner(ui["loading"]):
                res = call_ai(topic, level, keys, num_lines, unit_limit, mode_type, ui_lang)
                if res: st.session_state.current_data, st.session_state.audio_file, st.session_state.rendered_mode = res, "", mode_type; st.rerun()
        st.divider()
        show_pinyin, show_trans = st.toggle(ui["show_py"], value=True), st.toggle(ui["show_tr"], value=True)
        if st.button(f"🔄 {ui['refresh']}"): st.session_state.audio_file = ""; st.rerun()

    st.markdown('<div class="main-title">Long Wen Reading Assistant Pro</div>', unsafe_allow_html=True)
    if st.session_state.current_data:
        curr_mode = st.session_state.get("rendered_mode", mode_type)
        if not st.session_state.audio_file:
            fname = f"audio_{int(time.time())}.mp3"
            st.session_state.ts = asyncio.run(make_audio(st.session_state.current_data, fname, ui_lang))
            st.session_state.audio_file = fname
        if curr_mode == "podcast": st.markdown('<div class="podcast-card"><p class="podcast-title">🎙️ 中文学习播客 (Chinese Learning Podcast)</p></div>', unsafe_allow_html=True)
        if os.path.exists(st.session_state.audio_file):
            st.components.v1.html(get_player_html(st.session_state.audio_file, st.session_state.ts, curr_mode), height=100)
            if curr_mode == "podcast":
                with open(st.session_state.audio_file, "rb") as f: st.download_button(ui["dl_btn"], f, "podcast.mp3", "audio/mpeg")

        container_class = f"scroll-container {'hide-pinyin' if not show_pinyin else ''} {'hide-trans' if not show_trans else ''}"
        html_str = f'<div class="{container_class}">'
        if curr_mode == "story":
            ch_h, tr_h = '<div class="story-chinese">', '<div class="story-trans">'
            for idx, line in enumerate(st.session_state.current_data):
                trans = (line.get("tr_es", "") if ui_lang == "Español" else line.get("tr_en", ""))
                hanzi = ""
                for it in line.get("t", []):
                    if isinstance(it, list):
                        c = str(it[0]) if len(it) > 0 else ""
                        p = str(it[1]) if len(it) > 1 else ""
                        if len(it) > 2 and it[2]:
                            oov_trans = str(it[2])
                            hanzi += f'<ruby class="oov-word" title="超纲: {oov_trans}">{c}<span class="oov-star">*</span><rt>{p}</rt></ruby>'
                        else:
                            hanzi += f'<ruby>{c}<rt>{p}</rt></ruby>'
                    else:
                        hanzi += f'<ruby>{it}<rt></rt></ruby>'
                
                ch_h += f'<span class="story-sentence" id="row-{idx}">{hanzi}</span> '
                tr_h += f'<span class="story-trans-sentence" id="trans-{idx}">{idx+1}. {trans} </span>'
            html_str += f"{ch_h}</div>{tr_h}</div></div>"
        else:
            for idx, line in enumerate(st.session_state.current_data):
                role, trans = str(line.get("r", "美美")), (line.get("tr_es", "") if ui_lang == "Español" else line.get("tr_en", ""))
                avatar = "avatar-dawei" if "大卫" in role else ("avatar-host" if "主持人" in role else ("avatar-narrator" if "旁白" in role else ""))
                char = "🎧" if "主持人" in role else (role[0] if len(role)>0 else "美")
                
                hanzi = ""
                for it in line.get("t", []):
                    if isinstance(it, list):
                        c = str(it[0]) if len(it) > 0 else ""
                        p = str(it[1]) if len(it) > 1 else ""
                        if len(it) > 2 and it[2]:
                            oov_trans = str(it[2])
                            hanzi += f'<ruby class="oov-word" title="超纲 (OOV): {oov_trans}">{c}<span class="oov-star">*</span><rt>{p}</rt></ruby>'
                        else:
                            hanzi += f'<ruby>{c}<rt>{p}</rt></ruby>'
                    else:
                        hanzi += f'<ruby>{it}<rt></rt></ruby>'
                
                html_str += f'<div class="cute-row" id="row-{idx}"><div class="cute-avatar {avatar}">{char}</div><div class="cute-chinese">{hanzi}</div><div class="cute-trans">{trans}</div></div>'
        st.markdown(html_str + '</div>', unsafe_allow_html=True)
        st.text_input("practice", key="practice_input", label_visibility="collapsed", placeholder=ui["instr"])
    else: st.info("👈 Please enter settings and click Generate")

if __name__ == "__main__": main()
