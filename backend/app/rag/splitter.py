from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.logger import logger

class TranscriptSplitter:
    """
    Splits loaded documents into standard chunk sizes and adds chunk indexing metadata.
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Splits a list of documents and injects chunk_number metadata into each chunk.
        """
        split_docs = []
        for doc in documents:
            # Split this specific document
            chunks = self.splitter.split_documents([doc])
            
            # Add chunk numbers to each chunk's metadata
            for idx, chunk in enumerate(chunks):
                chunk.metadata["chunk_number"] = idx
                split_docs.append(chunk)

        logger.info(f"Split {len(documents)} documents into {len(split_docs)} total chunks.")
        return split_docs
