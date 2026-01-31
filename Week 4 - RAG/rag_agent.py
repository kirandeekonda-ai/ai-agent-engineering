"""
Week 4: RAG Agent - Document Q&A

This agent demonstrates Retrieval-Augmented Generation:
1. Load documents and split into chunks
2. Create embeddings and store in ChromaDB
3. Retrieve relevant chunks for user questions
4. Generate answers using LLM with retrieved context
"""
from pathlib import Path
from dotenv import load_dotenv
import os
from typing import TypedDict, Annotated, Optional
import operator

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END

# Load .env from parent directory (shared config)
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- CONFIGURATION ---
DOCS_DIR = Path(__file__).parent / "documents"
CHROMA_DIR = Path(__file__).parent / "chroma_db"

# --- 1. EMBEDDINGS MODEL ---
print("[SETUP] Loading embedding model...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",  # Small, fast, good quality
    model_kwargs={'device': 'cpu'}
)

# --- 2. VECTOR STORE ---
def load_or_create_vectorstore():
    """Load existing vectorstore or create new one from documents."""
    
    if CHROMA_DIR.exists():
        print("[SETUP] Loading existing vector store...")
        return Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=embeddings
        )
    
    print("[SETUP] Creating new vector store from documents...")
    
    # Load all markdown files from documents folder
    loader = DirectoryLoader(
        str(DOCS_DIR),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    print(f"  Loaded {len(documents)} document(s)")
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"  Split into {len(chunks)} chunk(s)")
    
    # Create vectorstore
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR)
    )
    print(f"  Vector store created at {CHROMA_DIR}")
    
    return vectorstore

vectorstore = load_or_create_vectorstore()
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})  # Top 3 chunks

# --- 3. LLM ---
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROQ_API_KEY")
)

# --- 4. STATE ---
class RAGState(TypedDict):
    question: str
    context: str  # Retrieved documents
    answer: str

# --- 5. NODES ---
def retrieve_node(state: RAGState) -> dict:
    """Retrieve relevant document chunks."""
    question = state["question"]
    print(f"\n[RETRIEVE] Searching for: '{question}'")
    
    docs = retriever.invoke(question)
    
    # Combine retrieved chunks
    context = "\n\n---\n\n".join([
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    ])
    
    print(f"  Found {len(docs)} relevant chunk(s)")
    return {"context": context}

def generate_node(state: RAGState) -> dict:
    """Generate answer using retrieved context."""
    question = state["question"]
    context = state["context"]
    
    print("\n[GENERATE] Creating answer...")
    
    system_prompt = """You are a helpful assistant that answers questions based on the provided context.

Rules:
1. ONLY use information from the provided context to answer.
2. If the context doesn't contain the answer, say "I don't have information about that in the documents."
3. Be concise and direct.
4. Quote specific details when relevant."""

    user_prompt = f"""Context:
{context}

Question: {question}

Answer:"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    answer = response.content
    print(f"\n[ANSWER] {answer}")
    return {"answer": answer}

# --- 6. BUILD GRAPH ---
workflow = StateGraph(RAGState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()

# --- 7. RUN ---
if __name__ == "__main__":
    import sys
    
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How many days of annual leave do employees get?"
    print(f"Question: {question}")
    print("=" * 50)
    
    result = app.invoke({
        "question": question,
        "context": "",
        "answer": ""
    })
    
    print("\n" + "=" * 50)
    print("Final Answer:", result["answer"])
