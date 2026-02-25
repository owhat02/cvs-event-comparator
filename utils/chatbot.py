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

# ★ 핵심 1: 검색 능력을 대폭 강화 (문장에서 불용어 빼고 키워드만 쏙쏙 뽑아 검색)
def get_chatbot_context(query, df):
    if df is None or df.empty:
        return "데이터베이스를 찾을 수 없습니다."
    
    # 1. 일상적인 대화 단어(불용어) 걸러내기
    stopwords = ['알려줘', '뭐있어', '뭐가', '있어', '주세요', '찾아줘', '어떤', '가장', '추천해줘', '은', '는', '이', '가', '에서', '파는', '?']
    query_cleaned = query
    for word in stopwords:
        query_cleaned = query_cleaned.replace(word, ' ')
        
    keywords = [k for k in query_cleaned.split() if k.strip()]
    
    if not keywords:
        return "구체적인 브랜드나 상품명, 행사 종류를 입력해 주세요."

    # 2. 브랜드, 이름, 카테고리, 행사를 합친 텍스트에서 키워드가 포함되어 있는지 '모두' 검사 (AND 조건)
    combined_text = df['brand'].astype(str) + " " + df['name'].astype(str) + " " + df['category'].astype(str) + " " + df['event'].astype(str)
    
    mask = pd.Series(True, index=df.index)
    for kw in keywords:
        mask = mask & combined_text.str.contains(kw, case=False, na=False)
        
    related = df[mask].head(20) # AI에게 줄 힌트를 20개까지 넉넉히 제공
    
    # 3. 만약 AND 검색 결과가 없으면, 키워드 중 하나라도 들어간 것(OR 조건)으로 재검색
    if related.empty:
        or_mask = pd.Series(False, index=df.index)
        for kw in keywords:
            or_mask = or_mask | combined_text.str.contains(kw, case=False, na=False)
        related = df[or_mask].head(10)
        
    # 최종적으로 못 찾은 경우
    if related.empty:
        return "해당 조건에 맞는 행사 상품이 현재 데이터에 없습니다."
    
    # AI가 읽기 편하게 정리해서 전달
    context = ""
    for _, row in related.iterrows():
        context += f"[{row['brand']}] {row['name']} | 가격: {row['price']}원 | 행사: {row['event']} | 분류: {row['category']}\n"
    
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
            bottom: 110px !important;      
            right: 30px !important;        
            
            top: auto !important;          
            left: auto !important;
            transform: none !important;    
            margin: 0 !important;
            
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

    with st.popover("💬"):
        st.markdown("""
            <div style='padding: 15px 20px; background-color: #21262d; border-bottom: 1px solid #30363d;'>
                <h4 style='margin: 0; color: #58a6ff; display: flex; align-items: center; gap: 10px;'>
                    🏪 편의점 꿀팁봇
                </h4>
            </div>
        """, unsafe_allow_html=True)
        
        chat_container = st.container(height=380)
        
        with chat_container:
            if not st.session_state.messages:
                st.info("무엇이든 물어보세요! 예: 'GS25 1+1 음료 알려줘'")
            
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if prompt := st.chat_input("질문을 입력하세요..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            if client:
                with chat_container:
                    with st.chat_message("assistant"):
                        df = load_chatbot_data()
                        context = get_chatbot_context(prompt, df)
                        
                        # ★ 핵심 2: AI에게 "주어진 데이터로만 대답하라"고 강력하게 지시하는 프롬프트
                        system_prompt = f"""당신은 편의점 행사 도우미입니다. 
아래 제공된 [검색된 데이터]에 있는 상품 정보만을 사용해서 답변하세요.
만약 [검색된 데이터]가 비어있거나 '데이터가 없습니다'라고 나와있다면, 절대 정보를 지어내지 말고 "제가 가진 행사 데이터에서는 해당 상품을 찾을 수 없습니다."라고 솔직하게 답변하세요.
질문과 무관한 내용은 답변하지 마세요. 답변 시 한글만 사용하세요(한자 불가).

[검색된 데이터]
{context}
"""
                        
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