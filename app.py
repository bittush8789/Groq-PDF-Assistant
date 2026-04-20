import streamlit as st
import os
import time
import logging
from typing import List, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

# LangChain Imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate

# Robust Imports for Chains
try:
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
except ImportError:
    from langchain.chains.retrieval import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DocuQA")

# --- CONFIGURATION ---
class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuQA | AI PDF Chatbot"
    UPLOAD_DIR: str = "uploads"
    VECTOR_STORE_DIR: str = "vector_store_db"
    
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    LLM_MODEL: str = "models/gemini-2.0-flash"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    USE_GROQ: bool = True

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)

# --- CORE LOGIC ---

def load_and_split_pdf(file_path: str, filename: str) -> List[Document]:
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        for doc in documents:
            doc.metadata["filename"] = filename
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Split {filename} into {len(chunks)} chunks.")
        return chunks
    except Exception as e:
        logger.error(f"Error loading PDF {filename}: {e}")
        st.error(f"Failed to process {filename}")
        return []

@st.cache_resource
def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model=settings.EMBEDDING_MODEL, 
        google_api_key=settings.GEMINI_API_KEY
    )

def add_to_vector_store(chunks: List[Document], store_name: str = "index"):
    if not chunks:
        return None
    
    embeddings = get_embeddings()
    store_path = os.path.join(settings.VECTOR_STORE_DIR, store_name)
    
    try:
        if os.path.exists(store_path):
            vector_store = FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)
            vector_store.add_documents(chunks)
            logger.info(f"Added {len(chunks)} documents to existing vector store.")
        else:
            vector_store = FAISS.from_documents(chunks, embeddings)
            logger.info(f"Created new vector store with {len(chunks)} documents.")
        
        vector_store.save_local(store_path)
        return vector_store
    except Exception as e:
        logger.error(f"Error updating vector store: {e}")
        st.error("Failed to update vector database.")
        return None

def ask_question(query: str, store_name: str = "index"):
    embeddings = get_embeddings()
    store_path = os.path.join(settings.VECTOR_STORE_DIR, store_name)
    
    if not os.path.exists(store_path):
        return {"answer": "No documents uploaded yet.", "sources": []}
    
    try:
        vector_store = FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        
        prompt_template = """
        You are an expert AI assistant. Answer based ONLY on the provided context.
        If the answer isn't there, say "The answer is not available in the context."
        
        Context: {context}
        Question: {input}
        Answer:
        """
        
        if settings.USE_GROQ:
            model = ChatGroq(model=settings.GROQ_MODEL, groq_api_key=settings.GROQ_API_KEY, temperature=0.3)
        else:
            model = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, google_api_key=settings.GEMINI_API_KEY, temperature=0.3)
            
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "input"])
        document_chain = create_stuff_documents_chain(model, prompt)
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        response = retrieval_chain.invoke({"input": query})
        
        sources = []
        if "context" in response:
            for doc in response["context"]:
                sources.append({
                    "filename": doc.metadata.get("filename", "Unknown"),
                    "page": doc.metadata.get("page", -1) + 1
                })
                
        # Deduplicate sources
        unique_sources = []
        seen = set()
        for src in sources:
            key = (src["filename"], src["page"])
            if key not in seen:
                seen.add(key)
                unique_sources.append(src)
                
        return {"answer": response["answer"], "sources": unique_sources}
    except Exception as e:
        logger.error(f"Error in RAG chain: {e}")
        return {"answer": f"An error occurred: {str(e)}", "sources": []}

# --- STREAMLIT UI ---

def main():
    st.set_page_config(
        page_title="DocuQA | AI PDF Chatbot", 
        page_icon="📄", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for premium look
    st.markdown("""
        <style>
        .stApp { background-color: #0f172a; color: #f8fafc; }
        .stButton>button { background-color: #2563eb; color: white; border-radius: 8px; width: 100%; }
        .citation { font-size: 0.85rem; color: #94a3b8; margin-top: 4px; border-left: 2px solid #3b82f6; padding-left: 8px; }
        .stChatInputContainer { border-top: 1px solid #1e293b; }
        [data-testid="stSidebar"] { background-color: #1e293b; }
        </style>
    """, unsafe_allow_html=True)

    # Header
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        st.write("## 📄")
    with col2:
        st.title("DocuQA: Unified AI PDF Chatbot")
    
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.title("📂 Document Center")
        st.markdown("Upload your PDFs and let AI analyze them.")
        
        uploaded_files = st.file_uploader(
            "Select PDF files", 
            type="pdf", 
            accept_multiple_files=True,
            help="Maximum 200MB per file"
        )
        
        if st.button("🚀 Process & Index"):
            if uploaded_files:
                with st.status("Indexing documents...", expanded=True) as status:
                    progress_bar = st.progress(0)
                    for i, uploaded_file in enumerate(uploaded_files):
                        temp_path = os.path.join(settings.UPLOAD_DIR, uploaded_file.name)
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        chunks = load_and_split_pdf(temp_path, uploaded_file.name)
                        add_to_vector_store(chunks)
                        progress_bar.progress((i + 1) / len(uploaded_files))
                        st.write(f"✅ Processed: {uploaded_file.name}")
                    
                    status.update(label="Indexing Complete!", state="complete", expanded=False)
                st.success("Successfully indexed documents!")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("Please upload at least one PDF file.")

        st.divider()
        st.subheader("⚙️ AI Configuration")
        
        if settings.USE_GROQ:
            groq_model_options = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
            selected_model = st.selectbox("Select Groq Model", groq_model_options, index=0)
            settings.GROQ_MODEL = selected_model
            st.info(f"⚡ Model: {selected_model}")
        else:
            st.info(f"⚡ Model: {settings.LLM_MODEL}")

        st.divider()
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

    # Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message:
                for src in message["sources"]:
                    st.markdown(f'<div class="citation">Source: {src["filename"]} | Page {src["page"]}</div>', unsafe_allow_html=True)

    # User Input
    if prompt := st.chat_input("Ask me anything about your documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing documents..."):
                result = ask_question(prompt)
                st.markdown(result["answer"])
                for src in result["sources"]:
                    st.markdown(f'<div class="citation">Source: {src["filename"]} | Page {src["page"]}</div>', unsafe_allow_html=True)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result["sources"]
                })

if __name__ == "__main__":
    main()
