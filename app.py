import streamlit as st
import asyncio
import edge_tts
import os
import streamlit.components.v1 as components

# --- 1. 页面基本设置 ---
st.set_page_config(
    page_title="互动阅读智能体 Pro", 
    page_icon="📖", 
    layout="centered"
)

# --- 2. 嵌入你完整的 HTML 源代码 ---
# 这里已经装载了你发给我的精美 de.html 全部逻辑
GRAMMAR_HTML_DE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>互动语法讲堂：的 (De) - High Contrast</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;700;900&family=Noto+Sans+SC:wght@400;700;900&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        'serif-sc': ['"Noto Serif SC"', 'serif'],
                        'sans-sc': ['"Noto Sans SC"', 'sans-serif'],
                        'mono': ['"Fira Code"', 'monospace'],
                    },
                    colors: {
                        'cream': '#FFFBF0', 'soft-pink': '#FF9A9E', 'soft-teal': '#4ECDC4', 
                        'soft-orange': '#FAB1A0', 'soft-blue': '#74B9FF', 'soft-purple': '#A29BFE',
                        'deep-pink': '#BE185D', 'deep-teal': '#0F766E', 'deep-orange': '#C2410C', 
                        'deep-blue': '#1D4ED8', 'deep-purple': '#7E22CE',
                    },
                    animation: {
                        'blob': 'blob 10s infinite', 'pop-in': 'popIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
                        'bounce-sm': 'bounceSm 2s infinite', 'wiggle': 'wiggle 1s ease-in-out infinite',
                    },
                    keyframes: {
                        blob: { '0%': { transform: 'translate(0px, 0px) scale(1)' }, '33%': { transform: 'translate(30px, -50px) scale(1.1)' }, '66%': { transform: 'translate(-20px, 20px) scale(0.9)' }, '100%': { transform: 'translate(0px, 0px) scale(1)' } },
                        popIn: { '0%': { opacity: '0', transform: 'scale(0.8)' }, '100%': { opacity: '1', transform: 'scale(1)' } },
                        bounceSm: { '0%, 100%': { transform: 'translateY(-5%)' }, '50%': { transform: 'translateY(0)' } },
                        wiggle: { '0%, 100%': { transform: 'rotate(-3deg)' }, '50%': { transform: 'rotate(3deg)' } }
                    }
                }
            }
        }
    </script>
    <style>
        @media (min-width: 768px) { body { height: 100vh; overflow: hidden; } #root { height: 100%; } }
        @media (max-width: 767px) { body { height: auto; min-height: 100vh; overflow-y: auto; } #root { height: auto; min-height: 100vh; } }
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
</head>
<body class="bg-cream font-sans-sc">
    <div id="root"></div>
    <script type="text/babel">
        const { useState, useEffect, useRef } = React;
        const ConfettiCanvas = ({ active }) => {
            const canvasRef = useRef(null);
            useEffect(() => {
                if (!active) return;
                const canvas = canvasRef.current;
                const ctx = canvas.getContext('2d');
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
                const particles = [];
                const colors = ['#BE185D', '#0F766E', '#C2410C', '#7E22CE'];
                for(let i=0; i<100; i++) {
                    particles.push({ x: canvas.width/2, y: canvas.height/2, vx: (Math.random()-0.5)*15, vy: (Math.random()-0.5)*15, color: colors[Math.floor(Math.random() * colors.length)], size: Math.random()*8+4 });
                }
                let animationId;
                const render = () => {
                    ctx.clearRect(0,0,canvas.width,canvas.height);
                    particles.forEach((p,i) => { p.x+=p.vx; p.y+=p.vy; p.vy+=0.5; p.size*=0.96; ctx.fillStyle=p.color; ctx.fillRect(p.x,p.y,p.size,p.size); if(p.size<0.5) particles.splice(i,1); });
                    if(particles.length>0) animationId = requestAnimationFrame(render);
                };
                render();
                return () => cancelAnimationFrame(animationId);
            }, [active]);
            return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-50" />;
        };
        const Icon = ({ path, className }) => ( <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className={className}>{path}</svg> );
        const Icons = {
            ArrowLeft: (props) => <Icon {...props} path={<path d="M19 12H5M12 19l-7-7 7-7"/>} />,
            ArrowRight: (props) => <Icon {...props} path={<path d="M5 12h14M12 5l7 7-7 7"/>} />,
            RefreshCw: (props) => <Icon {...props} path={<><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 21h5v-5"/></>} />,
            Star: (props) => <Icon {...props} path={<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>} />,
            BookOpen: (props) => <Icon {...props} path={<><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></>} />,
            Magic: (props) => <Icon {...props} path={<><path d="m2 9 3-3 3 3"/><path d="M13 2L2 13"/><path d="m11 13 3 3"/><path d="m16 9 3 3"/><path d="M16 22l6-11"/><path d="m22 2-3 3"/></>} />,
            ChevronRight: (props) => <Icon {...props} path={<path d="m9 18 6-6-6-6"/>} />,
        };
        function LessonPreview() {
            const [currentSlide, setCurrentSlide] = useState(0);
            const [conceptStep, setConceptStep] = useState(0);
            const [revealedRows, setRevealedRows] = useState({});
            const [triggerConfetti, setTriggerConfetti] = useState(false);
            const toggleRow = (index) => setRevealedRows(prev => ({ ...prev, [index]: !prev[index] }));
            const resetTable = () => setRevealedRows({});
            const revealAll = () => {
                 const allRevealed = {};
                 slides[currentSlide].tableData.forEach((_, index) => { allRevealed[index] = true; });
                 setRevealedRows(allRevealed);
                 setTriggerConfetti(true);
                 setTimeout(() => setTriggerConfetti(false), 2000);
            };
            const slides = [
                { type: 'cover', title: '的', pinyin: 'De', meaning: 'Possession / Description', subMeaning: 'Structural Particle' },
                {
                    type: 'progressive_concept', section: 'Usage', title: 'Modifier Magic',
                    steps: [
                        { label: 'Person', color: 'bg-soft-blue text-white', textColor: 'text-deep-blue', border: 'border-soft-blue', formula: 'Person (人)', icon: '👧', en: "my daughter's Chinese tea", cn: "我女儿的中国茶", py: "Wǒ nǚ'ér de Zhōngguó chá", desc: "Possession." },
                        { label: 'Adj', color: 'bg-soft-teal text-white', textColor: 'text-deep-teal', border: 'border-soft-teal', formula: 'Adj (形容词)', icon: '😋', en: "rich Chinese tea", cn: "好喝的中国茶", py: "Hǎohē de Zhōngguó chá", desc: "Description." },
                        { label: 'Verb', color: 'bg-soft-orange text-white', textColor: 'text-deep-orange', border: 'border-soft-orange', formula: 'Verb (动词)', icon: '🛍️', en: "the tea you buy", cn: "你买的中国茶", py: "Nǐ mǎi de Zhōngguó chá", desc: "Action." },
                    ]
                },
                { type: 'concept_omission', title: 'Omitting Noun', desc: 'Drop the noun if clear.' },
                {
                    type: 'smart_list', title: 'Phrases', theme: 'pink',
                    tableData: [
                        { icon: "👩‍🏫", en: "teacher's table", cn: "老师的桌子", py: "Lǎoshī de zhuōzi", highlight: "的" },
                        { icon: "📚", en: "book you buy", cn: "你买的书", py: "Nǐ mǎi de shū", highlight: "的" }
                    ]
                }
            ];
            const nextSlide = () => { if (currentSlide < slides.length - 1) { setCurrentSlide(curr => curr + 1); setConceptStep(0); setRevealedRows({}); } };
            const prevSlide = () => { if (currentSlide > 0) { setCurrentSlide(curr => curr - 1); setConceptStep(0); setRevealedRows({}); } };
            const nextConceptStep = () => { if (conceptStep < slides[1].steps.length - 1) setConceptStep(curr => curr + 1); };
            const prevConceptStep = () => { if (conceptStep > 0) setConceptStep(curr => curr - 1); };
            const renderContent = () => {
                const slide = slides[currentSlide];
                if (slide.type === 'progressive_concept') {
                    const currentData = slide.steps[conceptStep];
                    return (
                        <div className="flex flex-col h-full w-full bg-cream/50 p-4">
                            <div className="bg-white rounded-3xl p-4 shadow-md mb-4 flex items-center justify-center space-x-2">
                                {slide.steps.map((s, i) => (<div key={i} className={`px-2 py-1 rounded ${i===conceptStep ? 'bg-soft-pink text-white':'text-gray-300'}`}>{s.formula}</div>))}
                                <div className="bg-soft-pink text-white w-8 h-8 rounded-full flex items-center justify-center">的</div>
                                <div className="text-gray-400">Noun</div>
                            </div>
                            <div className="flex-1 flex flex-col items-center justify-center text-center">
                                <div className="text-8xl mb-4">{currentData.icon}</div>
                                <div className="text-4xl font-bold mb-2 font-serif-sc">
                                    <span className={currentData.textColor}>{currentData.cn.split('的')[0]}</span>
                                    <span className="mx-2 bg-soft-pink text-white px-2 rounded">的</span>
                                    <span>{currentData.cn.split('的')[1]}</span>
                                </div>
                                <div className="text-xl text-gray-500">{currentData.py}</div>
                                <div className="mt-4 bg-white p-2 rounded shadow-sm">{currentData.en}</div>
                            </div>
                            <div className="flex justify-center space-x-4 mt-4">
                                <button onClick={prevConceptStep} className="p-2 bg-white rounded-full shadow">⬅️</button>
                                <button onClick={nextConceptStep} className="p-2 bg-white rounded-full shadow">➡️</button>
                            </div>
                        </div>
                    );
                }
                return (
                    <div className="flex flex-col items-center justify-center h-full text-center p-6">
                        <div className="text-9xl font-bold text-deep-pink mb-4 font-serif-sc">{slide.title}</div>
                        <div className="text-2xl text-gray-600">{slide.meaning || slide.desc}</div>
                    </div>
                );
            };
            return (
                <div className="w-full h-full flex flex-col bg-cream relative">
                    <ConfettiCanvas active={triggerConfetti} />
                    <div className="flex-1 p-6 flex items-center justify-center">
                        <div className="bg-white/80 w-full max-w-4xl h-[600px] rounded-[3rem] shadow-2xl overflow-hidden border-8 border-white">
                            {renderContent()}
                        </div>
                    </div>
                    <div className="h-20 flex items-center justify-center space-x-8 bg-white/50 backdrop-blur">
                        <button onClick={prevSlide} className="text-3xl">👈</button>
                        <span className="font-bold text-xl">{currentSlide + 1} / {slides.length}</span>
                        <button onClick={nextSlide} className="text-3xl">👉</button>
                    </div>
                </div>
            );
        }
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<LessonPreview />);
    </script>
</body>
</html>
"""

# --- 3. CSS 注入：调优视觉设计 (间距/高对比度) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    .stApp { background-color: #FFFBF0; font-family: 'Noto Sans SC', sans-serif; }
    h1 { color: #BE185D; font-family: 'Noto Serif SC', serif; font-weight: 900; }

    /* 阅读卡片：解决拼音挤在一起的问题 */
    .reading-card {
        background-color: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(10px);
        padding: 40px;
        border-radius: 2.5rem;
        border: 6px solid white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        font-family: "Noto Serif SC", serif;
        line-height: 4.8; /* 👈 显著增加行高 */
        font-size: 28px;
        color: #333;
        margin-bottom: 25px;
    }

    /* 拼音 rt 样式 */
    ruby { ruby-position: under; margin: 0 8px; }
    rt { 
        color: #666; 
        font-size: 15px; 
        font-weight: 700; 
        padding-top: 15px; /* 👈 拼音与汉字拉开距离 */
        font-family: 'Noto Sans SC', sans-serif;
    }
    .hide-pinyin rt { visibility: hidden; }

    /* 语法贴纸按钮 */
    .stButton > button {
        background: #FF9A9E; 
        color: white; 
        border: 2px solid white; 
        border-radius: 12px;
        transform: rotate(-3deg);
        box-shadow: 0 4px 10px rgba(255, 154, 158, 0.4);
        font-weight: bold;
    }
    .stButton > button:hover {
        background: #BE185D;
        transform: scale(1.1) rotate(0deg);
    }
</style>
""", unsafe_allow_html=True)

# --- 4. 多语言文本 ---
UI_TEXT = {
    "Español": {
        "pinyin": "Pinyin", "trans": "Traducción", "hint": "¡Clica el carácter rosa!",
        "typing": "✍️ Práctica", "vocab": "📚 Unidades", "close": "❌ Cerrar Lección"
    },
    "English": {
        "pinyin": "Pinyin", "trans": "Translation", "hint": "Click pink character!",
        "typing": "✍️ Typing", "vocab": "📚 Units", "close": "❌ Close Lesson"
    }
}

# --- 5. 数据库 ---
DATABASE = {
    "title": "我的爱好 (My Hobbies)",
    "content": [
        {"char": "我", "pinyin": "wǒ", "unit": "U1"},
        {"char": "非常", "pinyin": "fēi cháng", "unit": "U2"},
        {"char": "喜欢", "pinyin": "xǐ huān", "unit": "U1"},
        {"char": "看书", "pinyin": "kàn shū", "unit": "U3"},
        {"char": "。", "pinyin": "", "unit": ""},
        {"char": "虽然", "pinyin": "suī rán", "unit": "U5"},
        {"char": "工作", "pinyin": "很忙", "pinyin_list": ["gōng zuò", "hěn máng"], "unit": "U2"},
        {"char": "，", "pinyin": "", "unit": ""},
        {"char": "但是", "pinyin": "dàn shì", "unit": "U5"},
        {"char": "的", "pinyin": "de", "unit": "Grammar", "is_grammar": True},
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

# --- 6. 核心逻辑：音频 ---
async def get_audio(text):
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await asyncio.sleep(0.1) # 稍微延迟防报错
    await communicate.save("audio.mp3")

# --- 7. 主程序 ---
def main():
    with st.sidebar:
        lang = st.selectbox("Language / Idioma", ["Español", "English"])
        ui = UI_TEXT[lang]
        st.divider()
        show_pinyin = st.toggle(ui["pinyin"], True)
        show_trans = st.toggle(ui["trans"], False)
        st.warning(ui["hint"])

    st.title(DATABASE["title"])
    
    # 语音
    plain_text = "".join([i['char'] for i in DATABASE["content"]])
    if "audio_ready" not in st.session_state:
        asyncio.run(get_audio(plain_text))
        st.session_state.audio_ready = True
    st.audio("audio.mp3")

    # 渲染卡片
    st.markdown(f'<div class="reading-card {"" if show_pinyin else "hide-pinyin"}">', unsafe_allow_html=True)
    
    # 使用列布局显示每个汉字
    cols = st.columns(len(DATABASE["content"]))
    for idx, item in enumerate(DATABASE["content"]):
        with cols[idx]:
            if item.get("is_grammar"):
                if st.button(item["char"], key=f"btn_{idx}"):
                    st.session_state.show_grammar = True
                st.markdown(f'<ruby style="color:#BE185D;">&nbsp;<rt>{item["pinyin"]}</rt></ruby>', unsafe_allow_html=True)
            else:
                p = item.get("pinyin_list", [item["pinyin"]])[0]
                st.markdown(f'<ruby>{item["char"]}<rt>{p}</rt></ruby>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 语法展示区
    if st.session_state.get("show_grammar"):
        if st.button(ui["close"]):
            st.session_state.show_grammar = False
            st.rerun()
        components.html(GRAMMAR_HTML_DE, height=850, scrolling=True)

    # 翻译/单元
    if show_trans:
        t = DATABASE["translation"]["es"] if lang == "Español" else DATABASE["translation"]["en"]
        st.markdown(f'<div class="trans-box"><b>{ui["trans"]}:</b> {t}</div>', unsafe_allow_html=True)

    st.divider()
    with st.expander(ui["vocab"]):
        v = [f"**{i['char']}** ({i['unit']})" for i in DATABASE["content"] if i['unit']]
        st.write(" / ".join(v))

if __name__ == "__main__":
    main()
