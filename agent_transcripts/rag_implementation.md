# Agent Session Log: RAG Implementation

**Date:** 2026-08-02  
**Speaker:** AI Coding Assistant (Antigravity)  
**Task:** Build the loader, splitter, retriever, and ingestion pipeline modules for RAG integration.

---

### 1. Document Loading & Parsing (`loader.py`)
Scans directories recursively for markdown transcript files.
*   **Metadata Harvesting:** Designed to extract `guest`, `title`, and `source_path` attributes for contextual transparency.
*   **Fallback Structure:** Attempts to read the first markdown header (`# Guest Name: Episode Title`). If missing, it extracts name tokens from the file names (e.g., `guest-name.md` -> `Guest Name`).

---

### 2. Character Splitting (`splitter.py`)
Uses LangChain's `RecursiveCharacterTextSplitter` configured for digital content chunking:
*   `chunk_size = 1000` (aims to capture logical paragraphs)
*   `chunk_overlap = 200` (preserves contextual continuity across borders)
*   **Chunk IDs:** Injects a zero-indexed `chunk_number` value into each split segment's metadata dictionary.

---

### 3. Deduplicated Ingestion (`ingest.py`)
To prevent the script from uploading duplicate vectors to ChromaDB on multiple runs, we implemented an ID check mechanism:
1.  Generate a deterministic unique ID for each split segment using SHA-256:
    ```python
    def generate_chunk_id(source_path: str, chunk_number: int) -> str:
        input_str = f"{source_path}_chunk_{chunk_number}"
        return hashlib.sha256(input_str.encode("utf-8")).hexdigest()
    ```
2.  Batch query ChromaDB with target IDs before inserting:
    ```python
    existing = vectorstore.get(ids=batch_ids, include=[])
    existing_ids = set(existing.get("ids", []))
    # Filter out existing IDs to prevent duplicates
    chunks_to_insert = [c for c, cid in zip(batch, batch_ids) if cid not in existing_ids]
    ```
3.  Inserts only the missing chunks, saving disk writes and network traffic.

---

### 4. Chat Pipeline Integration (`chat_service.py`)
Integrates the RAG retriever with chat query endpoints:
1.  **Retrieve:** Queries ChromaDB for the top 5 relevant transcript segments matching the user question.
2.  **Context Construction:** Formats references dynamically:
    ```text
    [Chunk 1] Source: episode_1.md | Guest: Shreyas Doshi | Title: Product Strategy
    <text content>
    ```
3.  **Prompt Building:** Enforces strict instructions:
    *   Answer ONLY using the provided transcript context.
    *   Do not invent facts or extrapolate beyond provided materials.
    *   Fallback text: `"I couldn't find that information in the indexed Lenny Podcast transcripts."`
4.  **Logging Metrics:** Logs the query performance details (retrieval time duration, count of retrieved chunks, and model provider used).
5.  **Supabase Logs:** Persists final answers and session records.
