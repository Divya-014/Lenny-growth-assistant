# Agent Session Log: Failed Attempts

**Date:** 2026-08-02  
**Speaker:** AI Coding Assistant (Antigravity)  
**Task:** Identify and review failed execution paths, traceback analysis, and their recovery actions.

---

### 1. The File Lock & Package Installation Lockout
*   **Incident:** We attempted to run a bulk update of the virtual environment to install RAG packages (`sentence-transformers`, `torch`, `tqdm`).
*   **Error Output:**
    ```text
    ERROR: Could not install packages due to an OSError: [WinError 5] Access is denied: 'D:\\lenny-growth-assistant\\backend\\venv\\Lib\\site-packages\\~ebsockets\\speedups.cp310-win_amd64.pyd'
    ```
*   **Root Cause:** The `uvicorn` development server was actively running in the background of the user's terminal session, importing and locking the `websockets` library files.
*   **Recovery action:** Switched to a targeted `pip install` approach (`pip install sentence-transformers tqdm langchain-text-splitters`) that skipped modifying the locked `websockets` binaries, allowing dependencies to be set up without crashing the active server.

---

### 2. PyTorch DefaultCPUAllocator Memory Crash
*   **Incident:** Running the initial RAG pipeline ingestion script (`ingest.py`) with `sentence-transformers/all-MiniLM-L6-v2` locally.
*   **Error Output:**
    ```text
    File "D:\lenny-growth-assistant\backend\app\rag\ingest.py", line 117, in ingest_pipeline
        vectorstore.add_documents(documents=chunks_to_insert, ids=ids_to_insert)
    ...
    RuntimeError: [enforce fail at alloc_cpu.cpp:117] data. DefaultCPUAllocator: not enough memory: you tried to allocate 12582912 bytes.
    ```
*   **Root Cause:**
    1.  The podcast transcripts produced over 38,000 text chunks.
    2.  `sentence-transformers` loaded PyTorch, which by default spans threads across all CPU cores.
    3.  During large batch operations on the local machine, thread stacks and matrix variables caused heap memory exhaustion on the allocator.
*   **Recovery action:** Abandoned the resource-heavy local PyTorch runtime entirely, migrating to the optimized local **Ollama API** model (`nomic-embed-text`) which handles calculations asynchronously in a separate process.

---

### 3. SentenceTransformers Version 5.x Import ValueError
*   **Incident:** Loading HuggingFace embeddings via LangChain wrapper.
*   **Error Output:**
    ```text
    ValueError: Unrecognized processing class in sentence-transformers/all-MiniLM-L6-v2. Can't instantiate a processor, a tokenizer, an image processor, a video processor or a feature extractor for this model.
    ```
*   **Root Cause:** The environment loaded the latest 2026 packages (`sentence-transformers 5.6.1` and `transformers 5.14.1`). In these newer versions, the base class attempts to instantiate an `AutoProcessor` configuration. Standard text-only models like `all-MiniLM-L6-v2` do not possess preprocessor configurations, causing an instantiation crash inside Hugging Face.
*   **Recovery action:** Transitioned strictly to Ollama embeddings, removing `sentence-transformers` from `requirements.txt` to eliminate PyTorch loader version mismatches.
