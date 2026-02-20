from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base

# Import all models to ensure they are registered with SQLAlchemy
from app.models import user, chat, otp, admin, subscription, settings, activity
from app.models import user_memory, moderation_log

# Import routes
from app.routes import auth, chat as chat_routes, user as user_routes, payment
from app.routes import admin_auth, admin_dashboard, admin_users, admin_plans, admin_settings
from app.routes import user_profile_image, admin_profile_image
from app.routes import admin_companion

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Authentication & AI Chat with Admin Dashboard",
    description="Backend API for authentication, AI chat, and admin dashboard",
    version="2.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include user routers
app.include_router(auth.router)
app.include_router(chat_routes.router)
app.include_router(user_routes.router)
app.include_router(user_profile_image.router)
app.include_router(payment.router)

# Include admin routers
app.include_router(admin_auth.router)
app.include_router(admin_dashboard.router)
app.include_router(admin_users.router)
app.include_router(admin_plans.router)
app.include_router(admin_settings.router)
app.include_router(admin_profile_image.router)
app.include_router(admin_companion.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to FastAPI Authentication & AI Chat API",
        "docs": "/docs",
        "redoc": "/redoc",
        "admin_docs": "/docs#/Admin%20Authentication"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

