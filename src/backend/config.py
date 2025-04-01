# Updated on April 1 for token management

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from pathlib import Path

# Locate and load the .env.development file from the root project directory
env_path = Path(__file__).parent.parent.parent / ".env.development"
print(f"Looking for .env file at: {env_path.absolute()}")
print(f"File exists: {env_path.exists()}")

# Load environment variables from the .env file into Python's os.environ
load_dotenv(str(env_path))

# Debug output to confirm correct loading
print("\nLoaded Environment Variables:")
print(f"HUGGINGFACE_API_KEY: {os.getenv('HUGGINGFACE_API_KEY')}")
print(f"MONGO_DB_URI: {os.getenv('MONGO_DB_URI')}")

class Settings(BaseSettings):
    # API Keys (used for model integration and cloud services)
    HUGGINGFACE_API_KEY: str
    GOOGLE_GEMINI_API_KEY: str
    LLM_MODEL: str

    # Security & Token Settings
    # SECRET_KEY: used to sign and verify JWT tokens
    # ALGORITHM: used with PyJWT/Jose for encoding
    # ACCESS_TOKEN_EXPIRE_MINUTES: lifespan of access tokens (short-lived)
    # REFRESH_TOKEN_EXPIRE_DAYS: lifespan of refresh tokens (longer-lived)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

    # MongoDB Configuration
    MONGO_DB_URI: str
    DB_CLOUD_PASSWORD: str
    DB_CLOUD_USERNAME: str

    # Upload and Storage Configuration
    UPLOAD_FOLDER: str = "uploads"
    UPLOAD_DIR: str = "uploads/videos"

    # Transformer/Model Execution Settings
    # Used to optimize or debug CUDA-based Torch/Transformer operations
    CUDA_LAUNCH_BLOCKING: str = "0"
    TOKENIZERS_PARALLELISM: str = "true"
    TORCH_USE_CUDA_DSA: str = "1"

    # Frontend Configuration
    # Used to allow the frontend (React) to know which backend URL to talk to
    REACT_APP_API_URL: str = "http://localhost:8000"

    # CORS Configuration
    # These determine which origins, headers, and methods are allowed during cross-origin requests
    ALLOWED_HOSTS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "https://your-production-domain.com",
    ]

    ALLOWED_HEADERS: list = [
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ]

    ALLOWED_METHODS: list = [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
        "PATCH"
    ]

    class Config:
        # Tells Pydantic to load variables from this env file
        env_file = str(env_path)
        env_file_encoding = 'utf-8'
        case_sensitive = False

    # Custom init for debugging failed env loads
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
        except Exception as e:
            print(f"\nError initializing Settings: {str(e)}")
            print("Current environment variables:")
            for key in ["HUGGINGFACE_API_KEY", "MONGO_DB_URI", "UPLOAD_DIR"]:
                print(f"{key}: {os.getenv(key)}")
            raise

# Try to load the Settings and log success/failure
try:
    settings = Settings()
    print("\nSettings loaded successfully!")
except Exception as e:
    print(f"\nFailed to load settings: {str(e)}")
    raise
