"""
Tests for source validator functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.data_collection.source_validator import SourceValidator, validate_sources_batch
from src.utils.exceptions import SourceValidationError, ComplianceError


class TestSourceValidator:
    """Test cases for SourceValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return SourceValidator()
    
    def test_validate_url_success(self, validator):
        """Test successful URL validation."""
        url = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        
        with patch('socket.create_connection'), \
             patch('ssl.create_default_context') as mock_ssl:
            
            mock_ssl.return_value.wrap_socket.return_value.getpeercert.return_value = {
                'notAfter': 'Dec 31 23:59:59 2025 GMT'
            }
            
            result = validator.validate_url(url)
            
            assert result['is_valid'] is True
            assert result['url'] == url
            assert result['domain'] == 'groww.in'
            assert result['is_ssl'] is True
            assert result['is_allowed_domain'] is True
            assert len(result['errors']) == 0
    
    def test_validate_url_invalid_format(self, validator):
        """Test URL validation with invalid format."""
        url = "invalid-url"
        
        with pytest.raises(SourceValidationError) as exc_info:
            validator.validate_url(url)
        
        assert "Invalid URL format" in str(exc_info.value)
    
    def test_validate_url_unallowed_domain(self, validator):
        """Test URL validation with unallowed domain."""
        url = "https://example.com/fund"
        
        with pytest.raises(SourceValidationError) as exc_info:
            validator.validate_url(url)
        
        assert "Domain not allowed" in str(exc_info.value)
    
    def test_validate_url_ssl_verification_failure(self, validator):
        """Test SSL verification failure."""
        url = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        
        with patch('socket.create_connection'), \
             patch('ssl.create_default_context') as mock_ssl:
            
            mock_ssl.return_value.wrap_socket.side_effect = Exception("SSL error")
            
            with pytest.raises(SourceValidationError) as exc_info:
                validator.validate_url(url)
            
            assert "SSL verification failed" in str(exc_info.value)
    
    def test_validate_content_success(self, validator):
        """Test successful content validation."""
        content = "This fund has an expense ratio of 0.85% and minimum SIP of ₹500."
        url = "https://groww.in/fund"
        
        result = validator.validate_content(content, url)
        
        assert result['is_valid'] is True
        assert result['url'] == url
        assert result['content_length'] == len(content)
        assert result['contains_advice'] is False
        assert result['contains_recommendations'] is False
        assert result['contains_personal_data'] is False
        assert result['quality_score'] > 0.8
    
    def test_validate_content_advice_language(self, validator):
        """Test content validation with advisory language."""
        content = "You should invest in this fund as it is a good choice."
        url = "https://groww.in/fund"
        
        result = validator.validate_content(content, url)
        
        assert result['contains_advice'] is True
        assert result['contains_recommendations'] is True
        assert len(result['warnings']) > 0
        assert result['quality_score'] < 1.0
    
    def test_validate_content_personal_data(self, validator):
        """Test content validation with personal data."""
        content = "Contact us at 9876543210 or email with PAN ABCDE1234F."
        url = "https://groww.in/fund"
        
        with pytest.raises(ComplianceError) as exc_info:
            validator.validate_content(content, url)
        
        assert "Personal data pattern detected" in str(exc_info.value)
    
    def test_validate_content_short_content(self, validator):
        """Test content validation with very short content."""
        content = "Short"
        url = "https://groww.in/fund"
        
        result = validator.validate_content(content, url)
        
        assert result['quality_score'] < 0.8
    
    def test_calculate_quality_score(self, validator):
        """Test quality score calculation."""
        # Perfect content
        content = "This fund has expense ratio of 0.85% and minimum SIP of ₹500."
        validation_result = {
            'contains_advice': False,
            'contains_recommendations': False,
            'contains_personal_data': False
        }
        
        score = validator._calculate_quality_score(content, validation_result)
        assert score == 1.0
        
        # Content with advice
        validation_result['contains_advice'] = True
        score = validator._calculate_quality_score(content, validation_result)
        assert score == 0.8
        
        # Content with personal data
        validation_result['contains_personal_data'] = True
        score = validator._calculate_quality_score(content, validation_result)
        assert score == 0.3
    
    def test_validate_fund_data_success(self, validator):
        """Test successful fund data validation."""
        metadata = {
            'fund_name': 'HDFC Mid Cap Fund',
            'url': 'https://groww.in/fund',
            'expense_ratio': '0.85%',
            'exit_load': '1%',
            'min_sip': '₹500'
        }
        
        result = validator.validate_fund_data(metadata)
        
        assert result['is_valid'] is True
        assert len(result['errors']) == 0
        assert len(result['missing_fields']) == 0
        assert len(result['invalid_formats']) == 0
    
    def test_validate_fund_data_missing_fields(self, validator):
        """Test fund data validation with missing fields."""
        metadata = {
            'url': 'https://groww.in/fund'
        }
        
        result = validator.validate_fund_data(metadata)
        
        assert result['is_valid'] is False
        assert 'fund_name' in result['missing_fields']
    
    def test_validate_fund_data_invalid_formats(self, validator):
        """Test fund data validation with invalid formats."""
        metadata = {
            'fund_name': 'HDFC Mid Cap Fund',
            'url': 'https://groww.in/fund',
            'expense_ratio': 'invalid',  # Should be percentage
            'min_sip': 'invalid'  # Should be amount
        }
        
        result = validator.validate_fund_data(metadata)
        
        assert len(result['invalid_formats']) > 0
        assert any('expense_ratio' in fmt for fmt in result['invalid_formats'])
        assert any('min_sip' in fmt for fmt in result['invalid_formats'])
    
    def test_is_valid_percentage_format(self, validator):
        """Test percentage format validation."""
        assert validator._is_valid_percentage_format("0.85%") is True
        assert validator._is_valid_percentage_format("1.5%") is True
        assert validator._is_valid_percentage_format("85%") is True
        assert validator._is_valid_percentage_format("0.85") is False
        assert validator._is_valid_percentage_format("invalid") is False
        assert validator._is_valid_percentage_format("") is False
    
    def test_is_valid_amount_format(self, validator):
        """Test amount format validation."""
        assert validator._is_valid_amount_format("₹500") is True
        assert validator._is_valid_amount_format("₹1,000") is True
        assert validator._is_valid_amount_format("500") is True
        assert validator._is_valid_amount_format("1,000") is True
        assert validator._is_valid_amount_format("₹500.50") is True
        assert validator._is_valid_amount_format("invalid") is False
        assert validator._is_valid_amount_format("") is False
    
    def test_validate_sources_batch(self):
        """Test batch URL validation."""
        urls = [
            "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
            "https://invalid.com/fund"
        ]
        
        with patch('socket.create_connection'), \
             patch('ssl.create_default_context') as mock_ssl:
            
            mock_ssl.return_value.wrap_socket.return_value.getpeercert.return_value = {
                'notAfter': 'Dec 31 23:59:59 2025 GMT'
            }
            
            results = validate_sources_batch(urls)
            
            assert results['total_urls'] == 3
            assert results['valid_urls'] == 2
            assert results['invalid_urls'] == 1
            assert len(results['validation_results']) == 3
            assert results['summary']['allowed_domains'] == 2
