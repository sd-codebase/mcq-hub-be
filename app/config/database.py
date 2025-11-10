"""
Database configuration and connection management.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.exceptions import DatabaseConnectionException

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# MongoDB settings
MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DB_NAME")

# Global database client
mongodb_client: Optional[AsyncIOMotorClient] = None


def get_database() -> AsyncIOMotorDatabase:
    """
    Get the database instance.

    Returns:
        AsyncIOMotorDatabase: MongoDB database instance

    Raises:
        DatabaseConnectionException: If database client is not initialized
    """
    if mongodb_client is None:
        logger.error("Database client is not initialized")
        raise DatabaseConnectionException("Database connection not established")

    return mongodb_client[DB_NAME]


async def connect_to_mongo() -> None:
    """
    Connect to MongoDB with proper error handling.

    Raises:
        DatabaseConnectionException: If connection fails
    """
    global mongodb_client

    try:
        mongodb_client = AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000,  # 5 seconds timeout
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )

        # Test the connection
        await mongodb_client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB")

    except Exception as e:
        logger.critical(f"❌ Failed to connect to MongoDB: {str(e)}")
        raise DatabaseConnectionException(f"Failed to connect to MongoDB: {str(e)}")


async def close_mongo_connection() -> None:
    """Close MongoDB connection gracefully."""
    global mongodb_client

    if mongodb_client:
        mongodb_client.close()
        logger.info("🔌 Disconnected from MongoDB")
        mongodb_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles database connection startup and shutdown.
    """
    # Startup: Connect to MongoDB
    try:
        await connect_to_mongo()
    except DatabaseConnectionException as e:
        logger.error(f"Application startup failed: {str(e)}")
        # Re-raise to prevent application from starting with broken DB connection
        raise

    yield

    # Shutdown: Close MongoDB connection
    await close_mongo_connection()


async def create_indexes() -> None:
    """
    Create database indexes for better query performance.
    Should be called after database connection is established.
    """
    try:
        db = get_database()

        # Create indexes for items collection
        await db.items.create_index("name")
        logger.info("Created index on items.name")

        # Create indexes for subjects collection
        await db.subjects.create_index("name", unique=True)
        await db.subjects.create_index("shortName", unique=True)
        await db.subjects.create_index("order")
        await db.subjects.create_index("status")
        logger.info("Created indexes on subjects collection")

        # Create indexes for chapters collection
        await db.chapters.create_index("subjectId")
        await db.chapters.create_index("order")
        await db.chapters.create_index("status")
        await db.chapters.create_index([("subjectId", 1), ("order", 1)])
        logger.info("Created indexes on chapters collection")

        # Create indexes for topics collection
        await db.topics.create_index("chapterId")
        await db.topics.create_index("order")
        await db.topics.create_index("status")
        await db.topics.create_index([("chapterId", 1), ("order", 1)])
        logger.info("Created indexes on topics collection")

    except Exception as e:
        logger.error(f"Failed to create indexes: {str(e)}")
        # Don't raise exception - indexes are optimization, not critical for startup
