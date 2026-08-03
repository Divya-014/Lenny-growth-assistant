import os
import sys
import subprocess
import hashlib
import time
from pathlib import Path
from typing import List
from tqdm import tqdm

# Add parent directory to path to ensure app modules can be imported
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.utils.logger import logger
from app.rag.loader import TranscriptLoader
from app.rag.splitter import TranscriptSplitter
from app.rag.embedder import TranscriptEmbedder
from app.rag.vectordb import TranscriptVectorDB
from langchain_core.documents import Document

def clone_transcripts_repo(dest_dir: Path):
    """
    Clones the lennys-podcast-transcripts repository if it doesn't already exist.
    """
    repo_url = "https://github.com/ChatPRD/lennys-podcast-transcripts"
    if dest_dir.exists() and any(dest_dir.iterdir()):
        logger.info(f"Transcripts directory already exists and is not empty: {dest_dir}")
        return

    logger.info(f"Cloning transcripts from {repo_url} into {dest_dir}...")
    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["git", "clone", repo_url, str(dest_dir)], check=True)
        logger.info("Successfully cloned transcripts repository.")
    except Exception as e:
        logger.error(f"Failed to clone transcripts repository: {e}")
        logger.error("Please ensure git is installed and reachable from your shell command line.")
        raise e

def generate_chunk_id(source_path: str, chunk_number: int) -> str:
    """
    Generates a deterministic unique ID for a chunk using SHA-256.
    """
    input_str = f"{source_path}_chunk_{chunk_number}"
    return hashlib.sha256(input_str.encode("utf-8")).hexdigest()

def ingest_pipeline():
    """
    Complete ETL ingestion pipeline:
    1. Downloads transcripts.
    2. Loads transcripts recursively.
    3. Splits text.
    4. Embeds & stores new chunks in ChromaDB.
    5. Displays progress and final stats.
    """
    # DEMO_MODE Note: Limiting transcripts reduces local vector indexing time. 
    # To index the full repository, set MAX_TRANSCRIPTS = None or 0 in app/config.py.
    logger.info("Starting RAG Ingestion Pipeline (DEMO_MODE)...")
    
    start_time = time.perf_counter()

    # 1. Resolve and clone repo
    dest_dir = Path("./data/lenny_transcripts").resolve()
    clone_transcripts_repo(dest_dir)

    # 2. Load Documents
    loader = TranscriptLoader(str(dest_dir))
    documents = loader.load()
    if not documents:
        logger.warning("No documents loaded. Exiting pipeline.")
        return

    # Display pre-ingestion statistics
    estimated_chunks = len(documents) * 97  # Average chunks count per transcript
    logger.info("=========================================")
    logger.info(f"Number of transcript files to process: {len(documents)}")
    logger.info(f"Estimated number of chunks to generate: {estimated_chunks}")
    logger.info("=========================================")

    # 3. Split Documents
    splitter = TranscriptSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    if not chunks:
        logger.warning("No chunks generated. Exiting pipeline.")
        return

    # 4. Resolve Embeddings and Vector DB
    embeddings = TranscriptEmbedder.get_embedding_model()
    db = TranscriptVectorDB(embeddings)
    vectorstore = db.get_vectorstore()

    # 5. Insert new chunks in batches, skipping duplicates
    batch_size = 100
    new_chunks_count = 0
    skipped_chunks_count = 0

    logger.info(f"Checking for duplicates and inserting {len(chunks)} chunks in batches of {batch_size}...")
    
    for i in tqdm(range(0, len(chunks), batch_size), desc="Ingesting batches"):
        batch = chunks[i : i + batch_size]
        
        # Generate ID for each chunk in the batch
        batch_ids = []
        for chunk in batch:
            source = chunk.metadata.get("source_path", "unknown")
            chunk_num = chunk.metadata.get("chunk_number", 0)
            batch_ids.append(generate_chunk_id(source, chunk_num))

        # Check which IDs already exist in Chroma
        try:
            existing = vectorstore.get(ids=batch_ids, include=[])
            existing_ids = set(existing.get("ids", []))
        except Exception as e:
            # If collection is empty or query fails, assume none exist
            logger.debug(f"Chroma DB query debug: {e}")
            existing_ids = set()

        # Filter out existing chunks
        chunks_to_insert = []
        ids_to_insert = []
        for chunk, cid in zip(batch, batch_ids):
            if cid not in existing_ids:
                chunks_to_insert.append(chunk)
                ids_to_insert.append(cid)
            else:
                skipped_chunks_count += 1

        # Batch insert new chunks
        if chunks_to_insert:
            vectorstore.add_documents(documents=chunks_to_insert, ids=ids_to_insert)
            new_chunks_count += len(chunks_to_insert)

    # 6. Display statistics
    total_ingestion_time = time.perf_counter() - start_time
    
    logger.info("=========================================")
    logger.info("RAG Ingestion Pipeline Completed Successfully!")
    logger.info(f"Total transcript files indexed: {len(documents)}")
    logger.info(f"Total chunks created: {len(chunks)}")
    logger.info(f"Total embeddings inserted: {new_chunks_count}")
    logger.info(f"Total duplicate chunks skipped: {skipped_chunks_count}")
    logger.info(f"Total ingestion time: {total_ingestion_time:.2f} seconds")
    logger.info("=========================================")

if __name__ == "__main__":
    ingest_pipeline()

