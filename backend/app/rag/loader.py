import os
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document
from app.utils.logger import logger
from app.config import settings

class TranscriptLoader:
    """
    Recursively loads markdown transcript files and extracts contents and metadata.
    """
    def __init__(self, transcripts_dir: str):
        self.transcripts_dir = Path(transcripts_dir)

    def load(self) -> List[Document]:
        """
        Recursively scans the transcripts directory for .md files,
        reads them, and returns a list of LangChain Document objects with metadata.
        """
        documents = []
        if not self.transcripts_dir.exists():
            logger.error(f"Transcripts directory does not exist: {self.transcripts_dir}")
            return []

        # Find all markdown files recursively
        raw_md_files = list(self.transcripts_dir.glob("**/*.md"))
        
        # Sort alphabetically for deterministic indexing
        md_files = sorted(raw_md_files, key=lambda p: str(p.relative_to(self.transcripts_dir)))
        
        total_found = len(md_files)
        
        # DEMO_MODE: Limiting the number of transcripts processed reduces local vector database indexing time.
        # Set settings.MAX_TRANSCRIPTS = None or 0 to index the full repository.
        max_limit = settings.MAX_TRANSCRIPTS
        if max_limit and max_limit > 0:
            md_files = md_files[:max_limit]

        logger.info(f"Total transcript files found: {total_found}")
        logger.info(f"Number of transcript files actually being indexed: {len(md_files)}")


        for filepath in md_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract title and guest name from header or filename
                metadata = self._extract_metadata(filepath, content)
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
            except Exception as e:
                logger.error(f"Error loading transcript file {filepath}: {e}")

        return documents

    def _extract_metadata(self, filepath: Path, content: str) -> Dict[str, Any]:
        """
        Extracts metadata such as guest, title, and source path from content or filename.
        """
        filename = filepath.stem
        source_path = str(filepath.relative_to(self.transcripts_dir.parent.parent))

        # Default values
        guest = "Unknown"
        title = filename.replace("-", " ").replace("_", " ").title()

        # Try to parse the first heading in the file
        lines = content.split("\n")
        first_heading = ""
        for line in lines[:10]:  # Look at first 10 lines
            if line.startswith("#"):
                first_heading = line.lstrip("#").strip()
                break

        if first_heading:
            # Common patterns: "Guest Name: Title" or "Episode X - Guest Name" or "Guest Name (Company)"
            if ":" in first_heading:
                parts = first_heading.split(":", 1)
                guest = parts[0].strip()
                title = parts[1].strip()
            elif " - " in first_heading:
                parts = first_heading.split(" - ", 1)
                # If there's an episode number, e.g. "Episode 100 - Guest Name"
                if "episode" in parts[0].lower():
                    guest = parts[1].strip()
                    title = first_heading
                else:
                    guest = parts[0].strip()
                    title = parts[1].strip()
            else:
                title = first_heading
                # Try to guess guest from title
                guest = first_heading.split(" ")[0]  # simple fallback

        # If guest remains unknown, try parsing filename (e.g. "shreyas-doshi-on-product-management")
        if guest == "Unknown":
            name_parts = filename.split("-")
            if len(name_parts) >= 2:
                # Capitalize first two parts as guest name
                guest = f"{name_parts[0]} {name_parts[1]}".title()

        return {
            "guest": guest,
            "title": title,
            "source_path": source_path,
        }
