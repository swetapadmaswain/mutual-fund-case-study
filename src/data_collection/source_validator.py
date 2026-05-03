"""
Source validation for ensuring compliance and data quality.
"""
import re
from urllib.parse import urlparse
from typing import Dict, Any, List
import ssl
import socket
from datetime import datetime

from src.config.settings import settings
from src.utils.logger import logger
from src.utils.exceptions import SourceValidationError, ComplianceError


class SourceValidator:
    """Validates sources for compliance and data quality."""
    
    def __init__(self):
        """Initialize the source validator."""
        self.allowed_domains = settings.allowed_domains
        self.ssl_verify = settings.ssl_verify
    
    def validate_url(self, url: str) -> Dict[str, Any]:
        """
        Validate a URL against compliance requirements.
        
        Args:
            url: URL to validate
            
        Returns:
            Validation result dictionary
            
        Raises:
            SourceValidationError: If validation fails
        """
        logger.info(f"Validating URL: {url}")
        
        validation_result = {
            'url': url,
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'domain': None,
            'is_ssl': False,
            'is_allowed_domain': False
        }
        
        try:
            # Parse URL
            parsed_url = urlparse(url)
            validation_result['domain'] = parsed_url.netloc
            
            # Check if URL is properly formatted
            if not parsed_url.scheme or not parsed_url.netloc:
                validation_result['is_valid'] = False
                validation_result['errors'].append("Invalid URL format")
                raise SourceValidationError(f"Invalid URL format: {url}")
            
            # Check SSL
            if parsed_url.scheme == 'https':
                validation_result['is_ssl'] = True
            else:
                validation_result['warnings'].append("URL does not use HTTPS")
            
            # Check allowed domains
            if any(domain in parsed_url.netloc for domain in self.allowed_domains):
                validation_result['is_allowed_domain'] = True
            else:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Domain not in allowed list: {parsed_url.netloc}")
                raise SourceValidationError(f"Domain not allowed: {parsed_url.netloc}")
            
            # Additional SSL verification if enabled
            if self.ssl_verify and validation_result['is_ssl']:
                self._verify_ssl_certificate(parsed_url.netloc)
            
            logger.info(f"URL validation passed: {url}")
            return validation_result
            
        except Exception as e:
            logger.error(f"URL validation failed: {url} - {e}")
            validation_result['is_valid'] = False
            validation_result['errors'].append(str(e))
            raise SourceValidationError(f"URL validation failed: {e}")
    
    def _verify_ssl_certificate(self, hostname: str) -> None:
        """
        Verify SSL certificate for a hostname.
        
        Args:
            hostname: Hostname to verify
            
        Raises:
            SourceValidationError: If SSL verification fails
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check certificate expiration
                    if cert:
                        expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        if expiry_date < datetime.now():
                            raise SourceValidationError(f"SSL certificate expired for {hostname}")
                    
        except Exception as e:
            raise SourceValidationError(f"SSL verification failed for {hostname}: {e}")
    
    def validate_content(self, content: str, url: str) -> Dict[str, Any]:
        """
        Validate content for compliance and quality.
        
        Args:
            content: Content to validate
            url: Source URL
            
        Returns:
            Content validation result
            
        Raises:
            ComplianceError: If content violates compliance requirements
        """
        logger.info(f"Validating content from: {url}")
        
        validation_result = {
            'url': url,
            'content_length': len(content),
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'contains_advice': False,
            'contains_recommendations': False,
            'contains_personal_data': False,
            'quality_score': 0.0
        }
        
        # Check for advisory language
        advice_patterns = [
            r'\bshould\s+invest\b',
            r'\bwould\s+recommend\b',
            r'\badvice\b',
            r'\bsuggest\b.*\byou\b',
            r'\bgood\s+time\s+to\s+invest\b',
            r'\bbetter\s+to\s+invest\b',
            r'\bbest\s+fund\b'
        ]
        
        for pattern in advice_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                validation_result['contains_advice'] = True
                validation_result['warnings'].append(f"Potential advisory language detected: {pattern}")
        
        # Check for recommendation language
        recommendation_patterns = [
            r'\brecommend\b',
            r'\bpick\s+this\b',
            r'\bchoose\s+this\b',
            r'\bgood\s+choice\b',
            r'\bbest\s+option\b'
        ]
        
        for pattern in recommendation_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                validation_result['contains_recommendations'] = True
                validation_result['warnings'].append(f"Potential recommendation language detected: {pattern}")
        
        # Check for personal data patterns
        personal_data_patterns = [
            r'\b\d{4}\s*-\s*\d{4}\s*-\s*\d{4}\s*-\s*\d{4}\b',  # Credit card
            r'\b\d{2}[-/]\d{2}[-/]\d{4}\b',  # Date patterns
            r'\b[A-Za-z]{5}\d{4}[A-Za-z]\b',  # PAN-like patterns
            r'\b\d{12}\b',  # Aadhaar-like patterns
            r'\b\d{10}\b'   # Phone-like patterns
        ]
        
        for pattern in personal_data_patterns:
            if re.search(pattern, content):
                validation_result['contains_personal_data'] = True
                validation_result['errors'].append(f"Personal data pattern detected: {pattern}")
                validation_result['is_valid'] = False
        
        # Calculate quality score
        validation_result['quality_score'] = self._calculate_quality_score(content, validation_result)
        
        # Log validation results
        if validation_result['errors']:
            logger.error(f"Content validation failed for {url}: {validation_result['errors']}")
            raise ComplianceError(f"Content validation failed: {validation_result['errors']}")
        
        if validation_result['warnings']:
            logger.warning(f"Content validation warnings for {url}: {validation_result['warnings']}")
        
        logger.info(f"Content validation passed for: {url}")
        return validation_result
    
    def _calculate_quality_score(self, content: str, validation_result: Dict[str, Any]) -> float:
        """
        Calculate content quality score.
        
        Args:
            content: Content to analyze
            validation_result: Current validation result
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 1.0
        
        # Deduct points for issues
        if validation_result['contains_advice']:
            score -= 0.2
        
        if validation_result['contains_recommendations']:
            score -= 0.2
        
        if validation_result['contains_personal_data']:
            score -= 0.5
        
        # Content length factor
        content_length = len(content)
        if content_length < 100:
            score -= 0.3
        elif content_length < 500:
            score -= 0.1
        
        # Ensure score doesn't go below 0
        return max(0.0, score)
    
    def validate_fund_data(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate fund-specific metadata.
        
        Args:
            metadata: Fund metadata to validate
            
        Returns:
            Validation result for fund data
        """
        logger.info("Validating fund metadata")
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'missing_fields': [],
            'invalid_formats': []
        }
        
        # Required fields
        required_fields = ['fund_name', 'url']
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                validation_result['missing_fields'].append(field)
                validation_result['is_valid'] = False
        
        # Validate financial data formats
        financial_fields = ['expense_ratio', 'exit_load']
        for field in financial_fields:
            if field in metadata and metadata[field]:
                if not self._is_valid_percentage_format(metadata[field]):
                    validation_result['invalid_formats'].append(f"{field}: {metadata[field]}")
        
        # Validate amount fields
        amount_fields = ['min_sip']
        for field in amount_fields:
            if field in metadata and metadata[field]:
                if not self._is_valid_amount_format(metadata[field]):
                    validation_result['invalid_formats'].append(f"{field}: {metadata[field]}")
        
        if validation_result['errors'] or validation_result['missing_fields']:
            validation_result['is_valid'] = False
        
        return validation_result
    
    def _is_valid_percentage_format(self, value: str) -> bool:
        """Check if value is a valid percentage format."""
        if not isinstance(value, str):
            return False
        
        # Remove whitespace and check for percentage
        value = value.strip()
        return bool(re.match(r'^\d+\.?\d*%$', value))
    
    def _is_valid_amount_format(self, value: str) -> bool:
        """Check if value is a valid amount format."""
        if not isinstance(value, str):
            return False
        
        value = value.strip()
        # Check for patterns like ₹1000, 1000, 1,000, etc.
        return bool(re.match(r'^(₹\s*)?\d{1,3}(,\d{3})*(\.\d{2})?$', value))


def validate_sources_batch(urls: List[str]) -> Dict[str, Any]:
    """
    Validate a batch of URLs.
    
    Args:
        urls: List of URLs to validate
        
    Returns:
        Batch validation result
    """
    validator = SourceValidator()
    
    results = {
        'total_urls': len(urls),
        'valid_urls': 0,
        'invalid_urls': 0,
        'validation_results': [],
        'summary': {
            'ssl_enabled': 0,
            'allowed_domains': 0,
            'common_errors': {},
            'common_warnings': {}
        }
    }
    
    for url in urls:
        try:
            validation_result = validator.validate_url(url)
            results['validation_results'].append(validation_result)
            
            if validation_result['is_valid']:
                results['valid_urls'] += 1
                
                if validation_result['is_ssl']:
                    results['summary']['ssl_enabled'] += 1
                
                if validation_result['is_allowed_domain']:
                    results['summary']['allowed_domains'] += 1
            else:
                results['invalid_urls'] += 1
            
            # Track common errors and warnings
            for error in validation_result['errors']:
                results['summary']['common_errors'][error] = results['summary']['common_errors'].get(error, 0) + 1
            
            for warning in validation_result['warnings']:
                results['summary']['common_warnings'][warning] = results['summary']['common_warnings'].get(warning, 0) + 1
                
        except Exception as e:
            logger.error(f"Validation failed for {url}: {e}")
            results['invalid_urls'] += 1
            results['validation_results'].append({
                'url': url,
                'is_valid': False,
                'errors': [str(e)],
                'warnings': []
            })
    
    return results
