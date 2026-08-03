# Product Requirements Document (PRD)

## Project: Lenny Growth Assistant

---

## 1. Problem Statement
Product managers, founders, and growth marketers struggle to find relevant, actionable advice on user acquisition, onboarding loops, conversion rates, and retention strategies. While sources like *Lenny's Newsletter* and *Lenny's Podcast* contain answers, searching through hours of audio transcripts and lengthy articles is slow and inefficient. Existing generic LLM bots often invent strategies or lack access to specific, validated frameworks (e.g., specific case studies mentioned by guests). 

There is a critical need for an AI-powered conversational tool that:
*   Restricts its knowledge base to validated growth frameworks from the transcripts.
*   Presents answers in structured, skimmable digital styles.
*   Renders interactive markdown reports and HTML calculation tools side-by-side with conversation streams.

---

## 2. Target Users & Personas
*   **Early-Stage Founder (Alex):** Wants to calculate benchmark conversion funnel targets, outline early acquisition loops, and reference case studies of relevant startups.
*   **Growth Product Manager (Sarah):** Needs to draft A/B testing experiment templates or run onboarding calculations. Uses the output to share strategies with engineering and design teams.
*   **Digital Content Creator/Writer (Marcus):** Wants to summarize complex strategies into atomic, skimmable, bolded formats (like Ship30 writing framework) for twitter threads or blog posts.

---

## 3. Goals & Objectives
*   **Provide Citation-Backed Answers:** Deliver accurate insights where every response is derived directly from podcast context chunks with source transparency.
*   **Sleek Workspace Rendering:** Isolate code artifacts, tables, and documents into a separate panel to keep chat feeds readable.
*   **Dynamic Local Processing:** Maintain high privacy standards and support local developer testing through offline-capable local embeddings and inference options.

---

## 4. Feature Specifications

### 4.1 Hybrid RAG Pipeline
*   **ETL Pipeline:** Clones podcast transcripts, cleans the Markdown headers, and splits files using `RecursiveCharacterTextSplitter` (chunk size: 1000, overlap: 200).
*   **Vector Database:** Persists embeddings locally using ChromaDB. Deduplicates chunks on ingestion by hashing relative source paths and chunk offsets.
*   **Vector Retrieval:** Returns the 5 most relevant segments for user prompts.

### 4.2 Split Workspace & Claude-Style Artifact Viewer
*   **Double-Panel UI:** Left panel holds the sidebar history and chat box. Right panel opens dynamically when code, HTML, or Markdown document code blocks are generated.
*   **Sandboxed HTML Rendering:** Executes HTML/JS within a sandboxed `iframe` wrapper with script isolation.
*   **Markdown Processor:** Parses markdown headers, tables, and list hierarchies using `react-markdown`.
*   **Download Actions:** Exposes file download options to extract generated templates directly.

### 4.3 LLM Routing & Prompt Customization
*   **Multi-Provider Selection:** Chip interface allows toggling between `openai` (GPT-4o), `anthropic` (Claude 3.5), and local `ollama` (`llama3.2`).
*   **Ship30 Writing Skill:** Intercepts message keywords (e.g., `"ship30"`, `"essay"`, `"twitter thread"`, `"long-form post"`). Switches prompt instructions to generate atomic essays of 1200-1300 words with bolded skimmability markers, engaging hooks, lists, and takeaway summaries.

---

## 5. System Constraints & Tech Stack
*   **Backend:** FastAPI (Python 3.12) utilizing asynchronous endpoints.
*   **Frontend:** React (Vite, TypeScript, TailwindCSS v4).
*   **Database:** Supabase Client wrapper for chat logging.
*   **Vector Database:** Local ChromaDB Persistent Client.
*   **LLM Orchestrator:** LangChain with ChatOpenAI, ChatAnthropic, and ChatOllama interfaces.
*   **Embeddings:** Ollama local `nomic-embed-text:latest` model.

---

## 6. Acceptance Criteria

| Feature | Acceptance Criteria |
| :--- | :--- |
| **System Boot** | Dev servers start up cleanly. Client queries proxy back to port 8000. |
| **Data Ingestion** | Ingestion pipeline creates local directory, processes markdown transcripts, hashes IDs, skips duplicates, and populates vector index. |
| **Database Sync** | Sessions are retrieved on client mount. Messages are logged with role, model used, and session association. If session ID doesn't exist, it is created. |
| **Artifact Activation** | Any message containing HTML or markdown block code triggers the Right Panel slide-out, displaying preview/code tabs. Normal chats hide the panel automatically. |
| **Ship30 Skill** | Requests containing Ship30 keywords trigger the long-form (1200-1300 words) template, rendering bolded text blocks and hooks. |
