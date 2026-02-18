# --- 核心 AI 调用逻辑修改 ---
def call_real_ai(topic, level, keywords):
    if not MY_API_KEY:
        st.error("❌ Key missing")
        return None
    try:
        genai.configure(api_key=MY_API_KEY)
        
        # 💡 强制切换到你已验证成功的 2.0 模型
        model = genai.GenerativeModel('gemini-2.0-flash-exp') 
        
        prompt = f"Create a Chinese dialogue JSON about {topic} for {level} with words {keywords}."
        response = model.generate_content(prompt)
        
        # 自动清洗并解析数据
        raw_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(raw_text)
    except Exception as e:
        # 直接把报错详情显示在侧边栏红色框里
        st.sidebar.markdown(f'<div style="color:red;border:1px solid red;padding:5px;">⚠️ API Error: {str(e)}</div>', unsafe_allow_html=True)
        return None
