import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import async_session, init_db
from app.models import Shop


async def main():
    await init_db()

    async with async_session() as db:
        shop = Shop(
            shop_name="Demo Print Shop",
            device_id="demo-device-001",
        )
        db.add(shop)
        await db.commit()
        await db.refresh(shop)

        print(f"Shop created:")
        print(f"  Name:      {shop.shop_name}")
        print(f"  Shop ID:   {shop.shop_id}")
        print(f"  Device ID: {shop.device_id}")
        print(f"\nUpload URL: http://localhost:8000/frontend/index.html?shop_id={shop.shop_id}")


if __name__ == "__main__":
    asyncio.run(main())
