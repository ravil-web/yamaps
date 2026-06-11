"""
Main FastAPI application
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth, users, lessons, games, progress, achievements, parent, tests, tts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await init_db()
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.MEDIA_UPLOAD_DIR, exist_ok=True)
    
    yield
    
    # Shutdown
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Interactive English learning platform for children aged 5-12",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(lessons.router, prefix="/api/lessons", tags=["Lessons"])
app.include_router(games.router, prefix="/api/games", tags=["Games"])
app.include_router(progress.router, prefix="/api/progress", tags=["Progress"])
app.include_router(achievements.router, prefix="/api/achievements", tags=["Achievements"])
app.include_router(parent.router, prefix="/api/parent", tags=["Parent Dashboard"])
app.include_router(tests.router, prefix="/api/tests", tags=["Tests"])
app.include_router(tts.router, prefix="/api/tts", tags=["Text-to-Speech"])

# Static files for media
if os.path.exists(settings.MEDIA_UPLOAD_DIR):
    app.mount("/media", StaticFiles(directory=settings.MEDIA_UPLOAD_DIR), name="media")

# Prometheus metrics
if settings.DEBUG:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "Welcome to EnglishKids Academy!"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
