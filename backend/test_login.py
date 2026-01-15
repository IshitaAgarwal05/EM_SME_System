
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.auth_service import AuthService
from app.core.exceptions import AuthenticationError

async def test_login():
    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)
        try:
            # We know this user exists from previous check
            user = await auth_service.authenticate_user("ishanvi@jklu.edu.in", "Password123!")
            print(f"Authenticated user: {user.email}")
            tokens = await auth_service.create_tokens(user)
            print(f"Tokens created: {tokens.access_token[:20]}...")
        except AuthenticationError as e:
            print(f"Auth error: {e}")
        except Exception as e:
            print(f"Error type: {type(e)}")
            print(f"Error message: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_login())
