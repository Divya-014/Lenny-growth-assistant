from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import OllamaEmbeddings
from app.config import settings
from app.utils.logger import logger

class TranscriptEmbedder:
    """
    Manages embedding model resolution.
    Uses Local Ollama (nomic-embed-text) exclusively.
    """
    @staticmethod
    def get_embedding_model() -> Embeddings:
        """
        Initializes and returns the Ollama embedding model.
        """
        logger.info(f"Initializing Ollama embeddings (nomic-embed-text) at: {settings.OLLAMA_HOST}")
        return OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=settings.OLLAMA_HOST
        )
