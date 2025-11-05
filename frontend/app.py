"""Streamlit frontend for RAG application."""
import streamlit as st
import requests

API_URL = "http://localhost:8000"


def check_api_health() -> bool:
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def upload_pdf(file) -> dict | None:
    """Upload PDF to the backend."""
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        response = requests.post(f"{API_URL}/upload", files=files, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error uploading PDF: {str(e)}")
        return None


def query_document(question: str) -> str | None:
    """Query the document via the backend."""
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"question": question},
            timeout=60
        )
        response.raise_for_status()
        return response.json()["answer"]
    except requests.exceptions.RequestException as e:
        st.error(f"Error querying document: {str(e)}")
        return None


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="RAG PDF Query",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Langchain RAG PDF Query System")
    st.markdown("Upload a PDF document and ask questions about its content.")
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ Backend API is not running. Please start the FastAPI server first.")
        st.code("uv run uvicorn backend.main:app --reload", language="bash")
        return
    
    # Sidebar for PDF upload
    with st.sidebar:
        st.header("📄 Upload PDF")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type="pdf",
            help="Upload a PDF document to query"
        )
        
        if uploaded_file is not None:
            if st.button("Upload and Process", type="primary"):
                with st.spinner("Processing PDF..."):
                    result = upload_pdf(uploaded_file)
                    if result:
                        st.success(f"✅ {result['message']}")
                        st.info(f"Processed {result['chunks']} text chunks")
                        st.session_state.pdf_uploaded = True
                        st.session_state.pdf_filename = result['filename']
        
        if st.session_state.get("pdf_uploaded", False):
            st.success("PDF is ready for queries!")
            st.caption(f"File: {st.session_state.get('pdf_filename', 'Unknown')}")
    
    # Main content area
    if not st.session_state.get("pdf_uploaded", False):
        st.info("👈 Please upload a PDF file using the sidebar to get started.")
    else:
        st.header("💬 Ask Questions")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if question := st.chat_input("Ask a question about the PDF..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            
            # Get answer
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = query_document(question)
                    if answer:
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        error_msg = "Sorry, I couldn't process your question. Please try again."
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    main()
