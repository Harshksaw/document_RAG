"""
Text chunking utilities for processing large documents.
"""
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter

class TextChunker:
    """
    Handles intelligent text chunking for large documents.
    """
    
    def __init__(self, chunk_size: int = 4000, chunk_overlap: int = 200):
        """
        Initialize text chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into manageable chunks.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        chunks = self.splitter.split_text(text)
        return chunks
    
    def get_first_n_pages(self, text: str, max_chars: int = 15000) -> str:
        """
        Extract first portion of document (useful for metadata).
        
        Args:
            text: Full document text
            max_chars: Maximum characters to extract
            
        Returns:
            First portion of text
        """
        return text[:max_chars]
    
    def chunk_by_pages(self, text: str, pages_per_chunk: int = 5) -> List[str]:
        """
        Split document by page markers if available.
        
        Args:
            text: Document text with page markers
            pages_per_chunk: Number of pages per chunk
            
        Returns:
            List of chunks grouped by pages
        """
        # Split by page markers (e.g., "--- Page 1 ---")
        pages = text.split("\n--- Page ")
        
        chunks = []
        current_chunk = ""
        page_count = 0
        
        for i, page in enumerate(pages):
            if i == 0 and not page.startswith("---"):
                # First element might be before first page marker
                current_chunk = page
                continue
            
            current_chunk += f"\n--- Page {page}"
            page_count += 1
            
            if page_count >= pages_per_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
                page_count = 0
        
        # Add remaining content
        if current_chunk.strip():
            chunks.append(current_chunk)
        
        return chunks


if __name__ == "__main__":
    # Example usage
    chunker = TextChunker(chunk_size=1000, chunk_overlap=100)
    
    sample_text = "Lorem ipsum " * 1000  # Large text
    chunks = chunker.chunk_text(sample_text)
    
    print(f"Original length: {len(sample_text)} characters")
    print(f"Number of chunks: {len(chunks)}")
    print(f"Average chunk size: {sum(len(c) for c in chunks) / len(chunks):.0f} chars")
