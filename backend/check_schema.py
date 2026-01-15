
import asyncio
from sqlalchemy import inspect
from app.db.session import engine

async def check_schema():
    def get_columns():
        inspector = inspect(engine.sync_engine)
        cols = inspector.get_columns("users")
        for col in cols:
            print(f"User Column: {col['name']} | Type: {col['type']}")
        
        cols = inspector.get_columns("refresh_tokens")
        for col in cols:
            print(f"Token Column: {col['name']} | Type: {col['type']}")

    await asyncio.get_event_loop().run_in_executor(None, get_columns)

if __name__ == "__main__":
    asyncio.run(check_schema())
