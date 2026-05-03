"""
Chunk validation and quality control module for Phase 2.1.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.utils.logger import logger
from src.utils.exceptions import DataCollectionError
from src.rag.chunking.chunker import Chunk


class ValidationStatus(Enum):
    """Validation status for chunks."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


@dataclass
class ValidationResult:
    """Result of chunk validation."""
    status: ValidationStatus
    score: float
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class ChunkValidator:
    """Validates chunks for quality and compliance."""
    
    def __init__(self):
        """Initialize the chunk validator."""
        # Quality thresholds
        self.min_chunk_size = 100  # tokens
        self.max_chunk_size = 1200  # tokens
        self.min_quality_score = 0.3
        self.max_quality_score = 1.0
        
        # Content quality indicators
        self.quality_indicators = {
            'financial_data': r'(expense\s*ratio|exit\s*load|nav|sip|aum|risk|benchmark)',
            'structured_info': r'(\d+\.?\d*%|₹\d+|\d+\s*years?)',
            'complete_sentences': r'[A-Z][^.!?]*[.!?]',
            'no_duplicates': r'(?!(\b\w+\b)(?:\s+\b\1\b)+)',  # Negative lookahead for duplicates
            'coherent_text': r'\w+\s+\w+\s+\w+'  # At least 3 consecutive words
        }
        
        # Compliance patterns to check
        self.compliance_patterns = {
            'advice_language': r'(should|must|recommend|suggest|advise)\s+(you|invest|buy|sell)',
            'personal_data': r'(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}|\d{2}[-/]\d{2}[-/]\d{4}|[A-Z]{5}\d{4}[A-Z])',
            'promotional_content': r'(best|top|guaranteed|sure.*shot|high.*return)',
            'speculative_content': r'(will.*go.*up|sure.*bet|can\'t.*lose)',
        }
        
        # Required metadata fields
        self.required_metadata = [
            'chunk_id',
            'source_document_id',
            'chunk_index',
            'total_chunks',
            'content_type',
            'citation_info'
        ]
        
        logger.info("Initialized ChunkValidator")
    
    def validate_chunk(self, chunk: Chunk) -> ValidationResult:
        """
        Validate a single chunk for quality and compliance.
        
        Args:
            chunk: Chunk to validate
            
        Returns:
            ValidationResult object
        """
        logger.debug(f"Validating chunk {chunk.chunk_id}")
        
        errors = []
        warnings = []
        validation_metadata = {}
        
        # Initialize score
        score = 1.0
        
        # 1. Content validation
        content_result = self._validate_content(chunk.content)
        score += content_result['score_adjustment']
        errors.extend(content_result['errors'])
        warnings.extend(content_result['warnings'])
        validation_metadata['content_validation'] = content_result['metadata']
        
        # 2. Metadata validation
        metadata_result = self._validate_metadata(chunk.metadata)
        score += metadata_result['score_adjustment']
        errors.extend(metadata_result['errors'])
        warnings.extend(metadata_result['warnings'])
        validation_metadata['metadata_validation'] = metadata_result['metadata']
        
        # 3. Compliance validation
        compliance_result = self._validate_compliance(chunk.content)
        score += compliance_result['score_adjustment']
        errors.extend(compliance_result['errors'])
        warnings.extend(compliance_result['warnings'])
        validation_metadata['compliance_validation'] = compliance_result['metadata']
        
        # 4. Quality validation
        quality_result = self._validate_quality(chunk)
        score += quality_result['score_adjustment']
        errors.extend(quality_result['errors'])
        warnings.extend(quality_result['warnings'])
        validation_metadata['quality_validation'] = quality_result['metadata']
        
        # 5. Size validation
        size_result = self._validate_size(chunk)
        score += size_result['score_adjustment']
        errors.extend(size_result['errors'])
        warnings.extend(size_result['warnings'])
        validation_metadata['size_validation'] = size_result['metadata']
        
        # Normalize score
        score = max(0.0, min(self.max_quality_score, score))
        
        # Determine status
        if errors:
            status = ValidationStatus.INVALID
        elif warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.VALID
        
        # Add validation timestamp
        validation_metadata['validation_timestamp'] = str(datetime.now())
        validation_metadata['validator_version'] = '1.0'
        
        result = ValidationResult(
            status=status,
            score=score,
            errors=errors,
            warnings=warnings,
            metadata=validation_metadata
        )
        
        logger.debug(f"Chunk {chunk.chunk_id} validation: {status.value}, score={score:.2f}")
        return result
    
    def _validate_content(self, content: str) -> Dict[str, Any]:
        """Validate chunk content."""
        errors = []
        warnings = []
        score_adjustment = 0.0
        metadata = {}
        
        # Check if content is empty
        if not content or not content.strip():
            errors.append("Chunk content is empty")
            score_adjustment -= 1.0
            return {
                'errors': errors,
                'warnings': warnings,
                'score_adjustment': score_adjustment,
                'metadata': metadata
            }
        
        # Check content length
        content_length = len(content.strip())
        metadata['content_length'] = content_length
        
        if content_length < 50:
            errors.append("Chunk content is too short (< 50 characters)")
            score_adjustment -= 0.5
        elif content_length < 200:
            warnings.append("Chunk content is short (< 200 characters)")
            score_adjustment -= 0.2
        
        # Check for financial data
        financial_matches = 0
        for indicator, pattern in self.quality_indicators.items():
            if indicator == 'financial_data':
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                financial_matches = matches
                metadata['financial_data_matches'] = matches
                break
        
        if financial_matches == 0:
            warnings.append("No financial data detected in chunk")
            score_adjustment -= 0.1
        elif financial_matches >= 3:
            score_adjustment += 0.1
        
        # Check for structured information
        structured_matches = len(re.findall(self.quality_indicators['structured_info'], content))
        metadata['structured_info_matches'] = structured_matches
        
        if structured_matches == 0:
            warnings.append("No structured information detected")
            score_adjustment -= 0.1
        elif structured_matches >= 2:
            score_adjustment += 0.1
        
        # Check for complete sentences
        sentence_matches = len(re.findall(self.quality_indicators['complete_sentences'], content))
        metadata['sentence_count'] = sentence_matches
        
        if sentence_matches == 0:
            warnings.append("No complete sentences detected")
            score_adjustment -= 0.1
        elif sentence_matches >= 3:
            score_adjustment += 0.1
        
        # Check for coherent text
        coherent_matches = len(re.findall(self.quality_indicators['coherent_text'], content))
        metadata['coherent_text_matches'] = coherent_matches
        
        if coherent_matches < 2:
            warnings.append("Text may not be coherent")
            score_adjustment -= 0.1
        
        # Check for duplicate content
        words = content.lower().split()
        unique_words = set(words)
        duplicate_ratio = 1 - (len(unique_words) / len(words)) if words else 0
        metadata['duplicate_ratio'] = duplicate_ratio
        
        if duplicate_ratio > 0.3:
            warnings.append("High duplicate content ratio")
            score_adjustment -= 0.2
        elif duplicate_ratio > 0.5:
            errors.append("Excessive duplicate content")
            score_adjustment -= 0.5
        
        return {
            'errors': errors,
            'warnings': warnings,
            'score_adjustment': score_adjustment,
            'metadata': metadata
        }
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate chunk metadata."""
        errors = []
        warnings = []
        score_adjustment = 0.0
        validation_metadata = {}
        
        # Check required metadata fields
        missing_fields = []
        for field in self.required_metadata:
            if field not in metadata or not metadata[field]:
                missing_fields.append(field)
        
        if missing_fields:
            errors.append(f"Missing required metadata fields: {', '.join(missing_fields)}")
            score_adjustment -= 0.5
        else:
            score_adjustment += 0.1
        
        validation_metadata['missing_fields'] = missing_fields
        validation_metadata['required_fields_present'] = len(missing_fields) == 0
        
        # Check citation info completeness
        citation_info = metadata.get('citation_info', {})
        required_citation_fields = ['source_url', 'fund_name']
        missing_citation_fields = [field for field in required_citation_fields 
                                 if not citation_info.get(field)]
        
        if missing_citation_fields:
            warnings.append(f"Missing citation fields: {', '.join(missing_citation_fields)}")
            score_adjustment -= 0.2
        else:
            score_adjustment += 0.1
        
        validation_metadata['missing_citation_fields'] = missing_citation_fields
        validation_metadata['citation_complete'] = len(missing_citation_fields) == 0
        
        # Check hierarchical keys
        hierarchical_keys = metadata.get('hierarchical_keys', [])
        if not hierarchical_keys:
            warnings.append("No hierarchical keys found")
            score_adjustment -= 0.1
        elif len(hierarchical_keys) >= 3:
            score_adjustment += 0.1
        
        validation_metadata['hierarchical_keys_count'] = len(hierarchical_keys)
        
        # Check retrieval tags
        retrieval_tags = metadata.get('retrieval_tags', [])
        if not retrieval_tags:
            warnings.append("No retrieval tags found")
            score_adjustment -= 0.1
        elif len(retrieval_tags) >= 2:
            score_adjustment += 0.1
        
        validation_metadata['retrieval_tags_count'] = len(retrieval_tags)
        
        # Check quality score
        quality_score = metadata.get('quality_score', 0)
        validation_metadata['quality_score'] = quality_score
        
        if quality_score < self.min_quality_score:
            warnings.append(f"Low quality score: {quality_score:.2f}")
            score_adjustment -= 0.2
        elif quality_score > 0.8:
            score_adjustment += 0.1
        
        return {
            'errors': errors,
            'warnings': warnings,
            'score_adjustment': score_adjustment,
            'metadata': validation_metadata
        }
    
    def _validate_compliance(self, content: str) -> Dict[str, Any]:
        """Validate chunk content for compliance."""
        errors = []
        warnings = []
        score_adjustment = 0.0
        metadata = {}
        
        # Check for advisory language
        advice_matches = re.findall(self.compliance_patterns['advice_language'], content, re.IGNORECASE)
        if advice_matches:
            errors.append(f"Advisory language detected: {len(advice_matches)} instances")
            score_adjustment -= 0.5
            metadata['advice_matches'] = advice_matches
        
        # Check for personal data
        personal_data_matches = re.findall(self.compliance_patterns['personal_data'], content)
        if personal_data_matches:
            errors.append(f"Personal data detected: {len(personal_data_matches)} instances")
            score_adjustment -= 0.5
            metadata['personal_data_matches'] = personal_data_matches
        
        # Check for promotional content
        promo_matches = re.findall(self.compliance_patterns['promotional_content'], content, re.IGNORECASE)
        if promo_matches:
            warnings.append(f"Promotional content detected: {len(promo_matches)} instances")
            score_adjustment -= 0.2
            metadata['promotional_matches'] = promo_matches
        
        # Check for speculative content
        speculative_matches = re.findall(self.compliance_patterns['speculative_content'], content, re.IGNORECASE)
        if speculative_matches:
            warnings.append(f"Speculative content detected: {len(speculative_matches)} instances")
            score_adjustment -= 0.2
            metadata['speculative_matches'] = speculative_matches
        
        # Check for facts-only compliance
        if not errors and not warnings:
            score_adjustment += 0.2
            metadata['compliance_status'] = 'compliant'
        else:
            metadata['compliance_status'] = 'non_compliant'
        
        return {
            'errors': errors,
            'warnings': warnings,
            'score_adjustment': score_adjustment,
            'metadata': metadata
        }
    
    def _validate_quality(self, chunk: Chunk) -> Dict[str, Any]:
        """Validate overall chunk quality."""
        errors = []
        warnings = []
        score_adjustment = 0.0
        metadata = {}
        
        # Check token count
        token_count = chunk.token_count
        metadata['token_count'] = token_count
        
        if token_count < 50:
            errors.append("Chunk has too few tokens")
            score_adjustment -= 0.5
        elif token_count < 200:
            warnings.append("Chunk has few tokens")
            score_adjustment -= 0.2
        elif 400 <= token_count <= 800:
            score_adjustment += 0.1
        
        # Check chunk context
        if not chunk.metadata.get('has_financial_context', False):
            warnings.append("Chunk lacks financial context")
            score_adjustment -= 0.1
        else:
            score_adjustment += 0.1
        
        # Check overlap information
        if chunk.overlap_info:
            score_adjustment += 0.05
            metadata['has_overlap'] = True
        else:
            metadata['has_overlap'] = False
        
        # Check sentence count
        sentence_count = chunk.metadata.get('sentence_count', 0)
        metadata['sentence_count'] = sentence_count
        
        if sentence_count == 0:
            warnings.append("No sentences detected")
            score_adjustment -= 0.1
        elif sentence_count >= 2:
            score_adjustment += 0.05
        
        # Check financial data presence
        financial_data = chunk.metadata.get('financial_data', {})
        financial_data_count = len(financial_data)
        metadata['financial_data_count'] = financial_data_count
        
        if financial_data_count == 0:
            warnings.append("No financial data extracted")
            score_adjustment -= 0.1
        elif financial_data_count >= 2:
            score_adjustment += 0.1
        
        return {
            'errors': errors,
            'warnings': warnings,
            'score_adjustment': score_adjustment,
            'metadata': metadata
        }
    
    def _validate_size(self, chunk: Chunk) -> Dict[str, Any]:
        """Validate chunk size constraints."""
        errors = []
        warnings = []
        score_adjustment = 0.0
        metadata = {}
        
        token_count = chunk.token_count
        metadata['token_count'] = token_count
        
        # Check against size limits
        if token_count < self.min_chunk_size:
            errors.append(f"Chunk too small: {token_count} tokens < {self.min_chunk_size}")
            score_adjustment -= 0.3
        elif token_count > self.max_chunk_size:
            errors.append(f"Chunk too large: {token_count} tokens > {self.max_chunk_size}")
            score_adjustment -= 0.3
        elif 400 <= token_count <= 800:
            score_adjustment += 0.1
        
        # Size categorization
        if token_count < 300:
            size_category = 'small'
        elif token_count <= 800:
            size_category = 'medium'
        else:
            size_category = 'large'
        
        metadata['size_category'] = size_category
        
        return {
            'errors': errors,
            'warnings': warnings,
            'score_adjustment': score_adjustment,
            'metadata': metadata
        }
    
    def validate_chunks_batch(self, chunks: List[Chunk]) -> List[ValidationResult]:
        """
        Validate multiple chunks.
        
        Args:
            chunks: List of chunks to validate
            
        Returns:
            List of validation results
        """
        logger.info(f"Starting batch validation of {len(chunks)} chunks")
        
        validation_results = []
        batch_stats = {
            'total_chunks': len(chunks),
            'valid_chunks': 0,
            'invalid_chunks': 0,
            'warning_chunks': 0,
            'avg_score': 0.0,
            'common_errors': {},
            'common_warnings': {}
        }
        
        for i, chunk in enumerate(chunks):
            try:
                result = self.validate_chunk(chunk)
                validation_results.append(result)
                
                # Update statistics
                if result.status == ValidationStatus.VALID:
                    batch_stats['valid_chunks'] += 1
                elif result.status == ValidationStatus.INVALID:
                    batch_stats['invalid_chunks'] += 1
                else:
                    batch_stats['warning_chunks'] += 1
                
                # Track common errors and warnings
                for error in result.errors:
                    batch_stats['common_errors'][error] = batch_stats['common_errors'].get(error, 0) + 1
                
                for warning in result.warnings:
                    batch_stats['common_warnings'][warning] = batch_stats['common_warnings'].get(warning, 0) + 1
                
                logger.debug(f"Validated chunk {i+1}/{len(chunks)}: {result.status.value}")
                
            except Exception as e:
                logger.error(f"Failed to validate chunk {i+1}: {e}")
                # Create error result
                error_result = ValidationResult(
                    status=ValidationStatus.INVALID,
                    score=0.0,
                    errors=[f"Validation failed: {str(e)}"],
                    warnings=[],
                    metadata={'validation_error': True}
                )
                validation_results.append(error_result)
                batch_stats['invalid_chunks'] += 1
        
        # Calculate average score
        if validation_results:
            batch_stats['avg_score'] = sum(result.score for result in validation_results) / len(validation_results)
        
        # Store batch statistics in metadata
        for result in validation_results:
            result.metadata['batch_statistics'] = batch_stats
        
        logger.info(f"Batch validation completed. "
                   f"Valid: {batch_stats['valid_chunks']}, "
                   f"Invalid: {batch_stats['invalid_chunks']}, "
                   f"Warnings: {batch_stats['warning_chunks']}, "
                   f"Avg score: {batch_stats['avg_score']:.2f}")
        
        return validation_results
    
    def filter_chunks_by_quality(self, chunks: List[Chunk], min_score: float = 0.5) -> Tuple[List[Chunk], List[Chunk]]:
        """
        Filter chunks based on quality score.
        
        Args:
            chunks: List of chunks to filter
            min_score: Minimum quality score threshold
            
        Returns:
            Tuple of (high_quality_chunks, low_quality_chunks)
        """
        logger.info(f"Filtering {len(chunks)} chunks with minimum score {min_score}")
        
        high_quality = []
        low_quality = []
        
        for chunk in chunks:
            result = self.validate_chunk(chunk)
            if result.score >= min_score:
                high_quality.append(chunk)
            else:
                low_quality.append(chunk)
        
        logger.info(f"Filtered chunks: {len(high_quality)} high quality, {len(low_quality)} low quality")
        return high_quality, low_quality
    
    def get_validation_summary(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Get summary of validation results.
        
        Args:
            validation_results: List of validation results
            
        Returns:
            Validation summary dictionary
        """
        if not validation_results:
            return {
                'total_chunks': 0,
                'valid_chunks': 0,
                'invalid_chunks': 0,
                'warning_chunks': 0,
                'avg_score': 0.0,
                'common_issues': {}
            }
        
        # Count by status
        status_counts = {
            ValidationStatus.VALID: 0,
            ValidationStatus.INVALID: 0,
            ValidationStatus.WARNING: 0
        }
        
        scores = []
        all_errors = []
        all_warnings = []
        
        for result in validation_results:
            status_counts[result.status] += 1
            scores.append(result.score)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        # Calculate statistics
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # Find common issues
        common_errors = {}
        for error in all_errors:
            common_errors[error] = common_errors.get(error, 0) + 1
        
        common_warnings = {}
        for warning in all_warnings:
            common_warnings[warning] = common_warnings.get(warning, 0) + 1
        
        # Sort by frequency
        common_errors = dict(sorted(common_errors.items(), key=lambda x: x[1], reverse=True))
        common_warnings = dict(sorted(common_warnings.items(), key=lambda x: x[1], reverse=True))
        
        return {
            'total_chunks': len(validation_results),
            'valid_chunks': status_counts[ValidationStatus.VALID],
            'invalid_chunks': status_counts[ValidationStatus.INVALID],
            'warning_chunks': status_counts[ValidationStatus.WARNING],
            'avg_score': avg_score,
            'min_score': min(scores) if scores else 0.0,
            'max_score': max(scores) if scores else 0.0,
            'common_errors': common_errors,
            'common_warnings': common_warnings,
            'validation_rate': status_counts[ValidationStatus.VALID] / len(validation_results)
        }


# Import datetime for validation timestamp
from datetime import datetime
