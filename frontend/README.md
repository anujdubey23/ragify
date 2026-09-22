# RAGify Frontend

React + Vite + Tailwind CSS single-page web interface for **RAGify — Intelligent Document RAG Chatbot**.

## Setup & Running

```bash
# Install dependencies
npm install

# Run dev server on port 5173
npm run dev

# Build for production
npm run build
```

## Environment Variables
Create `.env` or `.env.production` if connecting to an external backend URL:
```ini
VITE_API_URL=http://localhost:8000
```
If `VITE_API_URL` is omitted, the Vite development proxy forwards `/api` and `/health` requests directly to `http://127.0.0.1:8000`.
