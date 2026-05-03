"""
Document processing module for Phase 2.1 - Text preprocessing and cleaning.
"""
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError


@dataclass
class ProcessedDocument:
    """Represents a processed document with cleaned content."""
    original_content: str
    cleaned_content: str
    metadata: Dict[str, Any]
    processing_stats: Dict[str, Any]
    content_hash: str


class TextPreprocessor:
    """Handles text preprocessing and cleaning for mutual fund documents."""
    
    def __init__(self):
        """Initialize the text preprocessor."""
        # Financial symbol patterns
        self.currency_patterns = {
            'rs': r'(?i)rs\.?\s*',
            'inr': r'(?i)inr\s*',
            'rupee': r'(?i)rupee[s]?\s*',
            '₹': r'₹\s*'
        }
        
        # Noise patterns to remove
        self.noise_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<style[^>]*>.*?</style>',
            r'<[^>]+>',  # HTML tags
            r'\s+',      # Multiple whitespace
            r'\n\s*\n',  # Multiple newlines
            r'[^\w\s.,%₹-();:/]',  # Special characters except financial symbols
        ]
        
        # Financial term patterns to preserve
        self.financial_terms = [
            'expense ratio', 'exit load', 'nav', 'sip', 'aum',
            'large cap', 'mid cap', 'small cap', 'elss', 'tax saver',
            'direct growth', 'regular growth', 'benchmark', 'riskometer'
        ]
    
    def clean_text(self, raw_content: str) -> str:
        """
        Clean and normalize raw text content.
        
        Args:
            raw_content: Raw text content from documents
            
        Returns:
            Cleaned and normalized text
        """
        if not raw_content:
            return ""
        
        logger.debug(f"Starting text cleaning for content length: {len(raw_content)}")
        
        cleaned = raw_content
        
        # Step 1: Remove HTML tags and scripts
        cleaned = self._remove_html_tags(cleaned)
        
        # Step 2: Normalize financial symbols
        cleaned = self._normalize_financial_symbols(cleaned)
        
        # Step 3: Remove noise while preserving important content
        cleaned = self._remove_noise(cleaned)
        
        # Step 4: Normalize whitespace
        cleaned = self._normalize_whitespace(cleaned)
        
        # Step 5: Preserve financial terms
        cleaned = self._preserve_financial_terms(cleaned)
        
        # Step 6: Final cleanup
        cleaned = self._final_cleanup(cleaned)
        
        logger.debug(f"Text cleaning completed. Final length: {len(cleaned)}")
        return cleaned.strip()
    
    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML tags and scripts."""
        # Remove script and style blocks
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        return text
    
    def _normalize_financial_symbols(self, text: str) -> str:
        """Normalize financial symbols to consistent format."""
        # Normalize all currency symbols to ₹
        for pattern in self.currency_patterns.values():
            text = re.sub(pattern, '₹', text)
        
        # Normalize percentage format
        text = re.sub(r'(\d+)\s*%', r'\1%', text)
        text = re.sub(r'%\s*(\d+)', r'\1%', text)  # Handle % after number
        
        # Normalize decimal numbers in financial context
        text = re.sub(r'(\d+)\.(\d{2})\s*%', r'\1.\2%', text)  # Ensure 2 decimal places for percentages
        
        return text
    
    def _remove_noise(self, text: str) -> str:
        """Remove noise while preserving important content."""
        # Remove excessive special characters but keep financial ones
        text = re.sub(r'[^\w\s.,%₹-();:/]', ' ', text)
        
        # Remove common noise patterns
        noise_patterns = [
            r'click here',
            r'read more',
            r'view details',
            r'download.*?pdf',
            r'©.*?\d{4}',
            r'all rights reserved',
            r'terms and conditions',
            r'privacy policy',
            r'cookie policy',
            r'jump to navigation',
            r'skip to content'
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        # Replace multiple newlines with single newline
        text = re.sub(r'\n\s*\n+', '\n', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines
        lines = [line for line in lines if line]
        
        return ' '.join(lines)
    
    def _preserve_financial_terms(self, text: str) -> str:
        """Ensure financial terms are properly formatted."""
        # Capitalize important financial terms
        for term in self.financial_terms:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            text = pattern.sub(term.upper(), text)
        
        return text
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup of text."""
        # Remove any remaining HTML entities
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s*([.,%])', r'\1', text)
        text = re.sub(r'([.,%])\s*', r'\1 ', text)
        
        # Remove double spaces
        text = re.sub(r'\s{2,}', ' ', text)
        
        return text
    
    def extract_financial_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured financial data from cleaned text.
        
        Args:
            text: Cleaned text content
            
        Returns:
            Dictionary of extracted financial data
        """
        financial_data = {}
        
        # Extract expense ratios
        expense_ratios = re.findall(r'expense ratio[:\s]*([\d.]+%)', text, re.IGNORECASE)
        if expense_ratios:
            financial_data['expense_ratios'] = expense_ratios
        
        # Extract exit loads
        exit_loads = re.findall(r'exit load[:\s]*([\d.]+%)', text, re.IGNORECASE)
        if exit_loads:
            financial_data['exit_loads'] = exit_loads
        
        # Extract SIP amounts
        sip_amounts = re.findall(r'sip[:\s]*₹?(\d+,?\d*)', text, re.IGNORECASE)
        if sip_amounts:
            financial_data['sip_amounts'] = sip_amounts
        
        # Extract NAV values
        nav_values = re.findall(r'nav[:\s]*₹?([\d.]+)', text, re.IGNORECASE)
        if nav_values:
            financial_data['nav_values'] = nav_values
        
        # Extract AUM
        aum_values = re.findall(r'aum[:\s]*₹?([\d,]+\s*(?:cr|lakh|crore|thousand))', text, re.IGNORECASE)
        if aum_values:
            financial_data['aum_values'] = aum_values
        
        # Extract risk levels
        risk_levels = re.findall(r'risk\s*level[:\s]*([a-z\s]+)', text, re.IGNORECASE)
        if risk_levels:
            financial_data['risk_levels'] = [risk.strip() for risk in risk_levels]
        
        return financial_data
    
    def calculate_processing_stats(self, original: str, cleaned: str) -> Dict[str, Any]:
        """
        Calculate processing statistics.
        
        Args:
            original: Original text
            cleaned: Cleaned text
            
        Returns:
            Processing statistics dictionary
        """
        return {
            'original_length': len(original),
            'cleaned_length': len(cleaned),
            'compression_ratio': len(cleaned) / len(original) if original else 0,
            'words_removed': len(original.split()) - len(cleaned.split()),
            'financial_terms_found': len([term for term in self.financial_terms if term in cleaned.lower()]),
            'currency_symbols_normalized': len(re.findall(r'₹', cleaned)),
            'percentages_found': len(re.findall(r'\d+\.?\d*%', cleaned))
        }
    
    def process_document(self, raw_content: str, metadata: Dict[str, Any]) -> ProcessedDocument:
        """
        Process a complete document.
        
        Args:
            raw_content: Raw document content
            metadata: Document metadata
            
        Returns:
            ProcessedDocument object
        """
        logger.info(f"Processing document: {metadata.get('fund_name', 'Unknown')}")
        
        # Clean the content
        cleaned_content = self.clean_text(raw_content)
        
        # Extract financial data
        financial_data = self.extract_financial_data(cleaned_content)
        
        # Calculate processing stats
        processing_stats = self.calculate_processing_stats(raw_content, cleaned_content)
        
        # Generate content hash
        import hashlib
        content_hash = hashlib.md5(cleaned_content.encode()).hexdigest()
        
        # Update metadata with extracted data
        enhanced_metadata = metadata.copy()
        enhanced_metadata.update(financial_data)
        enhanced_metadata['content_hash'] = content_hash
        enhanced_metadata['processed_at'] = str(Path().cwd())
        
        processed_doc = ProcessedDocument(
            original_content=raw_content,
            cleaned_content=cleaned_content,
            metadata=enhanced_metadata,
            processing_stats=processing_stats,
            content_hash=content_hash
        )
        
        logger.info(f"Document processing completed. "
                   f"Length: {len(cleaned_content)}, "
                   f"Compression: {processing_stats['compression_ratio']:.2f}")
        
        return processed_doc


class DocumentProcessor:
    """Main document processor for Phase 2.1."""
    
    def __init__(self):
        """Initialize the document processor."""
        self.preprocessor = TextPreprocessor()
        self.processed_documents: List[ProcessedDocument] = []
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> List[ProcessedDocument]:
        """
        Process multiple documents.
        
        Args:
            documents: List of document dictionaries from Phase 1
            
        Returns:
            List of processed documents
        """
        logger.info(f"Starting batch processing of {len(documents)} documents")
        
        processed_docs = []
        processing_errors = []
        
        for i, doc in enumerate(documents):
            try:
                raw_content = doc.get('cleaned_content', '') or doc.get('content', '')
                metadata = doc.get('metadata', {})
                
                if not raw_content:
                    logger.warning(f"Document {i+1} has no content to process")
                    continue
                
                processed_doc = self.preprocessor.process_document(raw_content, metadata)
                processed_docs.append(processed_doc)
                
            except Exception as e:
                logger.error(f"Failed to process document {i+1}: {e}")
                processing_errors.append(f"Document {i+1}: {str(e)}")
        
        self.processed_documents = processed_docs
        
        logger.info(f"Batch processing completed. "
                   f"Successfully processed: {len(processed_docs)}, "
                   f"Errors: {len(processing_errors)}")
        
        if processing_errors:
            for error in processing_errors:
                logger.error(error)
        
        return processed_docs
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get summary of processing results.
        
        Returns:
            Processing summary dictionary
        """
        if not self.processed_documents:
            return {
                'total_documents': 0,
                'total_words': 0,
                'avg_compression_ratio': 0,
                'financial_data_extracted': {},
                'processing_errors': 0
            }
        
        total_docs = len(self.processed_documents)
        total_words = sum(len(doc.cleaned_content.split()) for doc in self.processed_documents)
        avg_compression = sum(doc.processing_stats['compression_ratio'] for doc in self.processed_documents) / total_docs
        
        # Aggregate financial data
        financial_data = {}
        for doc in self.processed_documents:
            for key, value in doc.metadata.items():
                if key.endswith('_ratios') or key.endswith('_loads') or key.endswith('_amounts') or key.endswith('_values') or key.endswith('_levels'):
                    if key not in financial_data:
                        financial_data[key] = []
                    if isinstance(value, list):
                        financial_data[key].extend(value)
        
        return {
            'total_documents': total_docs,
            'total_words': total_words,
            'avg_compression_ratio': avg_compression,
            'financial_data_extracted': financial_data,
            'processing_errors': 0,
            'avg_document_length': total_words / total_docs if total_docs > 0 else 0
        }
    
    def export_processed_documents(self, output_path: str) -> None:
        """
        Export processed documents to JSON file.
        
        Args:
            output_path: Path to save the processed documents
        """
        import json
        from pathlib import Path
        
        try:
            # Convert processed documents to serializable format
            export_data = []
            for doc in self.processed_documents:
                export_doc = {
                    'metadata': doc.metadata,
                    'cleaned_content': doc.cleaned_content,
                    'processing_stats': doc.processing_stats,
                    'content_hash': doc.content_hash
                }
                export_data.append(export_doc)
            
            # Save to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(export_data)} processed documents to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export processed documents: {e}")
            raise DataCollectionError(f"Export failed: {e}")
