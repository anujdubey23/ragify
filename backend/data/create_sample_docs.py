import os
import fitz

DOCS_DIR = os.path.join(os.path.dirname(__file__), "sample_documents")
os.makedirs(DOCS_DIR, exist_ok=True)

def create_transformer_pdf():
    doc = fitz.open()
    
    # Page 1
    p1 = doc.new_page()
    p1.insert_text((50, 70), "Attention Is All You Need — Architecture Overview", fontsize=14)
    p1.insert_text((50, 100), 
        "The Transformer is the first transduction model relying entirely on self-attention to compute \n"
        "representations of its input and output without using sequence-aligned RNNs or convolution. \n"
        "In the Transformer, multi-head self-attention allows the model to jointly attend to information \n"
        "from different representation subspaces at different positions.", fontsize=11)
    
    # Page 2
    p2 = doc.new_page()
    p2.insert_text((50, 70), "Attention Is All You Need — Encoder and Decoder Stacks", fontsize=14)
    p2.insert_text((50, 100),
        "The encoder is composed of a stack of N = 6 identical layers. Each layer has two sub-layers: \n"
        "a multi-head self-attention mechanism and a simple, position-wise fully connected feed-forward \n"
        "network. We employ residual connections around each of the two sub-layers, followed by layer \n"
        "normalization.", fontsize=11)

    pdf_path = os.path.join(DOCS_DIR, "Attention_Is_All_You_Need.pdf")
    doc.save(pdf_path)
    doc.close()
    print(f"Created {pdf_path}")

def create_deep_learning_pdf():
    doc = fitz.open()
    
    # Page 1
    p1 = doc.new_page()
    p1.insert_text((50, 70), "Deep Learning Basics & Backpropagation", fontsize=14)
    p1.insert_text((50, 100),
        "Artificial neural networks are trained using gradient descent optimization algorithms. \n"
        "Backpropagation calculates the gradient of the loss function with respect to each weight \n"
        "by applying the chain rule of calculus. The gradients propagate backwards through each layer \n"
        "to update connection weights.", fontsize=11)

    pdf_path = os.path.join(DOCS_DIR, "deep_learning_basics.pdf")
    doc.save(pdf_path)
    doc.close()
    print(f"Created {pdf_path}")

def create_rag_pdf():
    doc = fitz.open()
    
    # Page 1
    p1 = doc.new_page()
    p1.insert_text((50, 70), "Retrieval-Augmented Generation (RAG) System Design", fontsize=14)
    p1.insert_text((50, 100),
        "In a modern production RAG architecture, hybrid retrieval combines dense vector embeddings \n"
        "with sparse BM25 lexical token matching. Semantic search captures conceptual intent, \n"
        "whereas BM25 excels at exact keyword and acronym lookups. \n"
        "After hybrid retrieval produces candidate chunks, a cross-encoder reranker models full \n"
        "query-chunk attention to output the highest quality top-k context.", fontsize=11)

    pdf_path = os.path.join(DOCS_DIR, "rag_system_design.pdf")
    doc.save(pdf_path)
    doc.close()
    print(f"Created {pdf_path}")

if __name__ == "__main__":
    create_transformer_pdf()
    create_deep_learning_pdf()
    create_rag_pdf()
