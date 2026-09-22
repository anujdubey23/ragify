import os
import glob
from backend.app.rag.pipeline import rag_pipeline
from backend.app.database.database import SessionLocal, init_db
from backend.app.database.repository import DocumentRepository

def ingest_samples():
    init_db()
    db = SessionLocal()
    repo = DocumentRepository(db)
    
    docs_dir = os.path.join(os.path.dirname(__file__), "sample_documents")
    files = glob.glob(os.path.join(docs_dir, "*.pdf"))
    
    for fpath in files:
        fname = os.path.basename(fpath)
        doc_id = f"sample_{fname.split('.')[0]}"
        
        # Check if already exists
        existing = repo.get_by_id(doc_id)
        if existing:
            print(f"Skipping {fname} (already indexed)")
            continue
            
        print(f"Ingesting {fname}...")
        file_size = os.path.getsize(fpath)
        repo.create(doc_id=doc_id, filename=fname, file_type="pdf", file_size=file_size, file_path=fpath)
        
        chunks = rag_pipeline.ingest_document(fpath, fname, doc_id)
        repo.save_chunks(chunks)
        repo.update_status(doc_id, "indexed", chunk_count=len(chunks))
        print(f"  Indexed {len(chunks)} chunks for {fname}")
        
    db.close()
    print("All sample documents ingested successfully!")

if __name__ == "__main__":
    ingest_samples()
