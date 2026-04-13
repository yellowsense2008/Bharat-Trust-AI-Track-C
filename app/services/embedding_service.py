import logging

logger = logging.getLogger(__name__)

# Lazy import to avoid startup cost
_model = None

def preload_model():
    """Preload model in background"""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers model...")
            _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            logger.info("✅ Embedding model loaded")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")

def get_embedding(text: str):
    global _model
    
    # Load model if not already loaded
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading model on-demand...")
        _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    try:
        # Don't use convert_to_numpy - let it return tensor then convert
        embedding = _model.encode(text[:512])
        # Convert to list directly
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise