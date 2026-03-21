from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "JanGraph OS"
    
    # To utilize Upstash/Remote Postgres, populate the DATABASE_URL in .env
    DATABASE_URL: str = ""

    # Legacy Local Defaults (maintained for structural fallback)
    POSTGRES_USER: str = "jangraph"
    POSTGRES_PASSWORD: str = "jangraph_secure"
    POSTGRES_DB: str = "jangraph_os"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    
    # Neo4j Driver Connection
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_DATABASE: str = "neo4j"

    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "jangraph_secure_graph"
    
    # Cache / Celery
    REDIS_URL: str = "redis://redis:6379/0"

    # Settings for Sovereign Mode
    LOCAL_MODE_ENABLED: bool = True
    
    # LLM Providers
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    DEFAULT_LLM_PROVIDER: str = "groq" # Fallback is gemini
    PRIMARY_LLM_MODEL: str = ""

    # External Intelligence
    NEWS_API_KEY: str = ""
    ACLED_API_KEY: str = ""
    GDELT_ENABLED: bool = True
    HUGGINGFACE_API_KEY: str = ""
    OPENSKY_USERNAME: str = ""
    OPENSKY_PASSWORD: str = ""
    FRED_API_KEY: str = ""
    POLYMARKET_ENABLED: bool = True
    USGS_EARTHQUAKE_ENABLED: bool = True
    NASA_FIRMS_ENABLED: bool = True
    
    # MCP Servers
    BRIGHT_DATA_MCP_KEY: str = ""
    FINANCIAL_MCP_KEY: str = ""
    
    # Social Media APIs
    TWITTER_API_IO_KEY: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    BLUESKY_APIFY_KEY: str = ""
    MASTODON_ACCESS_TOKEN: str = ""
    MASTODON_API_BASE_URL: str = "https://mastodon.social"
    YOUTUBE_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    BEWGLE_API_KEY: str = ""
    VITE_MAPBOX_TOKEN: str = ""
    VITE_API_BASE_URL: str = ""

    @property
    def sync_database_url(self) -> str:
        """ Returns the sync version for tools like Alembic or legacy scripts """
        if self.DATABASE_URL:
            # Enforces sync postgresql dialect if starting with postgres:// or postgresql://
            return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def async_database_url(self) -> str:
        """ Primary Async backend URL """
        if self.DATABASE_URL:
            # Upstash standard URLs often use 'postgres://'. asyncpg requires 'postgresql+asyncpg://'
            url = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
            if not url.startswith("postgresql+asyncpg://"):
                url = "postgresql+asyncpg://" + url.split("://")[-1]
            return url
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


    class Config:
        case_sensitive = True
        extra = "ignore"
        # Resolve the path to the root .env regardless of where the app is started
        import os
        from pathlib import Path
        _root_dir = Path(__file__).resolve().parent.parent.parent.parent
        env_file = str(_root_dir / ".env")


settings = Settings()
