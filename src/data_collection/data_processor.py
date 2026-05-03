"""
Data processing pipeline for cleaning, normalizing, and storing collected data.
"""
import json
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
import re
from datetime import datetime
import pandas as pd

from src.config.settings import settings
from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError, CacheError


class DataProcessor:
    """Processes and stores collected mutual fund data."""
    
    def __init__(self):
        """Initialize the data processor."""
        self.cache_dir = Path(settings.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Data storage
        self.data_file = self.cache_dir / "hdfc_fund_data.json"
        self.metadata_file = self.cache_dir / "processing_metadata.json"
        
        # Load existing data if available
        self.existing_data = self._load_existing_data()
        self.processed_hashes = set()
        if self.existing_data:
            self.processed_hashes = {item.get('content_hash', '') for item in self.existing_data}
    
    def _load_existing_data(self) -> List[Dict[str, Any]]:
        """Load existing data from cache."""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load existing data: {e}")
        return []
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of documents.
        
        Args:
            documents: List of document dictionaries from DocumentLoader
            
        Returns:
            Processing results summary
        """
        logger.info(f"Processing {len(documents)} documents")
        
        results = {
            'total_documents': len(documents),
            'new_documents': 0,
            'duplicate_documents': 0,
            'processed_documents': 0,
            'failed_documents': 0,
            'errors': [],
            'processing_time': datetime.now().isoformat()
        }
        
        processed_docs = []
        
        for doc in documents:
            try:
                # Check for duplicates
                if doc.get('content_hash') in self.processed_hashes:
                    results['duplicate_documents'] += 1
                    logger.info(f"Skipping duplicate document: {doc['url']}")
                    continue
                
                # Process the document
                processed_doc = self._process_single_document(doc)
                processed_docs.append(processed_doc)
                results['processed_documents'] += 1
                results['new_documents'] += 1
                
                # Add to processed hashes
                self.processed_hashes.add(doc.get('content_hash', ''))
                
            except Exception as e:
                logger.error(f"Failed to process document {doc.get('url', 'unknown')}: {e}")
                results['failed_documents'] += 1
                results['errors'].append(f"{doc.get('url', 'unknown')}: {str(e)}")
        
        # Save processed documents
        if processed_docs:
            self._save_processed_data(processed_docs)
        
        logger.info(f"Processing complete. New: {results['new_documents']}, "
                   f"Duplicates: {results['duplicate_documents']}, "
                   f"Failed: {results['failed_documents']}")
        
        return results
    
    def _process_single_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single document.
        
        Args:
            doc: Document dictionary
            
        Returns:
            Processed document dictionary
        """
        processed_doc = doc.copy()
        
        # Clean and normalize content
        cleaned_content = self._clean_content(doc.get('content', ''))
        processed_doc['cleaned_content'] = cleaned_content
        
        # Extract structured data
        structured_data = self._extract_structured_data(cleaned_content, doc.get('metadata', {}))
        processed_doc['structured_data'] = structured_data
        
        # Add processing timestamp
        processed_doc['processed_at'] = datetime.now().isoformat()
        
        # Validate processed data
        self._validate_processed_document(processed_doc)
        
        return processed_doc
    
    def _clean_content(self, content: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            content: Raw content string
            
        Returns:
            Cleaned content string
        """
        if not content:
            return ""
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove special characters that might interfere with processing
        content = re.sub(r'[^\w\s.,%₹-]', ' ', content)
        
        # Normalize financial symbols
        content = content.replace('Rs.', '₹')
        content = content.replace('INR', '₹')
        
        # Normalize percentage format
        content = re.sub(r'(\d+)\s*%', r'\1%', content)
        
        # Strip and return
        return content.strip()
    
    def _extract_structured_data(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured financial data from content.
        
        Args:
            content: Cleaned content string
            metadata: Existing metadata
            
        Returns:
            Structured data dictionary
        """
        structured_data = metadata.copy() if metadata else {}
        
        # Extract fund name
        if not structured_data.get('fund_name'):
            structured_data['fund_name'] = self._extract_fund_name(content)
        
        # Extract financial metrics
        structured_data['expense_ratio'] = self._extract_expense_ratio(content)
        structured_data['exit_load'] = self._extract_exit_load(content)
        structured_data['min_sip_amount'] = self._extract_min_sip(content)
        structured_data['nav'] = self._extract_nav(content)
        structured_data['risk_level'] = self._extract_risk_level(content)
        structured_data['benchmark'] = self._extract_benchmark(content)
        structured_data['fund_type'] = self._extract_fund_type(content)
        structured_data['aum'] = self._extract_aum(content)
        
        # Extract key information sections
        structured_data['key_information'] = self._extract_key_information(content)
        structured_data['investment_objective'] = self._extract_investment_objective(content)
        
        return structured_data
    
    def _extract_fund_name(self, content: str) -> Optional[str]:
        """Extract fund name from content."""
        # Look for HDFC fund patterns
        patterns = [
            r'HDFC\s+([A-Za-z\s]+)\s+Fund',
            r'HDFC\s+([A-Za-z\s-]+)\s+(?:Direct|Regular)',
            r'([A-Za-z\s]+)\s+Fund\s*(?:-|\s)*(?:Direct|Regular)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                fund_name = match.group(1).strip()
                # Clean up the name
                fund_name = re.sub(r'\s+', ' ', fund_name)
                return fund_name
        
        return None
    
    def _extract_expense_ratio(self, content: str) -> Optional[str]:
        """Extract expense ratio from content."""
        patterns = [
            r'expense\s*ratio.*?(\d+\.?\d*%)',
            r'total\s*expense.*?(\d+\.?\d*%)',
            r'annual\s*expense.*?(\d+\.?\d*%)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_exit_load(self, content: str) -> Optional[str]:
        """Extract exit load from content."""
        patterns = [
            r'exit\s*load.*?(\d+\.?\d*%)',
            r'withdrawal.*?(\d+\.?\d*%)',
            r'redemption.*?(\d+\.?\d*%)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_min_sip(self, content: str) -> Optional[str]:
        """Extract minimum SIP amount from content."""
        patterns = [
            r'minimum\s*sip.*?₹?\s*(\d+,?\d*)',
            r'sip.*?minimum.*?₹?\s*(\d+,?\d*)',
            r'sip.*?starts.*?₹?\s*(\d+,?\d*)',
            r'systematic.*?₹?\s*(\d+,?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_nav(self, content: str) -> Optional[str]:
        """Extract NAV from content."""
        patterns = [
            r'nav.*?₹?\s*(\d+\.?\d*)',
            r'net\s*asset.*?value.*?₹?\s*(\d+\.?\d*)',
            r'current\s*nav.*?₹?\s*(\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_risk_level(self, content: str) -> Optional[str]:
        """Extract risk level from content."""
        risk_keywords = ['low', 'moderately low', 'moderate', 'moderately high', 'high', 'very high']
        
        for risk in risk_keywords:
            if re.search(rf'\b{risk}\b.*risk', content, re.IGNORECASE):
                return risk.title()
        
        return None
    
    def _extract_benchmark(self, content: str) -> Optional[str]:
        """Extract benchmark index from content."""
        patterns = [
            r'benchmark.*?([A-Za-z\s]+(?:Index| TRI))',
            r'benchmarked.*?against.*?([A-Za-z\s]+(?:Index| TRI))',
            r'compared.*?([A-Za-z\s]+(?:Index| TRI))'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_fund_type(self, content: str) -> Optional[str]:
        """Extract fund type from content."""
        fund_types = [
            'large cap', 'mid cap', 'small cap', 'multi cap', 'flexi cap',
            'elss', 'tax saver', 'equity', 'debt', 'hybrid', 'balanced',
            'arbitrage', 'focused', 'value', 'growth'
        ]
        
        for fund_type in fund_types:
            if re.search(rf'\b{fund_type}\b', content, re.IGNORECASE):
                return fund_type.title()
        
        return None
    
    def _extract_aum(self, content: str) -> Optional[str]:
        """Extract Assets Under Management from content."""
        patterns = [
            r'aum.*?₹?\s*(\d+,?\d*\s*(?:cr|crore|lakh|thousand))',
            r'assets.*?under.*?management.*?₹?\s*(\d+,?\d*\s*(?:cr|crore|lakh|thousand))',
            r'fund.*?size.*?₹?\s*(\d+,?\d*\s*(?:cr|crore|lakh|thousand))'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_key_information(self, content: str) -> List[str]:
        """Extract key information points from content."""
        key_info = []
        
        # Look for bullet points or numbered lists
        patterns = [
            r'•\s*([^\n]+)',
            r'·\s*([^\n]+)',
            r'\d+\.\s*([^\n]+)',
            r'-\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                cleaned = match.strip()
                if len(cleaned) > 10:  # Filter out very short points
                    key_info.append(cleaned)
        
        return key_info[:10]  # Limit to top 10 points
    
    def _extract_investment_objective(self, content: str) -> Optional[str]:
        """Extract investment objective from content."""
        patterns = [
            r'investment\s*objective[:\-]\s*([^\n]+)',
            r'objective[:\-]\s*([^\n]+)',
            r'aim\s*to[:\-]\s*([^\n]+)',
            r'goal[:\-]\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                objective = match.group(1).strip()
                # Limit to reasonable length
                if len(objective) > 500:
                    objective = objective[:500] + "..."
                return objective
        
        return None
    
    def _validate_processed_document(self, doc: Dict[str, Any]) -> None:
        """
        Validate a processed document.
        
        Args:
            doc: Processed document to validate
            
        Raises:
            DataCollectionError: If validation fails
        """
        required_fields = ['url', 'title', 'cleaned_content', 'structured_data']
        
        for field in required_fields:
            if field not in doc or not doc[field]:
                raise DataCollectionError(f"Missing required field: {field}")
        
        # Validate content length
        if len(doc['cleaned_content']) < 50:
            raise DataCollectionError("Content too short after cleaning")
        
        # Validate URL format
        if not doc['url'].startswith('http'):
            raise DataCollectionError("Invalid URL format")
    
    def _save_processed_data(self, documents: List[Dict[str, Any]]) -> None:
        """
        Save processed data to cache.
        
        Args:
            documents: List of processed documents
        """
        try:
            # Combine with existing data
            all_data = self.existing_data + documents
            
            # Remove duplicates based on content hash
            seen_hashes = set()
            unique_data = []
            for doc in all_data:
                content_hash = doc.get('content_hash', '')
                if content_hash not in seen_hashes:
                    unique_data.append(doc)
                    seen_hashes.add(content_hash)
            
            # Save to file
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(unique_data, f, indent=2, ensure_ascii=False)
            
            # Save metadata
            metadata = {
                'total_documents': len(unique_data),
                'last_updated': datetime.now().isoformat(),
                'source_urls': list(set(doc['url'] for doc in unique_data)),
                'processing_stats': {
                    'avg_content_length': sum(len(doc.get('cleaned_content', '')) for doc in unique_data) / len(unique_data),
                    'funds_processed': len(set(doc.get('structured_data', {}).get('fund_name', 'Unknown') for doc in unique_data))
                }
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            # Update existing data
            self.existing_data = unique_data
            
            logger.info(f"Saved {len(documents)} new documents, total: {len(unique_data)}")
            
        except Exception as e:
            logger.error(f"Failed to save processed data: {e}")
            raise CacheError(f"Failed to save data: {e}")
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get summary of processed data.
        
        Returns:
            Processing summary dictionary
        """
        if not self.existing_data:
            return {
                'total_documents': 0,
                'last_updated': None,
                'funds_processed': 0,
                'avg_content_length': 0
            }
        
        # Load metadata if available
        metadata = {}
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
        
        return {
            'total_documents': len(self.existing_data),
            'unique_funds': len(set(doc.get('structured_data', {}).get('fund_name', 'Unknown') for doc in self.existing_data)),
            'last_updated': metadata.get('last_updated'),
            'source_urls': metadata.get('source_urls', []),
            'processing_stats': metadata.get('processing_stats', {})
        }
    
    def export_to_csv(self, output_path: str) -> None:
        """
        Export processed data to CSV format.
        
        Args:
            output_path: Path to save CSV file
        """
        try:
            # Flatten data for CSV export
            flattened_data = []
            for doc in self.existing_data:
                flat_doc = {
                    'url': doc.get('url', ''),
                    'title': doc.get('title', ''),
                    'fund_name': doc.get('structured_data', {}).get('fund_name', ''),
                    'fund_type': doc.get('structured_data', {}).get('fund_type', ''),
                    'expense_ratio': doc.get('structured_data', {}).get('expense_ratio', ''),
                    'exit_load': doc.get('structured_data', {}).get('exit_load', ''),
                    'min_sip_amount': doc.get('structured_data', {}).get('min_sip_amount', ''),
                    'nav': doc.get('structured_data', {}).get('nav', ''),
                    'risk_level': doc.get('structured_data', {}).get('risk_level', ''),
                    'benchmark': doc.get('structured_data', {}).get('benchmark', ''),
                    'aum': doc.get('structured_data', {}).get('aum', ''),
                    'content_length': len(doc.get('cleaned_content', '')),
                    'fetched_at': doc.get('fetched_at', ''),
                    'processed_at': doc.get('processed_at', '')
                }
                flattened_data.append(flat_doc)
            
            # Create DataFrame and save
            df = pd.DataFrame(flattened_data)
            df.to_csv(output_path, index=False)
            
            logger.info(f"Exported {len(flattened_data)} documents to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            raise DataCollectionError(f"CSV export failed: {e}")
