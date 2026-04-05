import asyncio
import io

import streamlit as st
from fastapi import UploadFile

from app.agents import smartdocs_agent
from app.rag_pipeline import ingest_pdf
from app.schemas import AskResponse


st.set_page_config(
    page_title="SmartDocs Dashboard",
    page_icon="🧠💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=Inter:wght@400;500;600&display=swap');
    body {
        font-family: 'Inter', 'Space Grotesk', system-ui, sans-serif;
        background-color: #f4f3f8;
        color: #111322;
    }
    .stApp { 
        background: linear-gradient(180deg, #fdfdfd 0%, #f2f4ff 60%, #e5ecff 100%);
    }
    .stApp .block-container {
        background: rgba(255, 255, 255, 0.98);
        border-radius: 28px;
        padding: 2.8rem 3rem;
        border: 1px solid rgba(109, 118, 161, 0.25);
        box-shadow: 0 35px 55px rgba(24, 28, 69, 0.12);
    }
    .stHeader, .stMarkdown {
        color: #111322;
    }
    .stButton>button {
        background: linear-gradient(135deg, #a0b4ff, #fbcde6);
        color: #090b15;
        border-radius: 14px;
        border: none;
        font-weight: 600;
        padding: 0.75rem 1.8rem;
        letter-spacing: 0.02em;
        box-shadow: 0 12px 30px rgba(16, 24, 72, 0.18);
    }
    .stButton>button:hover {
        filter: brightness(1.08);
    }
    .stTextInput>div>input, .stTextArea>div>textarea {
        background: rgba(248, 250, 255, 0.9);
        color: #0f172a;
        border: 1px solid rgba(92, 100, 149, 0.35);
        border-radius: 12px;
        font-family: 'Inter', sans-serif;
    }
    .st-selectbox>div, .st-radio>div {
        background: rgba(255, 255, 255, 0.8);
    }
    .stSidebar .sidebar-content {
        background: linear-gradient(180deg, #ffffff 0%, #e8ecff 100%);
        border-radius: 24px;
        border: 1px solid rgba(109, 118, 161, 0.3);
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.3), 0 20px 25px rgba(15, 23, 42, 0.1);
    }
    .stSidebar .stMetric { color: #111322; }
    .result-card {
        border-radius: 18px;
        background: #fff;
        padding: 1.5rem;
        border: 1px solid rgba(109, 118, 161, 0.2);
        box-shadow: 0 15px 35px rgba(15, 23, 42, 0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_async(coro):
    return asyncio.run(coro)


def handle_ingest(uploaded_file):
    if uploaded_file is None:
        return "Upload a PDF to ingest."

    content = uploaded_file.read()
    st.session_state["last_upload_name"] = uploaded_file.name
    upload_file = UploadFile(filename=uploaded_file.name, file=io.BytesIO(content))
    with st.spinner("Ingesting document into the vector store..."):
        result = run_async(ingest_pdf(upload_file))
    return result


def ask_agent(question_text, tone_label):
    question_prompt = f"{question_text.strip()} (Answer style: {tone_label})"
    with st.spinner("Querying SmartDocs AI…"):
        raw_response = run_async(smartdocs_agent.ainvoke({"question": question_prompt}))
    return AskResponse.parse_obj(raw_response)


def main():
    st.title("SmartDocs AI 🌈")
    st.subheader("Upload your PDF, ask a question, and get a citation-backed answer on the same page.")

    if "ingest_status" not in st.session_state:
        st.session_state.ingest_status = "No document ingested yet."
    if "agent_response" not in st.session_state:
        st.session_state.agent_response = None

    with st.container():
        upload_col, question_col = st.columns(2, gap="large")

        with upload_col:
            st.header("1. Upload & Ingest 📄")
            pdf_file = st.file_uploader("Drop a PDF or click to browse", type=["pdf"], key="pdf_uploader")
            if st.button("Ingest document", key="ingest_btn"):
                try:
                    response = handle_ingest(pdf_file)
                    st.session_state.ingest_status = f"Ingested {response['chunks']} chunks from {response.get('status', 'the PDF')}."
                    st.success("Document ingested successfully!")
                except Exception as exc:
                    st.error(f"Failed to ingest document: {exc}")
            st.caption(st.session_state.ingest_status)
            with st.expander("Why ingest?"):
                st.write(
                    "Uploading the document uploads its vector embeddings into the local Chroma store. "
                    "Once ingested, the assistant can retrieve the right paragraphs to answer your question."
                )

        with question_col:
            st.header("2. Ask SmartDocs 🧠")
            question_input = st.text_area(
                "Ask anything about the uploaded document:",
                value="Summarize the topic of the key projects described for the associate engineer role.",
                height=140,
            )
            tone = st.radio("Answer tone", ["Concise", "Detailed", "Playful"], horizontal=True)
            if st.button("Ask the Assistant", key="ask_btn"):
                if not question_input.strip():
                    st.warning("Please enter a question.")
                else:
                    try:
                        response = ask_agent(question_input, tone)
                        st.session_state.agent_response = response
                    except Exception as exc:
                        st.error(f"Agent failed: {exc}")
            st.caption("The assistant looks through the ingested chunks and runs the applicable tool before calling GPT.")

    if st.session_state.agent_response:
        response = st.session_state.agent_response
        st.markdown("---")
        result_container = st.container()
        with result_container:
            st.subheader("SmartDocs Answer")
            st.metric("Confidence score", f"{response.score:.2f}", delta="👀")
            st.markdown(f"**Question:** {response.question}")
            st.markdown("**Answer:**")
            st.write(response.final_answer)
            if response.tool_output:
                st.markdown("**Tool Output:**")
                if isinstance(response.tool_output, (dict, list)):
                    st.json(response.tool_output)
                else:
                    st.write(response.tool_output)
            st.markdown("**Retrieved context:**")
            st.write(response.context)

        st.markdown(
            """
            <div style="background: rgba(255,255,255,0.05); border-radius: 18px; padding: 12px; border: 1px dashed rgba(248,250,252,0.5);">
            Pro tip: mention keywords such as “topic:” or “architecture” to trigger the specialized tools.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.sidebar:
        st.header("Status Panel")
        st.metric("Document", st.session_state.get("last_upload_name", "Not uploaded"))
        st.metric("Last question", st.session_state.agent_response.question if st.session_state.agent_response else "None")
        st.select_slider("Vibe", options=["Calm", "Energetic", "Vivid"])

    st.markdown("---")
    st.caption("Built with care for SmartDocs AI by Sruthi Nayagi")


if __name__ == "__main__":
    main()
