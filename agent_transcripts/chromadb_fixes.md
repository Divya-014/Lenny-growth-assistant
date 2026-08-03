# Agent Session Log: ChromaDB Fixes

**Date:** 2026-08-02  
**Speaker:** AI Coding Assistant (Antigravity)  
**Task:** Establish local persistent ChromaDB client configurations and handle database cleanups.

---

### 1. Persistent Directory Initialization
*   **Challenge:** Ensure the local Chroma database is saved inside the workspace directories recursively without manual configuration.
*   **Resolution:** Configured `TranscriptVectorDB` to resolve the folder path from `settings.CHROMADB_PATH` and call `os.makedirs` if it doesn't exist:
    ```python
    def _ensure_persist_dir_exists(self):
        if not self.persist_dir.exists():
            os.makedirs(self.persist_dir, exist_ok=True)
    ```
    This ensures that database initialization doesn't throw a "Directory not found" error during the first runs of `ingest.py`.

---

### 2. Resolving Embedding Dimension Conflicts
*   **Incident:** We initially configured the RAG embedding layer using HuggingFace's `all-MiniLM-L6-v2` model, which generates **384-dimensional vectors**. Later, we refactored the embedding model to local Ollama `nomic-embed-text`, which outputs **768-dimensional vectors**.
*   **Error:** If we ran the ingestion script directly over the existing ChromaDB files, Chroma threw a database error:
    ```text
    InvalidDimensionException: Dimensionality of inputs (768) does not match the dimensionality of the index (384)
    ```
*   **Resolution:** Before executing the Ollama ingestion pipeline, we ran a cleanup command to erase the old 384-dimension directory:
    ```powershell
    Remove-Item -Recurse -Force data/chromadb
    ```
    Erasing the index directories allowed the script to instantiate a fresh, 768-dimension persistent collection matching the `nomic-embed-text` parameters.
