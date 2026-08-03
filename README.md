# Lenny Growth Assistant

An AI-powered growth assistant designed for Product Managers, startup founders, and growth marketers. It uses a Retrieval-Augmented Generation (RAG) pipeline over indexed Lenny's Podcast transcripts, querying local or cloud LLMs (OpenAI, Anthropic, or local Ollama), storing chat session logs in Supabase (PostgreSQL), and indexing vectors locally in ChromaDB.

It features a Claude-style Artifact Viewer which renders code, HTML pages, and markdown documents side-by-side with your chat feed.

---

## 📸 Interface Preview (Screenshot Placeholders)

*   **Chat View (Single Panel):** A clean, dark-mode messaging board layout for standard conversation queries.
    `![Chat Panel Mockup Placeholder](./docs/screenshots/chat_view.png)`
*   **Workspace Split View (Dual Panel):** The screen splits to reveal the Artifact Viewer on the right when generating documents or interactive HTML tools.
    `![Artifact split View Mockup Placeholder](./docs/screenshots/artifact_view.png)`

---

## 🛠️ Environment Variables Configuration

Create a file named `.env` in the `backend/` directory based on [**`backend/.env.example`**](file:///d:/lenny-growth-assistant/backend/.env.example):

```ini
# App Configs
APP_NAME="Lenny Growth Assistant"
APP_ENV=local
DEBUG=true
PORT=8000
HOST=0.0.0.0

# Database Integration (Supabase)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-service-key

# LLM Providers Configuration
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
OLLAMA_HOST=http://localhost:11434

# Vector DB Configuration
CHROMADB_PATH=./data/chromadb
```

---

## 🚀 Setup & Local Deployment Guide

### Prerequisites
*   Node.js (v18+)
*   Python (3.11 or 3.12)
*   Ollama (running locally with `llama3.2` and `nomic-embed-text` models)
*   Supabase account (Postgres DB)

---

### 1. Database Setup (Supabase)
Log in to your Supabase Project SQL Editor and execute the following DDL script to create the required tables:

```sql
-- 1. Chat Sessions Table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Chat Messages Table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    citations JSONB DEFAULT '[]'::jsonb,
    model_used VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

### 2. Local LLM Setup (Ollama)
Install Ollama, start the local server, and pull the required models:
```bash
# Pull model for local inference (llama3.2)
ollama pull llama3.2

# Pull model for RAG embeddings (nomic-embed-text)
ollama pull nomic-embed-text
```

---

### 3. Backend Deployment (FastAPI)
1.  Navigate to the `backend/` directory:
    ```bash
    cd backend
    ```
2.  Set up a virtual environment and install package dependencies:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  Ingest the podcast transcripts into local ChromaDB:
    ```bash
    python app/rag/ingest.py
    ```
4.  Launch the FastAPI server:
    ```bash
    uvicorn app.main:app --reload
    ```
    *Access the API Swagger documentation at `http://localhost:8000/docs`.*

---

### 4. Frontend Deployment (React)
1.  Navigate to the `frontend/` directory:
    ```bash
    cd ../frontend
    ```
2.  Install packages:
    ```bash
    npm install
    ```
3.  Launch the development server:
    ```bash
    npm run dev
    ```
    *Open `http://localhost:5173` in your browser. API requests are automatically proxied to the backend.*