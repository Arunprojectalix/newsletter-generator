import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from typing import Optional
from ..core.config import settings
import asyncio
import sys

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

async def get_client() -> AsyncIOMotorClient:
    """Get or create MongoDB client with connection pooling."""
    global _client
    
    if _client is None:
        async with _connection_lock:
            # Double check after acquiring lock
            if _client is None:
                try:
                    logger.info("Initializing MongoDB connection pool")
                    # Configure connection pool for serverless
                    _client = AsyncIOMotorClient(
                        settings.MONGODB_URL,
                        maxPoolSize=10,  # Smaller pool size for serverless
                        minPoolSize=1,   # Keep at least one connection
                        maxIdleTimeMS=30000,  # Close idle connections after 30 seconds
                        waitQueueTimeoutMS=5000,  # Wait up to 5 seconds for a connection
                        serverSelectionTimeoutMS=5000,  # Fail fast if can't connect
                        connectTimeoutMS=5000,  # Connect timeout
                    )
                    # Test the connection
                    await _client.admin.command('ping')
                    logger.info("MongoDB connection pool initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize MongoDB connection pool: {e}")
                    _client = None
                    raise
    
    return _client

async def get_database():
    """Get database instance with lazy initialization."""
    global _database
    
    if _database is None:
        try:
            client = await get_client()
            _database = client[settings.MONGODB_DB_NAME]
            logger.info(f"Database connection established to {settings.MONGODB_DB_NAME}")
        except Exception as e:
            logger.error(f"Failed to get database connection: {e}")
            raise Exception("Database connection failed")
    
    return _database

async def close_mongo_connection():
    """Close MongoDB connection."""
    global _client, _database
    
    if _client is not None:
        try:
            _client.close()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
        finally:
            _client = None
            _database = None

# Initialize connection on module import
async def init_db():
    """Initialize database connection."""
    try:
        await get_database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# Create event loop and run initialization
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Run initialization in background
loop.create_task(init_db())
