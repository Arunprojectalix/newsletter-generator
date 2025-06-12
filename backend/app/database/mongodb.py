import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from typing import Optional
from ..core.config import settings
import asyncio
import sys
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout   
)
logger = logging.getLogger(__name__)

# Global connection pool
_client: Optional[AsyncIOMotorClient] = None
_database = None
_connection_lock = asyncio.Lock()

@lru_cache(maxsize=1)
def get_motor_client() -> AsyncIOMotorClient:
    """Get a cached MongoDB client instance."""
    return AsyncIOMotorClient(
        settings.MONGODB_URL,
        maxPoolSize=10,  # Smaller pool size for serverless
        minPoolSize=1,   # Keep at least one connection
        maxIdleTimeMS=30000,  # Close idle connections after 30 seconds
        waitQueueTimeoutMS=5000,  # Wait up to 5 seconds for a connection
        serverSelectionTimeoutMS=5000,  # Fail fast if can't connect
        connectTimeoutMS=5000,  # Connect timeout
    )

async def get_client() -> AsyncIOMotorClient:
    """Get or create MongoDB client with connection pooling."""
    try:
        client = get_motor_client()
        # Test the connection
        await client.admin.command('ping')
        logger.info("MongoDB connection pool initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB connection pool: {e}")
        raise

async def get_database():
    """Get database instance with lazy initialization."""
    try:
        client = await get_client()
        db = client[settings.MONGODB_DB_NAME]
        logger.info(f"Database connection established to {settings.MONGODB_DB_NAME}")
        return db
    except Exception as e:
        logger.error(f"Failed to get database connection: {e}")
        raise Exception("Database connection failed")

async def close_mongo_connection():
    """Close MongoDB connection."""
    try:
        client = get_motor_client()
        client.close()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")
    finally:
        # Clear the LRU cache to force a new client creation next time
        get_motor_client.cache_clear()
