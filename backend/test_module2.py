import asyncio
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.models.user import User
from sqlalchemy import select

async def test_all():
    print("Starting Module 2 Validation...\n")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("1. Database connection successful.")

    test_email = "validation@test.local"
    test_password = "SuperSecret123"
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == test_email))
        user = result.scalar_one_or_none()
        
        if not user:
            new_user = User(email=test_email, hashed_password=get_password_hash(test_password))
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            print("2. Test user created and saved to database.")
        else:
            print("2. Test user already exists in database.")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == test_email))
        user = result.scalar_one_or_none()
        is_valid = verify_password(test_password, user.hashed_password)
        if is_valid:
            print("3. Password hashing and verification works.")
        else:
            print("3. Password verification FAILED.")
            return

    token = create_access_token(data={"sub": user.email})
    payload = decode_access_token(token)
    
    if payload and payload.get("sub") == test_email:
        print("4. JWT Token generation and decoding works.")
    else:
        print("4. JWT Token FAILED.")
        return

    print("\nSUCCESS! Module 2 is 100% VALIDATED.")

if __name__ == "__main__":
    asyncio.run(test_all())
