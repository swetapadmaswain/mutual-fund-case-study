"""
Metadata enrichment module for Phase 2.1 - Enhancing chunk metadata for better retrieval.
"""
import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import hashlib

from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError
from src.rag.chunking.chunker import Chunk


@dataclass
class EnrichedMetadata:
    """Represents enriched metadata for chunks."""
    hierarchical_keys: List[str]
    content_type: str
    financial_data: Dict[str, Any]
    citation_info: Dict[str, Any]
    retrieval_tags: List[str]
    quality_score: float
    enrichment_timestamp: str


class MetadataEnricher:
    """Enriches chunk metadata for better organization and retrieval."""
    
    def __init__(self):
        """Initialize the metadata enricher."""
        # Fund type mappings
        self.fund_type_mapping = {
            'mid cap': 'mid_cap',
            'large cap': 'large_cap',
            'small cap': 'small_cap',
            'multi cap': 'multi_cap',
            'flexi cap': 'flexi_cap',
            'elss': 'elss',
            'tax saver': 'elss',
            'equity': 'equity',
            'debt': 'debt',
            'hybrid': 'hybrid',
            'focused': 'focused',
            'arbitrage': 'arbitrage'
        }
        
        # Content type patterns
        self.content_patterns = {
            'expense_ratio': r'expense\s*ratio',
            'exit_load': r'exit\s*load',
            'nav': r'nav',
            'sip': r'sip',
            'aum': r'aum',
            'risk': r'risk',
            'benchmark': r'benchmark',
            'portfolio': r'portfolio',
            'allocation': r'allocation',
            'performance': r'performance',
            'objective': r'objective',
            'returns': r'returns'
        }
        
        # Retrieval tags
        self.retrieval_tags = [
            'fund_info', 'performance_data', 'risk_assessment', 'investment_details',
            'fees_charges', 'portfolio_composition', 'benchmark_comparison',
            'investment_objective', 'historical_data', 'regulatory_info'
        ]
        
        logger.info("Initialized MetadataEnricher")
    
    def enrich_chunk_metadata(self, chunk: Chunk, source_metadata: Dict[str, Any]) -> Chunk:
        """
        Enrich metadata for a single chunk.
        
        Args:
            chunk: Chunk to enrich
            source_metadata: Original source metadata
            
        Returns:
            Chunk with enriched metadata
        """
        logger.debug(f"Enriching metadata for chunk {chunk.chunk_id}")
        
        # Create enriched metadata
        enriched_metadata = chunk.metadata.copy()
        
        # Add hierarchical keys
        hierarchical_keys = self._create_hierarchical_keys(chunk, source_metadata)
        enriched_metadata['hierarchical_keys'] = hierarchical_keys
        
        # Determine content type
        content_type = self._determine_content_type(chunk.content)
        enriched_metadata['content_type'] = content_type
        
        # Extract financial data
        financial_data = self._extract_financial_data(chunk.content)
        enriched_metadata['financial_data'] = financial_data
        
        # Create citation information
        citation_info = self._create_citation_info(chunk, source_metadata)
        enriched_metadata['citation_info'] = citation_info
        
        # Generate retrieval tags
        retrieval_tags = self._generate_retrieval_tags(chunk.content, content_type)
        enriched_metadata['retrieval_tags'] = retrieval_tags
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(chunk, enriched_metadata)
        enriched_metadata['quality_score'] = quality_score
        
        # Add enrichment metadata
        enriched_metadata['enrichment_timestamp'] = datetime.now().isoformat()
        enriched_metadata['enrichment_version'] = '1.0'
        
        # Create new chunk with enriched metadata
        enriched_chunk = Chunk(
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            metadata=enriched_metadata,
            chunk_index=chunk.chunk_index,
            total_chunks=chunk.total_chunks,
            token_count=chunk.token_count,
            source_document_id=chunk.source_document_id,
            chunk_type=chunk.chunk_type,
            overlap_info=chunk.overlap_info
        )
        
        logger.debug(f"Enriched metadata for chunk {chunk.chunk_id} with quality score {quality_score:.2f}")
        return enriched_chunk
    
    def _create_hierarchical_keys(self, chunk: Chunk, source_metadata: Dict[str, Any]) -> List[str]:
        """Create hierarchical keys for the chunk."""
        keys = []
        
        # Fund level
        fund_name = source_metadata.get('fund_name', '').lower()
        if fund_name:
            fund_key = f"fund:{self._normalize_key(fund_name)}"
            keys.append(fund_key)
        
        # Fund type level
        fund_type = self._extract_fund_type(chunk.content, source_metadata)
        if fund_type:
            type_key = f"type:{fund_type}"
            keys.append(type_key)
        
        # Content type level
        content_type = self._determine_content_type(chunk.content)
        if content_type:
            content_key = f"content:{content_type}"
            keys.append(content_key)
        
        # Document level
        doc_id = chunk.source_document_id
        if doc_id:
            doc_key = f"document:{doc_id[:8]}"  # Use short document ID
            keys.append(doc_key)
        
        # Chunk level
        chunk_key = f"chunk:{chunk.chunk_index}"
        keys.append(chunk_key)
        
        return keys
    
    def _normalize_key(self, key: str) -> str:
        """Normalize key for hierarchical structure."""
        # Remove special characters and normalize
        normalized = re.sub(r'[^a-z0-9]', '_', key.lower())
        # Remove multiple underscores
        normalized = re.sub(r'_+', '_', normalized)
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        return normalized
    
    def _extract_fund_type(self, content: str, source_metadata: Dict[str, Any]) -> Optional[str]:
        """Extract fund type from content and metadata."""
        # Check source metadata first
        fund_type = source_metadata.get('fund_type', '')
        if fund_type:
            return self.fund_type_mapping.get(fund_type.lower(), self._normalize_key(fund_type))
        
        # Extract from content
        content_lower = content.lower()
        for pattern, mapped_type in self.fund_type_mapping.items():
            if pattern in content_lower:
                return mapped_type
        
        return None
    
    def _determine_content_type(self, content: str) -> str:
        """Determine the primary content type of the chunk."""
        content_lower = content.lower()
        content_scores = {}
        
        # Score each content type
        for content_type, pattern in self.content_patterns.items():
            matches = len(re.findall(pattern, content_lower))
            content_scores[content_type] = matches
        
        # Find the content type with highest score
        if content_scores:
            best_type = max(content_scores, key=content_scores.get)
            if content_scores[best_type] > 0:
                return best_type
        
        return 'general'
    
    def _extract_financial_data(self, content: str) -> Dict[str, Any]:
        """Extract structured financial data from chunk content."""
        financial_data = {}
        
        # Extract expense ratios
        expense_matches = re.findall(r'expense\s*ratio[:\s]*([\d.]+%)', content, re.IGNORECASE)
        if expense_matches:
            financial_data['expense_ratios'] = expense_matches
        
        # Extract exit loads
        exit_load_matches = re.findall(r'exit\s*load[:\s]*([\d.]+%)', content, re.IGNORECASE)
        if exit_load_matches:
            financial_data['exit_loads'] = exit_load_matches
        
        # Extract NAV values
        nav_matches = re.findall(r'nav[:\s]*₹?([\d.]+)', content, re.IGNORECASE)
        if nav_matches:
            financial_data['nav_values'] = nav_matches
        
        # Extract SIP amounts
        sip_matches = re.findall(r'sip[:\s]*₹?(\d+,?\d*)', content, re.IGNORECASE)
        if sip_matches:
            financial_data['sip_amounts'] = sip_matches
        
        # Extract AUM
        aum_matches = re.findall(r'aum[:\s]*₹?([\d,]+\s*(?:cr|lakh|crore|thousand))', content, re.IGNORECASE)
        if aum_matches:
            financial_data['aum_values'] = aum_matches
        
        # Extract risk levels
        risk_matches = re.findall(r'risk\s*level[:\s]*([a-z\s]+)', content, re.IGNORECASE)
        if risk_matches:
            financial_data['risk_levels'] = [risk.strip() for risk in risk_matches]
        
        # Extract benchmark indices
        benchmark_matches = re.findall(r'benchmark[:\s]*([a-z\s]+(?:index|tri))', content, re.IGNORECASE)
        if benchmark_matches:
            financial_data['benchmarks'] = [bench.strip() for bench in benchmark_matches]
        
        return financial_data
    
    def _create_citation_info(self, chunk: Chunk, source_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create citation information for the chunk."""
        citation_info = {
            'source_url': source_metadata.get('url', ''),
            'source_title': source_metadata.get('title', ''),
            'fund_name': source_metadata.get('fund_name', ''),
            'chunk_id': chunk.chunk_id,
            'chunk_index': chunk.chunk_index,
            'total_chunks': chunk.total_chunks,
            'last_updated': source_metadata.get('fetched_at', ''),
            'citation_format': 'chunk_based',
            'access_date': datetime.now().isoformat()
        }
        
        # Add page context if available
        if chunk.metadata.get('page_number'):
            citation_info['page_number'] = chunk.metadata['page_number']
        
        # Add section context if available
        if chunk.metadata.get('section_title'):
            citation_info['section_title'] = chunk.metadata['section_title']
        
        return citation_info
    
    def _generate_retrieval_tags(self, content: str, content_type: str) -> List[str]:
        """Generate retrieval tags for the chunk."""
        tags = []
        content_lower = content.lower()
        
        # Add content type tag
        tags.append(content_type)
        
        # Add tags based on content patterns
        tag_patterns = {
            'fund_info': [r'fund\s*name', r'scheme\s*information', r'about\s*the\s*fund'],
            'performance_data': [r'returns?', r'performance', r'nav', r'growth'],
            'risk_assessment': [r'risk', r'volatility', r'riskometer'],
            'investment_details': [r'invest', r'sip', r'lumpsum', r'minimum'],
            'fees_charges': [r'expense\s*ratio', r'exit\s*load', r'charges?', r'fees?'],
            'portfolio_composition': [r'portfolio', r'allocation', r'holdings?', r'sector'],
            'benchmark_comparison': [r'benchmark', r'index', r'comparison'],
            'investment_objective': [r'objective', r'goal', r'aim', r'strategy'],
            'historical_data': [r'historical', r'past', r'previous', r'history'],
            'regulatory_info': [r'regulatory', r'compliance', r'sebi', r'amfi']
        }
        
        for tag, patterns in tag_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    tags.append(tag)
                    break
        
        # Remove duplicates while preserving order
        unique_tags = []
        seen = set()
        for tag in tags:
            if tag not in seen:
                unique_tags.append(tag)
                seen.add(tag)
        
        return unique_tags
    
    def _calculate_quality_score(self, chunk: Chunk, enriched_metadata: Dict[str, Any]) -> float:
        """Calculate quality score for the chunk."""
        score = 1.0
        
        # Length factor (optimal length gets higher score)
        if chunk.token_count < 300:
            score -= 0.2  # Too short
        elif chunk.token_count > 1000:
            score -= 0.2  # Too long
        elif 500 <= chunk.token_count <= 800:
            score += 0.1  # Optimal length
        
        # Financial content factor
        if enriched_metadata.get('financial_data'):
            financial_data_count = len(enriched_metadata['financial_data'])
            score += min(0.2, financial_data_count * 0.05)
        
        # Context preservation factor
        if enriched_metadata.get('has_financial_context', False):
            score += 0.1
        
        # Retrieval tags factor
        retrieval_tags = enriched_metadata.get('retrieval_tags', [])
        if len(retrieval_tags) >= 2:
            score += 0.1
        elif len(retrieval_tags) == 0:
            score -= 0.1
        
        # Citation completeness factor
        citation_info = enriched_metadata.get('citation_info', {})
        if citation_info.get('source_url') and citation_info.get('fund_name'):
            score += 0.1
        elif not citation_info.get('source_url'):
            score -= 0.2
        
        # Ensure score is within bounds
        return max(0.0, min(1.0, score))
    
    def ensure_consistency(self, chunks: List[Chunk]) -> List[Chunk]:
        """Ensure metadata consistency across chunks."""
        logger.info(f"Ensuring metadata consistency for {len(chunks)} chunks")
        
        # Collect all unique values for standardization
        all_fund_names = set()
        all_fund_types = set()
        all_content_types = set()
        
        for chunk in chunks:
            metadata = chunk.metadata
            if 'fund_name' in metadata:
                all_fund_names.add(metadata['fund_name'])
            if 'fund_type' in metadata:
                all_fund_types.add(metadata['fund_type'])
            if 'content_type' in metadata:
                all_content_types.add(metadata['content_type'])
        
        # Standardize values
        standardized_chunks = []
        for chunk in chunks:
            enriched_chunk = self._standardize_chunk_metadata(chunk, all_fund_names, all_fund_types, all_content_types)
            standardized_chunks.append(enriched_chunk)
        
        logger.info(f"Standardized metadata for {len(standardized_chunks)} chunks")
        return standardized_chunks
    
    def _standardize_chunk_metadata(self, chunk: Chunk, fund_names: Set[str], fund_types: Set[str], content_types: Set[str]) -> Chunk:
        """Standardize metadata for a chunk."""
        metadata = chunk.metadata.copy()
        
        # Standardize fund name
        if 'fund_name' in metadata:
            fund_name = metadata['fund_name']
            # Find the most similar fund name
            standardized_name = self._find_most_similar(fund_name, fund_names)
            if standardized_name:
                metadata['fund_name'] = standardized_name
        
        # Standardize fund type
        if 'fund_type' in metadata:
            fund_type = metadata['fund_type']
            standardized_type = self._find_most_similar(fund_type, fund_types)
            if standardized_type:
                metadata['fund_type'] = standardized_type
        
        # Standardize content type
        if 'content_type' in metadata:
            content_type = metadata['content_type']
            standardized_type = self._find_most_similar(content_type, content_types)
            if standardized_type:
                metadata['content_type'] = standardized_type
        
        # Create new chunk with standardized metadata
        return Chunk(
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            metadata=metadata,
            chunk_index=chunk.chunk_index,
            total_chunks=chunk.total_chunks,
            token_count=chunk.token_count,
            source_document_id=chunk.source_document_id,
            chunk_type=chunk.chunk_type,
            overlap_info=chunk.overlap_info
        )
    
    def _find_most_similar(self, value: str, candidates: Set[str]) -> Optional[str]:
        """Find the most similar value from candidates."""
        if not candidates or value in candidates:
            return value
        
        value_lower = value.lower()
        best_match = None
        best_similarity = 0.0
        
        for candidate in candidates:
            candidate_lower = candidate.lower()
            similarity = self._calculate_similarity(value_lower, candidate_lower)
            if similarity > best_similarity and similarity > 0.8:  # Threshold for similarity
                best_similarity = similarity
                best_match = candidate
        
        return best_match
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings."""
        # Simple word overlap similarity
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def preserve_citations(self, chunk: Chunk) -> Chunk:
        """Ensure proper citation information is preserved."""
        metadata = chunk.metadata.copy()
        
        # Ensure citation info exists
        if 'citation_info' not in metadata:
            metadata['citation_info'] = {}
        
        citation_info = metadata['citation_info']
        
        # Ensure required citation fields
        required_fields = ['source_url', 'fund_name', 'chunk_id', 'last_updated']
        for field in required_fields:
            if field not in citation_info:
                # Try to get from other metadata
                if field in metadata:
                    citation_info[field] = metadata[field]
                elif field == 'chunk_id':
                    citation_info[field] = chunk.chunk_id
                elif field == 'last_updated':
                    citation_info[field] = metadata.get('processed_at', datetime.now().isoformat())
        
        # Update chunk metadata
        return Chunk(
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            metadata=metadata,
            chunk_index=chunk.chunk_index,
            total_chunks=chunk.total_chunks,
            token_count=chunk.token_count,
            source_document_id=chunk.source_document_id,
            chunk_type=chunk.chunk_type,
            overlap_info=chunk.overlap_info
        )


class MetadataEnrichmentPipeline:
    """Main pipeline for metadata enrichment."""
    
    def __init__(self, enricher: Optional[MetadataEnricher] = None):
        """Initialize the metadata enrichment pipeline."""
        self.enricher = enricher or MetadataEnricher()
        self.enriched_chunks: List[Chunk] = []
    
    def enrich_chunks(self, chunks: List[Chunk], source_metadata: Dict[str, Any]) -> List[Chunk]:
        """
        Enrich metadata for multiple chunks.
        
        Args:
            chunks: List of chunks to enrich
            source_metadata: Source metadata for all chunks
            
        Returns:
            List of enriched chunks
        """
        logger.info(f"Starting metadata enrichment for {len(chunks)} chunks")
        
        enriched_chunks = []
        enrichment_stats = {
            'total_chunks': len(chunks),
            'enriched_chunks': 0,
            'avg_quality_score': 0,
            'content_type_distribution': {},
            'financial_data_coverage': 0
        }
        
        for i, chunk in enumerate(chunks):
            try:
                # Enrich chunk metadata
                enriched_chunk = self.enricher.enrich_chunk_metadata(chunk, source_metadata)
                
                # Ensure citations are preserved
                enriched_chunk = self.enricher.preserve_citations(enriched_chunk)
                
                enriched_chunks.append(enriched_chunk)
                enrichment_stats['enriched_chunks'] += 1
                
                logger.debug(f"Enriched chunk {i+1}/{len(chunks)}: {chunk.chunk_id}")
                
            except Exception as e:
                logger.error(f"Failed to enrich chunk {i+1}: {e}")
                # Keep original chunk if enrichment fails
                enriched_chunks.append(chunk)
        
        # Ensure consistency across all enriched chunks
        if enriched_chunks:
            enriched_chunks = self.enricher.ensure_consistency(enriched_chunks)
        
        # Calculate statistics
        if enriched_chunks:
            quality_scores = [chunk.metadata.get('quality_score', 0) for chunk in enriched_chunks]
            enrichment_stats['avg_quality_score'] = sum(quality_scores) / len(quality_scores)
            
            # Content type distribution
            content_types = {}
            for chunk in enriched_chunks:
                content_type = chunk.metadata.get('content_type', 'unknown')
                content_types[content_type] = content_types.get(content_type, 0) + 1
            enrichment_stats['content_type_distribution'] = content_types
            
            # Financial data coverage
            financial_chunks = sum(1 for chunk in enriched_chunks 
                                if chunk.metadata.get('financial_data'))
            enrichment_stats['financial_data_coverage'] = financial_chunks / len(enriched_chunks)
        
        self.enriched_chunks = enriched_chunks
        
        logger.info(f"Metadata enrichment completed. "
                   f"Enriched: {enrichment_stats['enriched_chunks']}, "
                   f"Avg quality: {enrichment_stats['avg_quality_score']:.2f}")
        
        return enriched_chunks
    
    def get_enrichment_summary(self) -> Dict[str, Any]:
        """
        Get summary of enrichment results.
        
        Returns:
            Enrichment summary dictionary
        """
        if not self.enriched_chunks:
            return {
                'total_chunks': 0,
                'avg_quality_score': 0,
                'content_types': {},
                'financial_coverage': 0,
                'citation_completeness': 0
            }
        
        # Quality metrics
        quality_scores = [chunk.metadata.get('quality_score', 0) for chunk in self.enriched_chunks]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # Content type distribution
        content_types = {}
        for chunk in self.enriched_chunks:
            content_type = chunk.metadata.get('content_type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        # Financial data coverage
        financial_chunks = sum(1 for chunk in self.enriched_chunks 
                            if chunk.metadata.get('financial_data'))
        financial_coverage = financial_chunks / len(self.enriched_chunks)
        
        # Citation completeness
        complete_citations = sum(1 for chunk in self.enriched_chunks 
                               if chunk.metadata.get('citation_info', {}).get('source_url'))
        citation_completeness = complete_citations / len(self.enriched_chunks)
        
        return {
            'total_chunks': len(self.enriched_chunks),
            'avg_quality_score': avg_quality,
            'content_types': content_types,
            'financial_coverage': financial_coverage,
            'citation_completeness': citation_completeness,
            'avg_retrieval_tags': sum(len(chunk.metadata.get('retrieval_tags', [])) 
                                     for chunk in self.enriched_chunks) / len(self.enriched_chunks),
            'hierarchical_keys_coverage': sum(1 for chunk in self.enriched_chunks 
                                           if chunk.metadata.get('hierarchical_keys')) / len(self.enriched_chunks)
        }
    
    def export_enriched_chunks(self, output_path: str) -> None:
        """
        Export enriched chunks to JSON file.
        
        Args:
            output_path: Path to save enriched chunks
        """
        import json
        from pathlib import Path
        
        try:
            # Convert enriched chunks to serializable format
            export_data = []
            for chunk in self.enriched_chunks:
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
            
            # Add enrichment summary
            export_summary = {
                'enrichment_summary': self.get_enrichment_summary(),
                'enrichment_timestamp': datetime.now().isoformat(),
                'total_chunks_exported': len(export_data)
            }
            
            # Save to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'summary': export_summary,
                    'chunks': export_data
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(export_data)} enriched chunks to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export enriched chunks: {e}")
            raise DataCollectionError(f"Enriched chunk export failed: {e}")
