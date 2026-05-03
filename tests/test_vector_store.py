"""
Tests for Phase 2.2 vector store components.
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from src.rag.vector_store.embeddings import EmbeddingModel, EmbeddingCache, EmbeddingService
from src.rag.vector_store.vector_database import VectorDatabase, HierarchicalVectorDB
from src.rag.vector_store.hierarchical_indexing import HierarchicalIndexer
from src.rag.vector_store.storage_optimizer import StorageOptimizer
from src.rag.chunking.chunker import Chunk


class TestEmbeddingModel:
    """Test cases for EmbeddingModel class."""
    
    @pytest.fixture
    def embedding_model(self):
        """Create an embedding model instance for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield EmbeddingModel(
                model_name="BAAI/bge-small-en",
                device="cpu",
                batch_size=4,
                cache_dir=temp_dir
            )
    
    @pytest.fixture
    def sample_texts(self):
        """Sample texts for testing."""
        return [
            "HDFC Mid Cap Fund has expense ratio of 0.85%",
            "Minimum SIP amount is Rs. 500",
            "Current NAV is Rs. 145.67"
        ]
    
    def test_initialization(self, embedding_model):
        """Test embedding model initialization."""
        assert embedding_model.model_name == "BAAI/bge-small-en"
        assert embedding_model.device == "cpu"
        assert embedding_model.batch_size == 4
        assert embedding_model.embedding_dim == 384
        assert embedding_model.model is None  # Not loaded yet
    
    @patch('src.rag.vector_store.embeddings.SentenceTransformer')
    def test_load_model(self, mock_transformer, embedding_model):
        """Test model loading."""
        # Mock the transformer
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model
        
        embedding_model.load_model()
        
        assert embedding_model.model is not None
        assert embedding_model.embedding_dim == 384
        mock_transformer.assert_called_once()
    
    def test_prepare_text(self, embedding_model):
        """Test text preparation."""
        # Normal text
        text = "This is a normal text"
        result = embedding_model._prepare_text(text)
        assert result == text
        
        # Empty text
        result = embedding_model._prepare_text("")
        assert result == ""
        
        # Long text
        long_text = "a" * 1000
        result = embedding_model._prepare_text(long_text)
        assert len(result) <= 512
    
    def test_get_embedding_info(self, embedding_model):
        """Test embedding info retrieval."""
        info = embedding_model.get_embedding_info()
        
        assert "model_name" in info
        assert "embedding_dimension" in info
        assert "device" in info
        assert "batch_size" in info
        assert "model_loaded" in info
        assert "cache_dir" in info
        
        assert info["model_name"] == "BAAI/bge-small-en"
        assert info["embedding_dimension"] == 384


class TestEmbeddingCache:
    """Test cases for EmbeddingCache class."""
    
    @pytest.fixture
    def embedding_cache(self):
        """Create an embedding cache instance for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield EmbeddingCache(cache_dir=temp_dir)
    
    def test_generate_cache_key(self, embedding_cache):
        """Test cache key generation."""
        texts = ["text1", "text2"]
        model_name = "test-model"
        
        key1 = embedding_cache.generate_cache_key(texts, model_name)
        key2 = embedding_cache.generate_cache_key(texts, model_name)
        
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length
        
        # Different inputs should generate different keys
        key3 = embedding_cache.generate_cache(["different"], model_name)
        assert key1 != key3
    
    def test_cache_embeddings(self, embedding_cache):
        """Test caching embeddings."""
        cache_key = "test_key"
        embeddings = [np.array([1.0, 2.0, 3.0]), np.array([4.0, 5.0, 6.0])]
        texts = ["text1", "text2"]
        model_name = "test-model"
        
        # Cache embeddings
        embedding_cache.cache_embeddings(cache_key, embeddings, texts, model_name)
        
        # Verify cache index updated
        assert cache_key in embedding_cache.cache_index
        assert embedding_cache.cache_index[cache_key]["model_name"] == model_name
        assert embedding_cache.cache_index[cache_key]["text_count"] == 2
    
    def test_get_cached_embeddings(self, embedding_cache):
        """Test retrieving cached embeddings."""
        cache_key = "test_key"
        original_embeddings = [np.array([1.0, 2.0, 3.0])]
        texts = ["text1"]
        model_name = "test-model"
        
        # Cache embeddings
        embedding_cache.cache_embeddings(cache_key, original_embeddings, texts, model_name)
        
        # Retrieve cached embeddings
        cached_embeddings = embedding_cache.get_cached_embeddings(cache_key)
        
        assert cached_embeddings is not None
        assert len(cached_embeddings) == 1
        np.testing.assert_array_equal(cached_embeddings[0], original_embeddings[0])
    
    def test_get_cache_stats(self, embedding_cache):
        """Test cache statistics."""
        # Add some cached items
        for i in range(3):
            cache_key = f"test_key_{i}"
            embeddings = [np.array([float(i), float(i+1)])]
            texts = [f"text_{i}"]
            embedding_cache.cache_embeddings(cache_key, embeddings, texts, "test-model")
        
        stats = embedding_cache.get_cache_stats()
        
        assert stats["total_cached_files"] == 3
        assert stats["models_used"] == ["test-model"]
        assert "cache_directory" in stats


class TestEmbeddingService:
    """Test cases for EmbeddingService class."""
    
    @pytest.fixture
    def embedding_service(self):
        """Create an embedding service instance for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield EmbeddingService(
                model_name="BAAI/bge-small-en",
                device="cpu",
                batch_size=4,
                enable_cache=True
            )
    
    @pytest.fixture
    def sample_texts(self):
        """Sample texts for testing."""
        return [
            "HDFC Mid Cap Fund expense ratio",
            "SIP investment details",
            "NAV and performance data"
        ]
    
    @patch('src.rag.vector_store.embeddings.SentenceTransformer')
    async def test_embed_texts_async(self, mock_transformer, embedding_service, sample_texts):
        """Test asynchronous text embedding."""
        # Mock the transformer
        mock_model = Mock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])
        mock_model.get_sentence_embedding_dimension.return_value = 3
        mock_transformer.return_value = mock_model
        
        # Load model
        embedding_service.embedding_model.load_model()
        
        # Embed texts
        embeddings = await embedding_service.embed_texts_async(sample_texts)
        
        assert len(embeddings) == 3
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)
        assert embeddings[0].shape[0] == 3
    
    def test_get_service_info(self, embedding_service):
        """Test service information retrieval."""
        info = embedding_service.get_service_info()
        
        assert "model_name" in info
        assert "embedding_dimension" in info
        assert "cache_enabled" in info
        assert "device" in info
        assert "batch_size" in info
        
        assert info["cache_enabled"] is True


class TestVectorDatabase:
    """Test cases for VectorDatabase class."""
    
    @pytest.fixture
    def vector_database(self):
        """Create a vector database instance for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield VectorDatabase(
                collection_name="test_collection",
                persist_directory=temp_dir,
                embedding_dimension=384
            )
    
    @pytest.fixture
    def sample_chunks(self):
        """Sample chunks for testing."""
        return [
            Chunk(
                chunk_id="chunk_1",
                content="HDFC Mid Cap Fund has expense ratio of 0.85%",
                metadata={"fund_name": "HDFC Mid Cap", "content_type": "expense_ratio"},
                chunk_index=0,
                total_chunks=2,
                token_count=15,
                source_document_id="doc_1"
            ),
            Chunk(
                chunk_id="chunk_2",
                content="Minimum SIP amount is Rs. 500",
                metadata={"fund_name": "HDFC Mid Cap", "content_type": "sip"},
                chunk_index=1,
                total_chunks=2,
                token_count=10,
                source_document_id="doc_1"
            )
        ]
    
    @pytest.fixture
    def sample_embeddings(self):
        """Sample embeddings for testing."""
        return [
            np.array([0.1, 0.2, 0.3, 0.4]),
            np.array([0.5, 0.6, 0.7, 0.8])
        ]
    
    @patch('src.rag.vector_store.vector_database.chromadb')
    def test_initialize_client(self, mock_chromadb, vector_database):
        """Test ChromaDB client initialization."""
        # Mock ChromaDB components
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_collection.side_effect = Exception("Collection not found")
        mock_client.create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client
        
        # Initialize
        vector_database._initialize_client()
        
        assert vector_database.client is not None
        assert vector_database.collection is not None
        mock_chromadb.PersistentClient.assert_called_once()
    
    @patch('src.rag.vector_store.vector_database.chromadb')
    def test_add_chunks(self, mock_chromadb, vector_database, sample_chunks, sample_embeddings):
        """Test adding chunks to database."""
        # Mock ChromaDB
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client
        
        vector_database.client = mock_client
        vector_database.collection = mock_collection
        
        # Add chunks
        doc_ids = vector_database.add_chunks(sample_chunks, sample_embeddings)
        
        assert len(doc_ids) == 2
        mock_collection.add.assert_called_once()
        
        # Verify call arguments
        call_args = mock_collection.add.call_args
        assert len(call_args[1]['ids']) == 2
        assert len(call_args[1]['documents']) == 2
        assert len(call_args[1]['metadatas']) == 2
        assert len(call_args[1]['embeddings']) == 2
    
    @patch('src.rag.vector_store.vector_database.chromadb')
    def test_search(self, mock_chromadb, vector_database):
        """Test searching in database."""
        # Mock ChromaDB
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "ids": [["doc_1", "doc_2"]],
            "documents": [["doc1_content", "doc2_content"]],
            "metadatas": [[{"meta1": "value1"}, {"meta2": "value2"}]],
            "distances": [[0.1, 0.3]]
        }
        mock_client.get_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client
        
        vector_database.client = mock_client
        vector_database.collection = mock_collection
        
        # Search
        query_embedding = np.array([0.1, 0.2, 0.3, 0.4])
        results = vector_database.search(query_embedding, top_k=5)
        
        assert len(results) == 2
        assert results[0]["similarity"] == 0.9  # 1 - 0.1
        assert results[1]["similarity"] == 0.7  # 1 - 0.3
    
    def test_get_collection_stats(self, vector_database):
        """Test collection statistics."""
        # Mock collection
        vector_database.collection = Mock()
        vector_database.collection.count.return_value = 10
        vector_database.collection.metadata = {"description": "Test collection"}
        vector_database.collection.get.return_value = {
            "metadatas": [{"type": "expense"}, {"type": "sip"}]
        }
        
        stats = vector_database.get_collection_stats()
        
        assert stats["document_count"] == 10
        assert stats["collection_name"] == "test_collection"
        assert stats["embedding_dimension"] == 384


class TestHierarchicalIndexer:
    """Test cases for HierarchicalIndexer class."""
    
    @pytest.fixture
    def hierarchical_indexer(self):
        """Create a hierarchical indexer instance for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield HierarchicalIndexer(index_path=temp_dir)
    
    @pytest.fixture
    def sample_chunks(self):
        """Sample chunks for testing."""
        return [
            Chunk(
                chunk_id="chunk_1",
                content="HDFC Mid Cap Fund expense ratio is 0.85%",
                metadata={
                    "fund_name": "HDFC Mid Cap Fund",
                    "fund_type": "mid cap",
                    "content_type": "expense_ratio",
                    "hierarchical_keys": ["fund:hdfc_mid_cap", "type:mid_cap", "content:expense_ratio"]
                },
                chunk_index=0,
                total_chunks=3,
                token_count=12,
                source_document_id="doc_1"
            ),
            Chunk(
                chunk_id="chunk_2",
                content="HDFC Large Cap Fund SIP amount is Rs. 500",
                metadata={
                    "fund_name": "HDFC Large Cap Fund",
                    "fund_type": "large cap",
                    "content_type": "sip",
                    "hierarchical_keys": ["fund:hdfc_large_cap", "type:large_cap", "content:sip"]
                },
                chunk_index=1,
                total_chunks=3,
                token_count=10,
                source_document_id="doc_2"
            ),
            Chunk(
                chunk_id="chunk_3",
                content="HDFC Mid Cap Fund NAV is Rs. 145.67",
                metadata={
                    "fund_name": "HDFC Mid Cap Fund",
                    "fund_type": "mid cap",
                    "content_type": "nav",
                    "hierarchical_keys": ["fund:hdfc_mid_cap", "type:mid_cap", "content:nav"]
                },
                chunk_index=2,
                total_chunks=3,
                token_count=8,
                source_document_id="doc_1"
            )
        ]
    
    def test_build_index(self, hierarchical_indexer, sample_chunks):
        """Test building hierarchical index."""
        hierarchical_indexer.build_index(sample_chunks)
        
        # Check fund hierarchy
        assert len(hierarchical_indexer.fund_hierarchy) == 2
        assert "hdfc_mid_cap_fund" in hierarchical_indexer.fund_hierarchy
        assert "hdfc_large_cap_fund" in hierarchical_indexer.fund_hierarchy
        
        # Check type hierarchy
        assert len(hierarchical_indexer.type_hierarchy) == 2
        assert "mid_cap" in hierarchical_indexer.type_hierarchy
        assert "large_cap" in hierarchical_indexer.type_hierarchy
        
        # Check content hierarchy
        assert len(hierarchical_indexer.content_hierarchy) == 3
        assert "expense_ratio" in hierarchical_indexer.content_hierarchy
        assert "sip" in hierarchical_indexer.content_hierarchy
        assert "nav" in hierarchical_indexer.content_hierarchy
    
    def test_extract_fund_name(self, hierarchical_indexer):
        """Test fund name extraction."""
        # Test with fund_name in metadata
        metadata = {"fund_name": "HDFC Mid Cap Fund"}
        fund_name = hierarchical_indexer._extract_fund_name(metadata)
        assert fund_name == "hdfc mid cap fund"
        
        # Test with hierarchical keys
        metadata = {"hierarchical_keys": ["fund:hdfc_mid_cap", "type:mid_cap"]}
        fund_name = hierarchical_indexer._extract_fund_name(metadata)
        assert fund_name == "hdfc_mid_cap"
        
        # Test with no fund name
        metadata = {"other_field": "value"}
        fund_name = hierarchical_indexer._extract_fund_name(metadata)
        assert fund_name is None
    
    def test_extract_fund_type(self, hierarchical_indexer):
        """Test fund type extraction."""
        # Test with fund_type in metadata
        metadata = {"fund_type": "mid cap"}
        fund_type = hierarchical_indexer._extract_fund_type(metadata, "")
        assert fund_type == "mid_cap"
        
        # Test with content extraction
        content = "This is a mid cap fund with good performance"
        fund_type = hierarchical_indexer._extract_fund_type({}, content)
        assert fund_type == "mid_cap"
        
        # Test with hierarchical keys
        metadata = {"hierarchical_keys": ["fund:hdfc", "type:large_cap"]}
        fund_type = hierarchical_indexer._extract_fund_type(metadata, "")
        assert fund_type == "large_cap"
    
    def test_get_funds_by_type(self, hierarchical_indexer, sample_chunks):
        """Test getting funds by type."""
        hierarchical_indexer.build_index(sample_chunks)
        
        mid_cap_funds = hierarchical_indexer.get_funds_by_type("mid_cap")
        assert len(mid_cap_funds) == 1
        assert "hdfc_mid_cap_fund" in mid_cap_funds
        
        large_cap_funds = hierarchical_indexer.get_funds_by_type("large_cap")
        assert len(large_cap_funds) == 1
        assert "hdfc_large_cap_fund" in large_cap_funds
    
    def test_get_chunks_by_content_type(self, hierarchical_indexer, sample_chunks):
        """Test getting chunks by content type."""
        hierarchical_indexer.build_index(sample_chunks)
        
        expense_chunks = hierarchical_indexer.get_chunks_by_content_type("expense_ratio")
        assert len(expense_chunks) == 1
        assert "chunk_1" in expense_chunks
        
        sip_chunks = hierarchical_indexer.get_chunks_by_content_type("sip")
        assert len(sip_chunks) == 1
        assert "chunk_2" in sip_chunks
    
    def test_route_queries(self, hierarchical_indexer, sample_chunks):
        """Test query routing."""
        hierarchical_indexer.build_index(sample_chunks)
        
        # Test fund-specific query
        routing = hierarchical_indexer.route_queries("HDFC Mid Cap Fund expense ratio")
        assert routing["query_type"] == "fund_specific"
        assert "hdfc_mid_cap_fund" in routing["target_funds"]
        assert "expense_ratio" in routing["target_content_types"]
        
        # Test type-specific query
        routing = hierarchical_indexer.route_queries("mid cap funds")
        assert routing["query_type"] == "type_specific"
        assert "mid_cap" in routing["target_types"]
        
        # Test content-specific query
        routing = hierarchical_indexer.route_queries("What is the SIP amount?")
        assert routing["query_type"] == "content_specific"
        assert "sip" in routing["target_content_types"]
    
    def test_get_fund_statistics(self, hierarchical_indexer, sample_chunks):
        """Test fund statistics."""
        hierarchical_indexer.build_index(sample_chunks)
        
        stats = hierarchical_indexer.get_fund_statistics()
        
        assert stats["total_funds"] == 2
        assert stats["total_documents"] == 2
        assert stats["total_chunks"] == 3
        assert "mid_cap" in stats["fund_types"]
        assert "large_cap" in stats["fund_types"]
        assert stats["average_chunks_per_fund"] == 1.5


class TestStorageOptimizer:
    """Test cases for StorageOptimizer class."""
    
    @pytest.fixture
    def storage_optimizer(self):
        """Create a storage optimizer instance for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield StorageOptimizer(
                storage_path=temp_dir,
                compression_enabled=True,
                backup_enabled=True
            )
    
    def test_initialization(self, storage_optimizer):
        """Test storage optimizer initialization."""
        assert storage_optimizer.compression_enabled is True
        assert storage_optimizer.backup_enabled is True
        assert storage_optimizer.compression_threshold_mb == 100
        assert storage_optimizer.backup_retention_days == 30
    
    def test_compress_vectors(self, storage_optimizer):
        """Test vector compression."""
        # Create test vectors
        vectors = [
            np.array([1.0, 2.0, 3.0, 4.0]),
            np.array([5.0, 6.0, 7.0, 8.0]),
            np.array([9.0, 10.0, 11.0, 12.0])
        ]
        
        # Test without compression (ratio >= 1.0)
        result = storage_optimizer.compress_vectors(vectors, compression_ratio=1.0)
        assert len(result) == len(vectors)
        
        # Test with compression
        with patch('src.rag.vector_store.storage_optimizer.PCA') as mock_pca:
            mock_pca_instance = Mock()
            mock_pca_instance.fit_transform.return_value = np.array([
                [1.1, 2.1, 3.1],
                [5.1, 6.1, 7.1],
                [9.1, 10.1, 11.1]
            ])
            mock_pca_instance.explained_variance_ratio_.sum.return_value = 0.95
            mock_pca.return_value = mock_pca_instance
            
            result = storage_optimizer.compress_vectors(vectors, compression_ratio=0.75)
            
            assert len(result) == 3
            assert result[0].shape[1] == 3  # Compressed from 4 to 3 dimensions
    
    def test_quantize_vectors(self, storage_optimizer):
        """Test vector quantization."""
        vectors = [
            np.array([0.5, -0.3, 0.8, -0.1]),
            np.array([1.0, 0.0, -1.0, 0.5])
        ]
        
        # Test 8-bit quantization
        quantized = storage_optimizer.quantize_vectors(vectors, bits=8)
        assert len(quantized) == 2
        assert quantized[0].dtype == np.float32  # Should be normalized back to float
        
        # Test 16-bit quantization
        quantized = storage_optimizer.quantize_vectors(vectors, bits=16)
        assert len(quantized) == 2
        
        # Test invalid bits
        with pytest.raises(ValueError):
            storage_optimizer.quantize_vectors(vectors, bits=12)
    
    def test_compress_file(self, storage_optimizer):
        """Test file compression."""
        # Create a test file
        test_file = storage_optimizer.storage_path / "test_file.txt"
        test_content = "This is a test file content for compression testing." * 1000
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Compress the file
        compressed_file = storage_optimizer.compress_file(test_file)
        
        assert compressed_file is not None
        assert compressed_file.exists()
        assert compressed_file.suffix == '.gz'
        
        # Verify compressed content
        import gzip
        with gzip.open(compressed_file, 'rt') as f:
            decompressed_content = f.read()
        
        assert decompressed_content == test_content
    
    def test_setup_backup_procedures(self, storage_optimizer):
        """Test backup procedures setup."""
        backup_config = storage_optimizer.setup_backup_procedures()
        
        assert backup_config["backup_enabled"] is True
        assert "backup_directory" in backup_config
        assert backup_config["backup_retention_days"] == 30
        assert backup_config["compression_enabled"] is True
        
        # Check if backup directory was created
        backup_dir = storage_optimizer.storage_path / "backups"
        assert backup_dir.exists()
    
    def test_configure_retention_policies(self, storage_optimizer):
        """Test retention policies configuration."""
        retention_config = storage_optimizer.configure_retention_policies()
        
        assert "backup_retention_days" in retention_config
        assert "cache_retention_days" in retention_config
        assert "policies" in retention_config
        
        policies = retention_config["policies"]
        assert "backups" in policies
        assert "cache" in policies
        assert "logs" in policies
        assert "temp" in policies
    
    def test_monitor_storage_usage(self, storage_optimizer):
        """Test storage usage monitoring."""
        # Create some test files
        test_file1 = storage_optimizer.storage_path / "file1.txt"
        test_file2 = storage_optimizer.storage_path / "file2.json"
        
        test_file1.write_text("Test content 1")
        test_file2.write_text('{"key": "value"}')
        
        # Create a subdirectory
        sub_dir = storage_optimizer.storage_path / "subdir"
        sub_dir.mkdir()
        
        usage_stats = storage_optimizer.monitor_storage_usage()
        
        assert usage_stats["total_size_mb"] > 0
        assert usage_stats["file_count"] >= 2
        assert usage_stats["directory_count"] >= 1
        assert "file_type_distribution" in usage_stats
        assert "age_distribution" in usage_stats
        assert ".txt" in usage_stats["file_type_distribution"]
        assert ".json" in usage_stats["file_type_distribution"]


class TestIntegration:
    """Integration tests for Phase 2.2 components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_embedding_pipeline(self):
        """Test end-to-end embedding pipeline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create embedding service
            embedding_service = EmbeddingService(
                model_name="BAAI/bge-small-en",
                device="cpu",
                batch_size=2,
                enable_cache=True,
                cache_dir=temp_dir
            )
            
            # Mock the transformer
            with patch('src.rag.vector_store.embeddings.SentenceTransformer') as mock_transformer:
                mock_model = Mock()
                mock_model.encode.return_value = np.array([
                    [0.1, 0.2, 0.3],
                    [0.4, 0.5, 0.6],
                    [0.7, 0.8, 0.9]
                ])
                mock_model.get_sentence_embedding_dimension.return_value = 3
                mock_transformer.return_value = mock_model
                
                # Load model
                embedding_service.embedding_model.load_model()
                
                # Test embedding generation
                texts = [
                    "HDFC Mid Cap Fund expense ratio",
                    "SIP investment details",
                    "NAV performance data"
                ]
                
                embeddings = await embedding_service.embed_texts_async(texts)
                
                assert len(embeddings) == 3
                assert all(emb.shape[0] == 3 for emb in embeddings)
                
                # Test caching
                cached_embeddings = await embedding_service.embed_texts_async(texts)
                assert len(cached_embeddings) == 3
    
    def test_hierarchical_indexing_integration(self):
        """Test hierarchical indexing integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create indexer
            indexer = HierarchicalIndexer(index_path=temp_dir)
            
            # Create test chunks
            chunks = [
                Chunk(
                    chunk_id="chunk_1",
                    content="HDFC Mid Cap Fund expense ratio is 0.85%",
                    metadata={
                        "fund_name": "HDFC Mid Cap Fund",
                        "fund_type": "mid cap",
                        "content_type": "expense_ratio",
                        "hierarchical_keys": ["fund:hdfc_mid_cap", "type:mid_cap", "content:expense_ratio"]
                    },
                    chunk_index=0,
                    total_chunks=2,
                    token_count=12,
                    source_document_id="doc_1"
                ),
                Chunk(
                    chunk_id="chunk_2",
                    content="HDFC Large Cap Fund SIP amount is Rs. 500",
                    metadata={
                        "fund_name": "HDFC Large Cap Fund",
                        "fund_type": "large cap",
                        "content_type": "sip",
                        "hierarchical_keys": ["fund:hdfc_large_cap", "type:large_cap", "content:sip"]
                    },
                    chunk_index=1,
                    total_chunks=2,
                    token_count=10,
                    source_document_id="doc_2"
                )
            ]
            
            # Build index
            indexer.build_index(chunks)
            
            # Test query routing
            routing = indexer.route_queries("HDFC Mid Cap Fund expense ratio")
            assert routing["query_type"] == "fund_specific"
            assert "hdfc_mid_cap_fund" in routing["target_funds"]
            
            # Test metadata filters
            filters = indexer.setup_metadata_filters()
            assert len(filters["fund_filters"]) == 2
            assert len(filters["type_filters"]) == 2
            assert len(filters["content_filters"]) == 2
            
            # Test statistics
            stats = indexer.get_fund_statistics()
            assert stats["total_funds"] == 2
            assert stats["total_chunks"] == 2


if __name__ == "__main__":
    pytest.main([__file__])
