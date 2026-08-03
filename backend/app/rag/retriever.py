from typing import List, Dict, Any
from app.rag.embedder import TranscriptEmbedder
from app.rag.vectordb import TranscriptVectorDB
from app.utils.logger import logger

_vectorstore = None

def get_cached_vectorstore():
    """
    Returns a cached instance of the persistent Chroma vectorstore to avoid connection overhead.
    """
    global _vectorstore
    if _vectorstore is None:
        logger.info("Initializing vectorstore connection singleton...")
        embeddings = TranscriptEmbedder.get_embedding_model()
        db = TranscriptVectorDB(embeddings)
        _vectorstore = db.get_vectorstore()
    return _vectorstore

def retrieve(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Finds and returns the top k relevant transcript chunks matching the query.
    
    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing 'page_content' and 'metadata'.
    """
    logger.info(f"RAG search query initiated: '{query}' (k={k})")
    try:
        # Get cached vector store
        vectorstore = get_cached_vectorstore()

        # Query vector store
        docs = vectorstore.similarity_search(query, k=k)
        
        # Serialize to standard dictionary records
        results = []
        for doc in docs:
            results.append({
                "page_content": doc.page_content,
                "metadata": doc.metadata
            })
            
        logger.info(f"Retrieved {len(results)} relevant chunks.")
        return results
    except Exception as e:
        logger.error(f"Error during RAG retrieval: {e}")
        return []

