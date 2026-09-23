import os
import shutil
import gradio as gr
from backend.app.config import settings
from backend.app.rag.pipeline import rag_pipeline
from backend.app.database.database import init_db, SessionLocal
from backend.app.database.repository import DocumentRepository
from backend.app.rag.document_loader import DocumentLoader
from backend.app.rag.chunker import RecursiveCharacterChunker
from backend.app.rag.embeddings import embedding_service
from backend.app.utils.logging import logger

# Initialize database
init_db()

uploaded_docs_list = []

def load_existing_docs():
    global uploaded_docs_list
    try:
        db = SessionLocal()
        repo = DocumentRepository(db)
        docs = repo.get_all()
        uploaded_docs_list = [f"📄 {d.filename} ({d.file_type.upper()})" for d in docs]
        db.close()
    except Exception as e:
        logger.error(f"Error loading docs: {e}")

load_existing_docs()

def upload_and_index(files):
    if not files:
        return "⚠️ Please select at least one document (PDF, DOCX, or TXT).", "\n".join(uploaded_docs_list)
    
    results = []
    db = SessionLocal()
    repo = DocumentRepository(db)
    
    for file_obj in files:
        filepath = file_obj.name
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        
        try:
            # Copy to upload directory
            dest_path = os.path.join(settings.UPLOAD_DIR, filename)
            shutil.copy2(filepath, dest_path)
            
            doc_id = f"doc_{len(uploaded_docs_list) + 1}_{int(os.path.getmtime(dest_path))}"
            
            # Record in database
            repo.create(
                doc_id=doc_id,
                filename=filename,
                file_type=ext,
                file_size=os.path.getsize(dest_path),
                file_path=dest_path
            )
            
            # Ingest in RAG pipeline
            chunks = rag_pipeline.ingest_document(
                file_path=dest_path,
                filename=filename,
                document_id=doc_id
            )
            
            repo.save_chunks(chunks)
            repo.update_status(doc_id=doc_id, status="indexed", chunk_count=len(chunks))
            
            item_name = f"📄 {filename} ({len(chunks)} chunks)"
            if item_name not in uploaded_docs_list:
                uploaded_docs_list.append(item_name)
                
            results.append(f"✅ Successfully indexed '{filename}' ({len(chunks)} chunks)")
        except Exception as e:
            results.append(f"❌ Failed to process '{filename}': {str(e)}")
            
    db.close()
    return "\n".join(results), "\n".join(uploaded_docs_list) if uploaded_docs_list else "No documents uploaded yet."

async def chat_respond(user_message, history):
    if not user_message.strip():
        return "", history
    
    # Format chat history
    formatted_history = []
    if history:
        for turn in history:
            formatted_history.append({"role": "user", "content": turn[0]})
            if turn[1]:
                formatted_history.append({"role": "assistant", "content": turn[1]})
                
    try:
        res = await rag_pipeline.query(
            question=user_message,
            chat_history=formatted_history
        )
        
        answer = res.get("answer", "No answer generated.")
        sources = res.get("sources", [])
        confidence = res.get("confidence", 0.0)
        
        # Build source citation text
        citation_text = ""
        if sources:
            citation_text = "\n\n---\n### 📚 Sources Consulted:\n"
            for idx, s in enumerate(sources[:3], 1):
                doc_name = s.get("document", "Document")
                page = s.get("page", "N/A")
                score = s.get("score", 0.0)
                preview = s.get("preview", "")[:120]
                page_str = f"Page {page}" if page is not None else "Page N/A"
                citation_text += f"\n**[{idx}] {doc_name}** ({page_str}) — *Relevance: {score:.1%}*\n> \"{preview}...\"\n"
                
        full_reply = f"{answer}{citation_text}\n\n*Confidence: {confidence:.1%}*"
        history.append((user_message, full_reply))
    except Exception as e:
        history.append((user_message, f"❌ An error occurred during retrieval: {str(e)}"))
        
    return "", history

def clear_all_history():
    return []

# Custom CSS for modern dark UI
custom_css = """
.gradio-container {
    max-width: 1100px !important;
    margin: auto !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
#chat-box {
    min-height: 480px !important;
}
"""

with gr.Blocks(title="RAGify — Intelligent Document RAG Chatbot", theme=gr.themes.Soft(primary_hue="indigo"), css=custom_css) as demo:
    gr.Markdown("""
    # 🤖 RAGify — Intelligent Document RAG Chatbot
    ### Real Multi-Document Retrieval-Augmented Generation (Hybrid Dense + Sparse BM25 + Cross-Encoder Reranker)
    """)
    
    with gr.Row():
        with gr.Column(scale=4):
            gr.Markdown("### 📄 Document Knowledge Base")
            file_uploader = gr.File(
                label="Upload Documents (PDF, DOCX, TXT)",
                file_count="multiple",
                file_types=[".pdf", ".docx", ".txt"]
            )
            upload_btn = gr.Button("⚡ Process & Index Documents", variant="primary")
            upload_status = gr.Textbox(label="Ingestion Logs", lines=3, interactive=False)
            doc_list_display = gr.Textbox(
                label="Currently Indexed Documents",
                value="\n".join(uploaded_docs_list) if uploaded_docs_list else "No documents uploaded yet.",
                lines=4,
                interactive=False
            )
            
        with gr.Column(scale=6):
            gr.Markdown("### 💬 Ask Questions About Uploaded Documents")
            chatbot = gr.Chatbot(
                label="RAG Assistant (with Citations)",
                elem_id="chat-box",
                height=480,
                show_copy_button=True
            )
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ask a question about your documents...",
                    show_label=False,
                    scale=8
                )
                send_btn = gr.Button("Send", variant="primary", scale=2)
                
            clear_btn = gr.Button("Clear Chat History", variant="secondary")

    # Wire up events
    upload_btn.click(
        fn=upload_and_index,
        inputs=[file_uploader],
        outputs=[upload_status, doc_list_display]
    )
    
    send_btn.click(
        fn=chat_respond,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot]
    )
    
    msg_input.submit(
        fn=chat_respond,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot]
    )
    
    clear_btn.click(fn=clear_all_history, inputs=[], outputs=[chatbot])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
