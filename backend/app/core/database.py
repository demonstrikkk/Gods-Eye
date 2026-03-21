from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# PostGIS requires specific dialect configuration if doing advanced operations, 
# asyncpg is fine for base SQLAlchemy ORM mapping over PostGIS structures
engine = create_async_engine(
    settings.async_database_url,
    echo=False,

    future=True,
    pool_size=10, 
    max_overflow=20 # Handled for enterprise scaling
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
