import streamlit as st
import asyncio
import edge_tts
import os
import time
import random
import html

# --- 1. 页面基本配置 ---
st.set_page_config(
    page_title="阅读 Pro - 智能适配版", 
    page_icon="🎓", 
    layout="wide"
)

# --- 2. 界面双语语言包 ---
UI_TEXT = {
    "Español": {
        "pinyin": "Pinyin", "trans": "Traducción", "audio_gen": "Preparando voces...",
        "typing_title": "✍️ Práctica", "typing_instr": "Escribe el texto de arriba aquí.", "perfect": "🎉 ¡Excelente!"
    },
    "English": {
        "pinyin": "Pinyin", "trans": "Translation", "audio_gen": "Generating voices...",
        "typing_title": "✍️ Practice", "typing_instr": "Type the text above here.", "perfect": "🎉 Perfect!"
    }
}

# --- 3. 视觉设计 (CSS) - 智能响应式核心 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;700&display=swap');
    
    .stApp { background-color: #FFFBF0; }
    
    /* 1. 极限压缩顶部空间，把位置留给内容 */
    .block-container { 
        padding-top: 1.5rem !important; 
        padding-bottom: 1rem !important; 
        max-width: 1000px !important; 
    }

    /* 2. 智能阅读框：根据屏幕高度自动伸缩 */
    .reading-scroll-area {
        background-color: white; 
        padding: 15px 25px; 
        border-radius: 1.5rem;
        border: 2px solid #eee;
        overflow-y: auto;
        margin-bottom: 10px;
        transition: height 0.3s ease; /* 平滑过渡 */
    }

    /* 🧠 智能断点逻辑 (Media Queries) */
    
    /* 情况A: 大屏幕 (高度 > 900px) */
    @media (min-height: 901px) {
        .reading-scroll-area { height: 60vh; } 
    }

    /* 情况B: 普通笔记本 (高度 700px - 900px) */
    @media (max-height: 900px) {
        .reading-scroll-area { height: 50vh; } 
    }

    /* 情况C: 小屏幕/缩放150% (高度 < 700px) */
    @media (max-height: 700px) {
        .reading-scroll-area { height: 38vh; } 
        ruby { font-size: 18px !important; } /* 字体自动缩小 */
        .text-content { line-height: 2.2 !important; }
    }

    /* 行布局 */
    .line-container { 
        display: flex; 
        margin-bottom: 6px; 
        align-items: flex-start;
        justify-content: space-between;
        padding-bottom: 6px;
        border-bottom: 1px solid #fcfcfc;
    }

    .left-zone { display: flex; flex: 1; align-items: flex-start; max-width: 75%; }

    .role-label {
        min-width: 50px; font-weight: 900; color: #BE185D; 
        font-size: 0.95em; padding-top: 8px; font-family: 'Noto Serif SC', serif;
    }

    .text-content { line-height: 2.6; }

    ruby { 
        ruby-position: under; padding: 0 2px; font-family: "Noto Serif SC", serif; 
        font-size: 22px; font-weight: 900; color: #333; 
    }

    rt { 
        font-family: 'Noto Sans SC', sans-serif; font-size: 11px; 
        color: #15803D !important; font-weight: 700; padding-top: 5px !important; 
    }

    .right-zone {
        width: 22%; background: #EFF6FF; border-left: 3px solid #3B82F6;
        padding: 5px 10px; border-radius: 8px; margin-top: 5px;
    }

    .trans-text { 
        font-size: 0.8rem; color: #1D4ED8; 
        font-family: 'Noto Sans SC', sans-serif; font-weight: 700; line-height: 1.2;
    }

    /* 3. 底部打字区：紧凑设计 */
    .typing-section {
        background: #fff; padding: 8px 20px; border-radius: 1rem;
        border: 2px solid #eee; box-shadow: 0 -4px 10px rgba(0,0,0,0.02);
    }

    .instr-text { color: #666; font-size: 0.8em; font-weight: 700; margin-bottom: 2px; }

    .hide-
