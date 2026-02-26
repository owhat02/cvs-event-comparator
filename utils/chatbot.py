import streamlit as st
import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv
import time

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None


# CSV 데이터 로드
@st.cache_data
def load_chatbot_data():
    path = os.path.join("data", "categorized_data.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


def show_chatbot():
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "🏪 **편의점 꿀팁봇 사용법**\n\n"
                           "1. **상품 검색**: 궁금한 상품명을 입력하세요.\n"
                           "2. **행사 확인**: 1+1, 2+1 등 행사 정보를 묻어보세요.\n"
                           "3. **카테고리**: '과자', '도시락' 등으로 검색 가능합니다."
            }
        ]

    # 배경색 문제 해결 및 기존 UI 스타일 유지
    st.markdown("""
    <style>
    /* 팝업 버튼 위치 및 디자인 */
    div[data-testid="stPopover"] {
        position: fixed !important; 
        bottom: 30px !important; 
        right: 30px !important; 
        width: 65px !important; 
        height: 65px !important; 
        z-index: 999999 !important;
    }
    div[data-testid="stPopover"] > button {
        width: 65px !important; 
        height: 65px !important; 
        border-radius: 50% !important; 
        background-color: #007bff !important; 
        color: white !important; 
        border: none !important; 
        font-size: 30px !important;
    }
    /* 팝업 본체 및 배경색 고정 (검정색 변현 방지) */
    div[data-testid="stPopoverBody"] {
        position: fixed !important; 
        bottom: 110px !important; 
        right: 30px !important; 
        width: 380px !important; 
        height: 550px !important; 
        background-color: #1c2128 !important; 
        border: 1px solid #30363d !important;
        border-radius: 20px !important; 
        padding: 10px !important; 
        overflow: hidden !important;
    }
    /* 입력창 배경색 최적화 */
    .stChatFloatingInputContainer {
        background-color: transparent !important;
    }
    div[data-testid="stChatInput"] {
        background-color: #0d1117 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.popover("💬"):
        st.markdown("<h4 style='color:#58a6ff; margin-bottom:10px;'>🏪 편의점 꿀팁봇</h4>", unsafe_allow_html=True)

        # 채팅 컨테이너
        chat_container = st.container(height=400)

        # 기존 메시지 출력
        for msg in st.session_state.messages:
            with chat_container:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # 채팅 입력 (중복 방지를 위해 고정 키 사용)
        prompt = st.chat_input("질문을 입력하세요...", key="chatbot_input_unique")

        if prompt:
            # 사용자 메시지 기록
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            if client:
                with chat_container:
                    with st.chat_message("assistant"):
                        placeholder = st.empty()
                        placeholder.markdown("…")

                        # 데이터 준비
                        df = load_chatbot_data()
                        context = ""
                        if not df.empty:
                            sample_df = df.sample(n=min(15, len(df)))
                            for _, row in sample_df.iterrows():
                                context += f"[{row['brand']}] {row['name']} | {row['price']}원 | {row['event']} | {row['category']}\n"
                        else:
                            context = "조건에 맞는 행사 상품이 없습니다."

                        system_prompt = f"""
                        당신은 센스있고 친절한 편의점 행사 도우미예요.
                        사용자가 묻는 질문에 대해 아래 [검색된 데이터]만 사용해서 답변하세요.
                        답변은 자연스럽고 친근하게, 반드시 제공된 데이터 정보만 사용하세요.
                        언어는 무조건 한국어만 사용 그외의 언어 사용금지
                        [검색된 데이터]
                        {context}
                        """
                        full_response = ""
                        try:
                            # Groq 스트리밍 응답
                            response = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    *st.session_state.messages[-5:]
                                ],
                                stream=True,
                                temperature=0.5,
                                top_p=0.9
                            )

                            for chunk in response:
                                if chunk.choices[0].delta.content:
                                    full_response += chunk.choices[0].delta.content
                                    placeholder.markdown(full_response + "▌")

                            placeholder.markdown(full_response)

                        except Exception as e:
                            full_response = f"오류 발생: {e}"
                            placeholder.markdown(full_response)

                        # 기록 저장
                        st.session_state.messages.append({"role": "assistant", "content": full_response})