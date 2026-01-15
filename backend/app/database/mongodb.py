import pymongo
from pymongo import MongoClient
import logging
from typing import Optional
from ..core.config import settings
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout   
)
logger = logging.getLogger(__name__)

# Use a single client for the application
client = None
db = None

def get_database():
    """Get database instance with lazy initialization."""
    global client, db
    
    if db is None:
        try:
            # Initialize the client if not already done
            if client is None:
                logger.info(f"Initializing MongoDB connection to {settings.MONGODB_URL}")
                client = MongoClient(
                    settings.MONGODB_URL,
                    maxPoolSize=10,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000
                )
                
            # Get the database
            db = client[settings.MONGODB_DB_NAME]
            logger.info(f"Connected to database: {settings.MONGODB_DB_NAME}")
            
            # Test the connection
            db.command("ping")
            logger.info("Database connection verified with ping")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Reset the client and db so we try to reconnect next time
            client = None
            db = None
            raise Exception(f"Database connection failed: {e}")
    
    return db

def close_mongo_connection():
    """Close MongoDB connection."""
    global client, db
    
    if client is not None:
        try:
            client.close()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
        finally:
            client = None
            db = None
