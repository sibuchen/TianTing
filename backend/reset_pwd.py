import bcrypt
import asyncio
from app.core.database import init_database, get_db_context

init_database()
h = bcrypt.hashpw(b'test123', bcrypt.gensalt(12)).decode()

async def u():
    async with get_db_context() as db:
        from sqlalchemy import text
        await db.execute(
            text('UPDATE users SET password_hash = :h WHERE username = :u'),
            {'h': h, 'u': 'sibuchen'}
        )
        await db.commit()
    print('Password updated to: test123')

asyncio.run(u())
