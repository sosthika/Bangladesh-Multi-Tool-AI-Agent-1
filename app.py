"""Optional Streamlit interface."""
import streamlit as st
from agent import build_agent

st.set_page_config(page_title="Bangladesh Multi-Tool AI Agent", page_icon="🇧🇩")
st.title("🇧🇩 Bangladesh Multi-Tool AI Agent")
st.caption("Ask about institutions, hospitals, restaurants, or Bangladesh general knowledge.")

@st.cache_resource
def get_agent():
    return build_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "executor" not in st.session_state:
    try:
        st.session_state.executor = get_agent()
    except Exception as exc:
        st.error(f"Agent setup failed: {exc}")
        st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask a question...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    history = [("human" if m["role"] == "user" else "assistant", m["content"]) for m in st.session_state.messages[:-1]]
    with st.chat_message("assistant"):
        with st.spinner("Choosing a tool..."):
            try:
                result = st.session_state.executor.invoke({"input": question, "chat_history": history[-10:]})
                answer = result.get("output", "No answer returned.")
            except Exception as exc:
                answer = f"Error: {exc}"
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
