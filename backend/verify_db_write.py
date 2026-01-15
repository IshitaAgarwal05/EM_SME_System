
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User, RefreshToken

async def verify_db_write():
    async with AsyncSessionLocal() as db:
        try:
            # Get first user
            res = await db.execute(select(User).limit(1))
            user = res.scalar_one_or_none()
            if not user:
                print("No user found")
                return

            print(f"Testing write for user: {user.email}")
            
            # Update last login
            user.last_login_at = datetime.now(timezone.utc)
            
            # Create a dummy refresh token
            token = RefreshToken(
                user_id=user.id,
                token_hash="test_hash_" + str(datetime.now().timestamp()),
                expires_at=datetime.now(timezone.utc)
            )
            db.add(token)
            
            await db.commit()
            print("Successfully committed to database!")
            
            # Cleanup
            await db.delete(token)
            await db.commit()
            print("Cleanup successful!")
            
        except Exception as e:
            print(f"Write error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_db_write())
