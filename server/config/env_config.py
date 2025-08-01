import os
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel, Field

class EnvConfig(BaseModel):
    """Pydantic model for environment configuration"""
    notion_api_key: Optional[str] = Field(default=None, description="Notion API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    fastapi_host: str = Field(default="0.0.0.0", description="FastAPI host")
    fastapi_port: int = Field(default=8000, description="FastAPI port")
    fastapi_debug: bool = Field(default=True, description="FastAPI debug mode")
    database_url: str = Field(default="sqlite:///./notion_agent.db", description="Database URL")
    log_level: str = Field(default="INFO", description="Log level")

def load_env_config() -> None:
    """Load environment variables from .env file"""
    load_dotenv()

def get_notion_api_key() -> Optional[str]:
    """Get Notion API key from environment variables
    
    Returns:
        Optional Notion API key string
    """
    load_env_config()
    return os.getenv("NOTION_API_KEY")

def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from environment variables
    
    Returns:
        Optional OpenAI API key string
    """
    load_env_config()
    return os.getenv("OPENAI_API_KEY")

def get_fastapi_host() -> str:
    """Get FastAPI host from environment variables
    
    Returns:
        FastAPI host string
    """
    return os.getenv("FASTAPI_HOST", "0.0.0.0")

def get_fastapi_port() -> int:
    """Get FastAPI port from environment variables
    
    Returns:
        FastAPI port integer
    """
    return int(os.getenv("FASTAPI_PORT", "8000"))

def get_fastapi_debug() -> bool:
    """Get FastAPI debug mode from environment variables
    
    Returns:
        FastAPI debug mode boolean
    """
    return os.getenv("FASTAPI_DEBUG", "True").lower() == "true"

def get_database_url() -> str:
    """Get database URL from environment variables
    
    Returns:
        Database URL string
    """
    return os.getenv("DATABASE_URL", "sqlite:///./notion_agent.db")

def get_log_level() -> str:
    """Get log level from environment variables
    
    Returns:
        Log level string
    """
    return os.getenv("LOG_LEVEL", "INFO")

def get_env_config() -> EnvConfig:
    """Get complete environment configuration as Pydantic model
    
    Returns:
        EnvConfig Pydantic model with all environment settings
    """
    load_env_config()
    return EnvConfig(
        notion_api_key=get_notion_api_key(),
        openai_api_key=get_openai_api_key(),
        fastapi_host=get_fastapi_host(),
        fastapi_port=get_fastapi_port(),
        fastapi_debug=get_fastapi_debug(),
        database_url=get_database_url(),
        log_level=get_log_level()
    )
