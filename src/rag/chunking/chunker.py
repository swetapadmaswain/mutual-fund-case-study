"""
Semantic chunking module for Phase 2.1 - Creating optimal chunks for vector storage.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib

from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError
from src.rag.chunking.document_processor import ProcessedDocument


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    chunk_index: int
    total_chunks: int
    token_count: int
    source_document_id: str
    chunk_type: str = "semantic"
    overlap_info: Optional[Dict[str, Any]] = None


class SemanticChunker:
    """Implements semantic chunking strategy for mutual fund documents."""
    
    def __init__(self, 
                 min_chunk_size: int = 500,
                 max_chunk_size: int = 800,
                 overlap_tokens: int = 200,
                 sentence_overlap: int = 2):
        """
        Initialize the semantic chunker.
        
        Args:
            min_chunk_size: Minimum chunk size in tokens
            max_chunk_size: Maximum chunk size in tokens
            overlap_tokens: Number of overlapping tokens between chunks
            sentence_overlap: Number of overlapping sentences
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_tokens = overlap_tokens
        self.sentence_overlap = sentence_overlap
        
        # Financial context indicators
        self.context_indicators = [
            'expense ratio', 'exit load', 'nav', 'sip', 'aum',
            'risk level', 'benchmark', 'investment objective',
            'fund performance', 'portfolio composition', 'allocation'
        ]
        
        # Sentence patterns for splitting
        self.sentence_patterns = [
            r'(?<=[.!?])\s+',  # Standard sentence endings
            r'(?<=[;])\s+',    # Semicolons
            r'(?<=[:])\s+',     # Colons
        ]
        
        logger.info(f"Initialized SemanticChunker with min_size={min_chunk_size}, "
                   f"max_size={max_chunk_size}, overlap={overlap_tokens}")
    
    def create_chunks(self, document: ProcessedDocument) -> List[Chunk]:
        """
        Create semantic chunks from a processed document.
        
        Args:
            document: ProcessedDocument to chunk
            
        Returns:
            List of Chunk objects
        """
        logger.info(f"Creating chunks for document: {document.metadata.get('fund_name', 'Unknown')}")
        
        content = document.cleaned_content
        if not content:
            logger.warning("Document has no content to chunk")
            return []
        
        # Step 1: Split into sentences
        sentences = self._split_into_sentences(content)
        logger.debug(f"Split content into {len(sentences)} sentences")
        
        # Step 2: Group sentences into semantic chunks
        initial_chunks = self._create_initial_chunks(sentences)
        logger.debug(f"Created {len(initial_chunks)} initial chunks")
        
        # Step 3: Optimize chunk sizes
        optimized_chunks = self._optimize_chunk_sizes(initial_chunks)
        logger.debug(f"Optimized to {len(optimized_chunks)} chunks")
        
        # Step 4: Add overlap between chunks
        chunks_with_overlap = self._add_overlap(optimized_chunks)
        logger.debug(f"Added overlap to chunks")
        
        # Step 5: Create Chunk objects with metadata
        final_chunks = self._create_chunk_objects(chunks_with_overlap, document)
        logger.info(f"Created {len(final_chunks)} final chunks")
        
        return final_chunks
    
    def _split_into_sentences(self, content: str) -> List[str]:
        """Split content into sentences using multiple patterns."""
        sentences = []
        
        # Try each sentence pattern
        for pattern in self.sentence_patterns:
            if re.search(pattern, content):
                sentences = re.split(pattern, content)
                break
        
        # If no patterns matched, split on newlines
        if not sentences or len(sentences) == 1:
            sentences = content.split('\n')
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Filter very short fragments
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _create_initial_chunks(self, sentences: List[str]) -> List[List[str]]:
        """Create initial chunks by grouping sentences."""
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self._estimate_tokens(sentence)
            
            # Check if adding this sentence would exceed max chunk size
            if current_tokens + sentence_tokens > self.max_chunk_size and current_chunk:
                # Save current chunk and start new one
                chunks.append(current_chunk)
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _optimize_chunk_sizes(self, chunks: List[List[str]]) -> List[List[str]]:
        """Optimize chunk sizes to be within target range."""
        optimized = []
        
        for chunk in chunks:
            chunk_text = ' '.join(chunk)
            chunk_tokens = self._estimate_tokens(chunk_text)
            
            # Handle chunks that are too small
            if chunk_tokens < self.min_chunk_size:
                if optimized:
                    # Try to merge with previous chunk
                    last_chunk = optimized[-1]
                    last_text = ' '.join(last_chunk)
                    combined_tokens = self._estimate_tokens(last_text + ' ' + chunk_text)
                    
                    if combined_tokens <= self.max_chunk_size:
                        # Merge with previous chunk
                        optimized[-1].extend(chunk)
                        continue
                    else:
                        # Keep as separate small chunk
                        optimized.append(chunk)
                else:
                    # First chunk, keep it
                    optimized.append(chunk)
            
            # Handle chunks that are too large
            elif chunk_tokens > self.max_chunk_size:
                # Split the oversized chunk
                split_chunks = self._split_oversized_chunk(chunk)
                optimized.extend(split_chunks)
            
            # Chunk is within acceptable range
            else:
                optimized.append(chunk)
        
        return optimized
    
    def _split_oversized_chunk(self, chunk: List[str]) -> List[List[str]]:
        """Split an oversized chunk into smaller chunks."""
        oversized_chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in chunk:
            sentence_tokens = self._estimate_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.max_chunk_size and current_chunk:
                oversized_chunks.append(current_chunk)
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        if current_chunk:
            oversized_chunks.append(current_chunk)
        
        return oversized_chunks
    
    def _add_overlap(self, chunks: List[List[str]]) -> List[List[str]]:
        """Add overlapping content between chunks."""
        if len(chunks) <= 1:
            return chunks
        
        chunks_with_overlap = []
        
        for i, chunk in enumerate(chunks):
            overlap_chunk = chunk.copy()
            
            # Add overlap from previous chunk (except for first chunk)
            if i > 0:
                prev_chunk = chunks[i - 1]
                overlap_sentences = prev_chunk[-self.sentence_overlap:]
                overlap_chunk = overlap_sentences + overlap_chunk
            
            # Add overlap from next chunk (except for last chunk)
            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                overlap_sentences = next_chunk[:self.sentence_overlap]
                overlap_chunk.extend(overlap_sentences)
            
            chunks_with_overlap.append(overlap_chunk)
        
        return chunks_with_overlap
    
    def _create_chunk_objects(self, 
                            chunk_contents: List[List[str]], 
                            document: ProcessedDocument) -> List[Chunk]:
        """Create Chunk objects with metadata."""
        chunks = []
        doc_id = document.content_hash
        
        for i, chunk_sentences in enumerate(chunk_contents):
            chunk_text = ' '.join(chunk_sentences)
            chunk_id = self._generate_chunk_id(doc_id, i)
            
            # Estimate token count
            token_count = self._estimate_tokens(chunk_text)
            
            # Create chunk metadata
            chunk_metadata = document.metadata.copy()
            chunk_metadata.update({
                'chunk_id': chunk_id,
                'chunk_index': i,
                'total_chunks': len(chunk_contents),
                'token_count': token_count,
                'sentence_count': len(chunk_sentences),
                'has_financial_context': self._has_financial_context(chunk_text),
                'context_indicators': self._extract_context_indicators(chunk_text)
            })
            
            # Create overlap info
            overlap_info = None
            if i > 0 or i < len(chunk_contents) - 1:
                overlap_info = self._create_overlap_info(i, len(chunk_contents))
            
            chunk = Chunk(
                chunk_id=chunk_id,
                content=chunk_text,
                metadata=chunk_metadata,
                chunk_index=i,
                total_chunks=len(chunk_contents),
                token_count=token_count,
                source_document_id=doc_id,
                chunk_type="semantic",
                overlap_info=overlap_info
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Simple token estimation: words + punctuation + special chars
        words = len(text.split())
        # Add some tokens for punctuation and special characters
        special_chars = len(re.findall(r'[^\w\s]', text))
        return words + special_chars // 2
    
    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """Generate unique chunk ID."""
        content = f"{document_id}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _has_financial_context(self, text: str) -> bool:
        """Check if chunk contains financial context."""
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in self.context_indicators)
    
    def _extract_context_indicators(self, text: str) -> List[str]:
        """Extract context indicators present in chunk."""
        text_lower = text.lower()
        found_indicators = []
        for indicator in self.context_indicators:
            if indicator in text_lower:
                found_indicators.append(indicator)
        return found_indicators
    
    def _create_overlap_info(self, chunk_index: int, total_chunks: int) -> Dict[str, Any]:
        """Create overlap information for chunk."""
        overlap_info = {
            'has_previous_overlap': chunk_index > 0,
            'has_next_overlap': chunk_index < total_chunks - 1,
            'overlap_sentences': self.sentence_overlap
        }
        
        if chunk_index > 0:
            overlap_info['previous_chunk_index'] = chunk_index - 1
        
        if chunk_index < total_chunks - 1:
            overlap_info['next_chunk_index'] = chunk_index + 1
        
        return overlap_info
    
    def handle_tables(self, content: str) -> List[str]:
        """
        Special handling for tabular data in content.
        
        Args:
            content: Text content potentially containing tables
            
        Returns:
            List of table chunks
        """
        table_chunks = []
        
        # Look for table patterns
        table_patterns = [
            r'(?s)(Fund\s+Name.*?NAV.*?)(?=\n\n|\Z)',
            r'(?s)(Scheme\s+Information.*?)(?=\n\n|\Z)',
            r'(?s)(Portfolio.*?Allocation.*?)(?=\n\n|\Z)'
        ]
        
        for pattern in table_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) > 50:  # Filter very short matches
                    table_chunks.append(match.strip())
        
        return table_chunks
    
    def preserve_context(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Ensure context preservation across chunks.
        
        Args:
            chunks: List of chunks to preserve context for
            
        Returns:
            Chunks with preserved context
        """
        for i, chunk in enumerate(chunks):
            # Add context metadata
            context_metadata = {
                'context_preserved': True,
                'related_chunks': [],
                'context_type': 'semantic'
            }
            
            # Identify related chunks based on content similarity
            for j, other_chunk in enumerate(chunks):
                if i != j:
                    similarity = self._calculate_content_similarity(chunk.content, other_chunk.content)
                    if similarity > 0.3:  # Threshold for related chunks
                        context_metadata['related_chunks'].append({
                            'chunk_id': other_chunk.chunk_id,
                            'similarity': similarity
                        })
            
            # Update chunk metadata
            chunk.metadata.update(context_metadata)
        
        return chunks
    
    def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple content similarity between two texts."""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def optimize_chunk_size(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Optimize chunk sizes for better retrieval performance.
        
        Args:
            chunks: List of chunks to optimize
            
        Returns:
            Optimized chunks
        """
        optimized = []
        
        for chunk in chunks:
            # Check if chunk needs optimization
            if chunk.token_count < self.min_chunk_size:
                logger.debug(f"Chunk {chunk.chunk_id} is too small: {chunk.token_count} tokens")
                # Mark for potential merging (handled at higher level)
                chunk.metadata['size_optimization'] = 'too_small'
            
            elif chunk.token_count > self.max_chunk_size:
                logger.debug(f"Chunk {chunk.chunk_id} is too large: {chunk.token_count} tokens")
                # Mark for potential splitting (handled at higher level)
                chunk.metadata['size_optimization'] = 'too_large'
            
            else:
                chunk.metadata['size_optimization'] = 'optimal'
            
            optimized.append(chunk)
        
        return optimized


class ChunkingPipeline:
    """Main chunking pipeline for Phase 2.1."""
    
    def __init__(self, chunker: Optional[SemanticChunker] = None):
        """Initialize the chunking pipeline."""
        self.chunker = chunker or SemanticChunker()
        self.processed_chunks: List[Chunk] = []
    
    def process_documents(self, documents: List[ProcessedDocument]) -> List[Chunk]:
        """
        Process multiple documents into chunks.
        
        Args:
            documents: List of processed documents
            
        Returns:
            List of all chunks
        """
        logger.info(f"Starting chunking pipeline for {len(documents)} documents")
        
        all_chunks = []
        chunking_stats = {
            'total_documents': len(documents),
            'total_chunks': 0,
            'avg_chunks_per_document': 0,
            'avg_chunk_size': 0,
            'chunks_with_financial_context': 0,
            'size_optimization_stats': {}
        }
        
        for i, document in enumerate(documents):
            try:
                logger.info(f"Processing document {i+1}/{len(documents)}: "
                           f"{document.metadata.get('fund_name', 'Unknown')}")
                
                # Create chunks for this document
                chunks = self.chunker.create_chunks(document)
                
                # Preserve context across chunks
                chunks = self.chunker.preserve_context(chunks)
                
                # Optimize chunk sizes
                chunks = self.chunker.optimize_chunk_size(chunks)
                
                all_chunks.extend(chunks)
                
                logger.info(f"Created {len(chunks)} chunks for document {i+1}")
                
            except Exception as e:
                logger.error(f"Failed to chunk document {i+1}: {e}")
                continue
        
        # Calculate statistics
        if all_chunks:
            chunking_stats['total_chunks'] = len(all_chunks)
            chunking_stats['avg_chunks_per_document'] = len(all_chunks) / len(documents)
            chunking_stats['avg_chunk_size'] = sum(chunk.token_count for chunk in all_chunks) / len(all_chunks)
            chunking_stats['chunks_with_financial_context'] = sum(1 for chunk in all_chunks 
                                                                if chunk.metadata.get('has_financial_context', False))
            
            # Size optimization stats
            size_stats = {}
            for chunk in all_chunks:
                opt_status = chunk.metadata.get('size_optimization', 'unknown')
                size_stats[opt_status] = size_stats.get(opt_status, 0) + 1
            chunking_stats['size_optimization_stats'] = size_stats
        
        self.processed_chunks = all_chunks
        
        logger.info(f"Chunking pipeline completed. "
                   f"Total chunks: {chunking_stats['total_chunks']}, "
                   f"Avg size: {chunking_stats['avg_chunk_size']:.1f} tokens")
        
        return all_chunks
    
    def get_chunking_summary(self) -> Dict[str, Any]:
        """
        Get summary of chunking results.
        
        Returns:
            Chunking summary dictionary
        """
        if not self.processed_chunks:
            return {
                'total_chunks': 0,
                'total_documents': 0,
                'avg_chunk_size': 0,
                'size_distribution': {},
                'context_coverage': 0
            }
        
        # Calculate size distribution
        size_ranges = {
            'small (< 500)': 0,
            'medium (500-800)': 0,
            'large (> 800)': 0
        }
        
        for chunk in self.processed_chunks:
            if chunk.token_count < 500:
                size_ranges['small (< 500)'] += 1
            elif chunk.token_count <= 800:
                size_ranges['medium (500-800)'] += 1
            else:
                size_ranges['large (> 800)'] += 1
        
        # Calculate context coverage
        context_chunks = sum(1 for chunk in self.processed_chunks 
                           if chunk.metadata.get('has_financial_context', False))
        context_coverage = context_chunks / len(self.processed_chunks) if self.processed_chunks else 0
        
        return {
            'total_chunks': len(self.processed_chunks),
            'total_documents': len(set(chunk.source_document_id for chunk in self.processed_chunks)),
            'avg_chunk_size': sum(chunk.token_count for chunk in self.processed_chunks) / len(self.processed_chunks),
            'size_distribution': size_ranges,
            'context_coverage': context_coverage,
            'chunks_with_overlap': sum(1 for chunk in self.processed_chunks if chunk.overlap_info),
            'avg_sentences_per_chunk': sum(chunk.metadata.get('sentence_count', 0) for chunk in self.processed_chunks) / len(self.processed_chunks)
        }
    
    def export_chunks(self, output_path: str) -> None:
        """
        Export chunks to JSON file.
        
        Args:
            output_path: Path to save chunks
        """
        import json
        from pathlib import Path
        
        try:
            # Convert chunks to serializable format
            export_data = []
            for chunk in self.processed_chunks:
                export_chunk = {
                    'chunk_id': chunk.chunk_id,
                    'content': chunk.content,
                    'metadata': chunk.metadata,
                    'chunk_index': chunk.chunk_index,
                    'total_chunks': chunk.total_chunks,
                    'token_count': chunk.token_count,
                    'source_document_id': chunk.source_document_id,
                    'chunk_type': chunk.chunk_type,
                    'overlap_info': chunk.overlap_info
                }
                export_data.append(export_chunk)
            
            # Save to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(export_data)} chunks to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export chunks: {e}")
            raise DataCollectionError(f"Chunk export failed: {e}")
