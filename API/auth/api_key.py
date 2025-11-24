"""
API Key Authentication
Validates API keys from X-API-Key header
"""

import os
import sys
import bcrypt
from fastapi import Header, HTTPException, status

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.database import get_database
from src.core.logger import setup_logger

logger = setup_logger(__name__)


def hash_api_key(api_key: str) -> str:
    """Hash an API key using bcrypt"""
    return bcrypt.hashpw(api_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_api_key_hash(api_key: str, hashed_key: str) -> bool:
    """Verify API key against hash"""
    try:
        return bcrypt.checkpw(api_key.encode('utf-8'), hashed_key.encode('utf-8'))
    except Exception as e:
        logger.error(f"API key verification error: {e}")
        return False


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """
    Verify API key from request header
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        Verified API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check if API key exists in database
    db = get_database()
    
    # Try to find matching API key
    # Note: In production, this should be optimized with indexing
    with db.session_scope() as session:
        from src.core.database import APIKey
        
        api_keys = session.query(APIKey).filter_by(is_active=True).all()
        
        for stored_key in api_keys:
            if verify_api_key_hash(x_api_key, stored_key.key_hash):
                # Update usage statistics
                db.update_api_key_usage(stored_key.key_hash)
                
                logger.info(f"API key authenticated: {stored_key.key_name}")
                return x_api_key
    
    # If we get here, no valid key was found
    logger.warning(f"Invalid API key attempted")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


__all__ = ['verify_api_key', 'hash_api_key', 'verify_api_key_hash']

