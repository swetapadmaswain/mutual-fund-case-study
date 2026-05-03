"""
Configuration settings for the Mutual Fund FAQ Assistant.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    pythonpath: str = "src"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Data Collection
    data_collection_delay: float = 1.0
    max_retries: int = 3
    timeout_seconds: int = 30
    
    # Source Validation
    allowed_domains: List[str] = ["groww.in"]
    ssl_verify: bool = True
    
    # Cache
    cache_ttl: int = 3600
    cache_dir: str = "cache"
    
    # Monitoring
    monitoring_enabled: bool = True
    metrics_port: int = 8000
    
    # HDFC Mutual Fund URLs
    hdfc_fund_urls: List[str] = [
        "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
    ]
    
    # User Agent for web scraping
    user_agent: str = "Mutual-Fund-FAQ-Assistant/1.0 (Educational Purpose)"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
