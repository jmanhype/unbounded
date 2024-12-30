"""Database initialization script."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from .database import engine, Base

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def main():
    """Main function."""
    asyncio.run(init_db())

if __name__ == "__main__":
    main() 