"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI

from app.config.database import lifespan, create_indexes, get_database
from app.core.error_handlers import register_exception_handlers
from app.modules.items.routes import router as items_router
from app.modules.subjects.routes import router as subjects_router
from app.modules.chapters.routes import router as chapters_router
from app.modules.topics.routes import router as topics_router
from app.modules.questions.routes import router as questions_router


# Create FastAPI app
app = FastAPI(
    title="MCQ Hub API",
    description="A modular REST API built with FastAPI and MongoDB",
    version="1.0.0",
    lifespan=lifespan
)

# Register exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(items_router, prefix="/items", tags=["Items"])
app.include_router(subjects_router, prefix="/subjects", tags=["Subjects"])
app.include_router(chapters_router, prefix="/chapters", tags=["Chapters"])
app.include_router(topics_router, prefix="/topics", tags=["Topics"])
app.include_router(questions_router, prefix="/questions", tags=["Questions"])


@app.get("/")
async def root():
    """Root endpoint - Welcome message."""
    return {
        "message": "Welcome to MCQ Hub API!",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Verifies API and database connectivity.
    """
    try:
        db = get_database()
        await db.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "message": "All systems operational"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


@app.on_event("startup")
async def startup_event():
    """Create database indexes on startup."""
    await create_indexes()
