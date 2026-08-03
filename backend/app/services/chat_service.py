import anyio
import time
from typing import List, Dict, Any
from app.models.chat import ChatRequest, ChatResponse
from app.database.connection import supabase_db
from app.utils.logger import logger
from app.config import settings
from app.rag.retriever import retrieve

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama

class ChatService:
    """
    Service layer handling conversation state, persistence, RAG context retrieval,
    and LLM inference orchestrations.
    """
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Processes a chat request:
        1. Saves the user's message to Supabase.
        2. Routes the query to one of three skills:
           - Skill 2: Ship30 social media posts/articles (No RAG)
           - Skill 3: Code and document Artifact generation (No RAG)
           - Skill 1: Standard RAG transcript queries (Keeps transcript QA flow intact)
        3. Invokes the selected LLM provider.
        4. Saves assistant response and returns output with metadata.
        """
        logger.info(f"Processing chat request. Session: {request.session_id} | Provider: {request.provider}")

        # Save user's message to Supabase (automatically creates session if missing)
        await anyio.to_thread.run_sync(
            supabase_db.save_message,
            request.session_id,
            "user",
            request.message,
            request.provider
        )

        msg_lower = request.message.lower()

        # Skill 2 triggers: ship30, essay, linkedin post, twitter thread, write an article, blog
        ship30_keywords = ["ship30", "essay", "linkedin post", "twitter thread", "write an article", "blog"]
        
        # Skill 3 triggers: html, css, javascript, markdown, prd, readme, landing page, website, component, code, artifact
        artifact_keywords = [
            "html", "css", "javascript", "markdown", "prd", "readme", 
            "landing page", "website", "component", "code", "artifact"
        ]

        # Classification Routing
        if any(kw in msg_lower for kw in ship30_keywords):
            # Skill 2 - Ship30 Writer (No transcript retrieval)
            logger.info("Routing query to Skill 2 (Ship30 Writer)")
            chunks = []
            prompt = f"""You are a master digital writer specializing in the "Ship 30 for 30" writing framework.
Generate a structured, highly engaging long-form article or social media piece on the user's topic.

Strict formatting and style guidelines:
1. Hook: Open with a single, highly engaging sentence or question.
2. Bold Formatting: Bold key ideas, phrases, and metrics throughout the text to make it extremely skimmable.
3. Structure: Use short paragraphs (1-3 sentences) and bullet points.
4. Examples: Provide realistic examples or case studies.
5. Key Takeaway: End with a clear, bolded actionable takeaway.

User Request: {request.message}"""
            skill_type = "ship30"

        elif any(kw in msg_lower for kw in artifact_keywords):
            # Skill 3 - Artifact Generator (No transcript retrieval)
            logger.info("Routing query to Skill 3 (Artifact Generator)")
            chunks = []
            prompt = f"""You are an expert developer and technical writer.
Generate the requested document or code artifact directly. 

You must wrap the code or document inside a single appropriate markdown code block (e.g. ```html ... ``` or ```markdown ... ```). Do not put any conversational text before or after the code block.

User Request: {request.message}"""
            skill_type = "artifact"

        else:
            # Skill 1 - Transcript QA (Default RAG flow)
            logger.info("Routing query to Skill 1 (Transcript QA)")
            start_retrieval_time = time.perf_counter()
            try:
                chunks = await anyio.to_thread.run_sync(retrieve, request.message, 5)
            except Exception as e:
                logger.error(f"Failed to retrieve context chunks from ChromaDB: {e}")
                chunks = []
            retrieval_duration = time.perf_counter() - start_retrieval_time
            logger.info(
                f"ChromaDB retrieval completed. Chunks returned: {len(chunks)} | "
                f"Duration: {retrieval_duration:.4f}s | Provider: {request.provider}"
            )

            if chunks:
                context_blocks = []
                for i, chunk in enumerate(chunks):
                    meta = chunk.get("metadata", {})
                    source = meta.get("source_path", "unknown")
                    guest = meta.get("guest", "unknown")
                    title = meta.get("title", "unknown")
                    context_blocks.append(
                        f"[Chunk {i+1}] Source: {source} | Guest: {guest} | Title: {title}\n"
                        f"{chunk.get('page_content', '')}"
                    )
                context_str = "\n\n".join(context_blocks)
            else:
                context_str = "[No matching context found in transcripts database.]"

            prompt = f"""You are Lenny Growth Assistant.

Answer ONLY using the transcript context below.

If the answer cannot be found in the transcript context,
say:

"I couldn't find that information in the indexed Lenny Podcast transcripts."

Never invent facts.

Transcript Context:

{context_str}

User Question:

{request.message}"""
            skill_type = "transcript_qa"

        # 4. Initialize the requested LLM provider model
        try:
            if request.provider == "openai":
                if not settings.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY is not configured in environment settings.")
                llm = ChatOpenAI(
                    model="gpt-4o",
                    openai_api_key=settings.OPENAI_API_KEY,
                    temperature=0.0
                )
            elif request.provider == "anthropic":
                if not settings.ANTHROPIC_API_KEY:
                    raise ValueError("ANTHROPIC_API_KEY is not configured in environment settings.")
                llm = ChatAnthropic(
                    model="claude-3-5-sonnet-20240620",
                    anthropic_api_key=settings.ANTHROPIC_API_KEY,
                    temperature=0.0
                )
            elif request.provider == "ollama":
                llm = ChatOllama(
                    model="llama3.2:latest",
                    base_url=settings.OLLAMA_HOST,
                    temperature=0.0
                )
            else:
                raise ValueError(f"Unsupported LLM provider requested: {request.provider}")

            # 5. Invoke LLM asynchronously
            logger.info(f"Invoking LLM provider '{request.provider}' for skill '{skill_type}'...")
            llm_response = await llm.ainvoke(prompt)
            answer = llm_response.content
        except Exception as e:
            logger.error(f"Error during LLM inference: {e}")
            answer = f"Error communicating with LLM provider ({request.provider}): {str(e)}"

        # 6. Save assistant's response message to Supabase
        await anyio.to_thread.run_sync(
            supabase_db.save_message,
            request.session_id,
            "assistant",
            answer,
            request.provider
        )

        # Parse artifact metadata if Skill 3 or if answer contains code block
        resp_type = None
        resp_lang = None
        resp_content = None

        if skill_type == "artifact" or "```" in answer:
            import re
            match = re.search(r"```([a-zA-Z0-9+#-]+)\n([\s\S]*?)```", answer)
            if match:
                resp_type = "artifact"
                resp_lang = match.group(1).lower()
                resp_content = match.group(2).strip()
            elif answer.strip().startswith("<!DOCTYPE") or "<html>" in answer:
                resp_type = "artifact"
                resp_lang = "html"
                resp_content = answer.strip()
            elif answer.strip().startswith("#"):
                resp_type = "artifact"
                resp_lang = "markdown"
                resp_content = answer.strip()

        # 7. Return detailed response mapping the API contracts
        return ChatResponse(
            response=answer,
            answer=answer,
            retrieved_sources=chunks,
            session_id=request.session_id,
            type=resp_type,
            language=resp_lang,
            content=resp_content
        )


# Shared chat service instance
chat_service = ChatService()

