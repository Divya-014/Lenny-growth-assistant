import os
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from app.config import settings
from app.utils.logger import logger

class TranscriptVectorDB:
    """
    Handles connections to the local persistent ChromaDB instance.
    """
    def __init__(self, embedding_model: Embeddings):
        self.embedding_model = embedding_model
        self.persist_dir = Path(settings.CHROMADB_PATH).resolve()
        self.collection_name = "lenny_transcripts"
        self._ensure_persist_dir_exists()

    def _ensure_persist_dir_exists(self):
        """
        Ensures the persist directory exists before initializing ChromaDB.
        """
        if not self.persist_dir.exists():
            logger.info(f"ChromaDB persist directory '{self.persist_dir}' does not exist. Creating it.")
            os.makedirs(self.persist_dir, exist_ok=True)
        else:
            logger.debug(f"ChromaDB persist directory exists at '{self.persist_dir}'")

    def get_vectorstore(self) -> Chroma:
        """
        Instantiates and returns the persistent LangChain Chroma vectorstore.
        """
        logger.info(f"Connecting to persistent ChromaDB at: {self.persist_dir} (Collection: {self.collection_name})")
        return Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=str(self.persist_dir)
        )
