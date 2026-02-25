import streamlit as st
import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Groq 클라이언트 초기화
api_key = os.getenv("GROQ_API_KEY")
client = None
if api_key and api_key != "your_groq_api_key_here":
    client = Groq(api_key=api_key)

# 데이터 로드
@st.cache_data
def load_chatbot_data():
    file_path = os.path.join('data', 'categorized_data.csv')
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return None

def get_chatbot_context(query, df):
    if df is None or df.empty:
        return "데이터를 찾을 수 없습니다."
    
    related = df[
        df['name'].str.contains(query, case=False, na=False) |
        df['brand'].str.contains(query, case=False, na=False) |
        df['category'].str.contains(query, case=False, na=False)
    ].head(10)
    
    if related.empty:
        return f"현재 {len(df)}개의 행사 상품 정보가 있습니다."
    
    context = "관련 상품 정보:\n"
    for _, row in related.iterrows():
        context += f"- [{row['brand']}] {row['name']} | {row['price']}원 | {row['event']}\n"
    
    return context

def show_chatbot():
    """오른쪽 하단에 작고 예쁘게 고정되는 팝업 챗봇"""
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    st.markdown("""
        <style>
        /* 1. 팝오버 전체 '컨테이너' (버튼 영역) */
        div[data-testid="stPopover"] {
            position: fixed !important;
            bottom: 30px !important;
            right: 30px !important;
            left: auto !important;
            width: 65px !important;  
            height: 65px !important; 
            z-index: 999999 !important;
        }
        
        /* 2. 둥근 챗봇 토글 버튼 */
        div[data-testid="stPopover"] > button {
            width: 65px !important;
            height: 65px !important;
            border-radius: 50% !important;
            background-color: #007bff !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.4) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 30px !important;
            padding: 0 !important;
            transition: transform 0.2s ease !important;
        }
        
        div[data-testid="stPopover"] > button:hover {
            transform: scale(1.1) rotate(5deg) !important;
        }
        
        /* 3. 챗봇 대화창 박스 속성 */
        div[data-testid="stPopoverBody"] {
            position: fixed !important;
            bottom: 110px !important;       /* ★ 여기서 높낮이 조절! (버튼 65px + 여백 20px) */
            right: 30px !important;        
            
            /* ★★★ Streamlit의 위치 강제 고정 완벽 무력화 (이게 빠져서 안 움직인 겁니다!) ★★★ */
            top: auto !important;          /* 👈 핵심!! 위쪽 기준점을 없애야 bottom이 작동합니다 */
            left: auto !important;
            transform: none !important;    
            margin: 0 !important;
            
            /* 크기 정확하게 고정 */
            width: 380px !important; 
            min-width: 380px !important;
            max-width: 380px !important;
            height: 550px !important;      
            
            background-color: #1c2128 !important; 
            border: 1px solid #30363d !important;
            border-radius: 20px !important;
            box-shadow: 0 15px 50px rgba(0,0,0,0.7) !important;
            z-index: 999998 !important;
            padding: 0 !important; 
            overflow: hidden !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # st.popover를 사용하여 토글 로직을 Streamlit에 맡김
    with st.popover("💬"):
        # 헤더 영역
        st.markdown("""
            <div style='padding: 15px 20px; background-color: #21262d; border-bottom: 1px solid #30363d;'>
                <h4 style='margin: 0; color: #58a6ff; display: flex; align-items: center; gap: 10px;'>
                    🏪 편의점 꿀팁봇
                </h4>
            </div>
        """, unsafe_allow_html=True)
        
        # 실제 메시지가 표시될 공간
        chat_container = st.container(height=380)
        
        with chat_container:
            if not st.session_state.messages:
                st.info("무엇이든 물어보세요! 예: 'GS25 1+1 음료 알려줘'")
            
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # 입력창
        if prompt := st.chat_input("질문을 입력하세요..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            # AI 응답
            if client:
                with chat_container:
                    with st.chat_message("assistant"):
                        df = load_chatbot_data()
                        context = get_chatbot_context(prompt, df)
                        
                        system_prompt = f"당신은 편의점 행사 도우미입니다. 다음 데이터를 바탕으로 친절하고 센스있게 대답하세요. [데이터]: {context}"
                        
                        message_placeholder = st.empty()
                        full_response = ""
                        
                        try:
                            response = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[{"role": "system", "content": system_prompt}, *st.session_state.messages[-5:]],
                                stream=True,
                            )
                            for chunk in response:
                                if chunk.choices[0].delta.content:
                                    full_response += chunk.choices[0].delta.content
                                    message_placeholder.markdown(full_response + "▌")
                            message_placeholder.markdown(full_response)
                        except Exception as e:
                            full_response = f"현재 연결이 원활하지 않습니다. ({e})"
                            message_placeholder.markdown(full_response)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()