import asyncio
import json
import os

from aiogram import Dispatcher
from dotenv import load_dotenv
from loguru import logger

from bot_instance import create_bot_instance
from database import DB
from routes.admin import admin_router
from routes.default import default_router
from routes.game import game_router


def register_routes(dp: Dispatcher) -> None:
    dp.include_router(admin_router)
    dp.include_router(game_router)
    dp.include_router(default_router)


def create_json() -> None:
    try:
        open("/tmp/dao/images.json", "r")
    except IOError:
        with open("/tmp/dao/images.json", "w") as f:
            f.write(json.dumps({"photos": []}))


async def main() -> None:
    logger.info("loading .env")
    load_dotenv()
    TOKEN = os.getenv("TOKEN", "")

    logger.info("starting dispatcher")
    bot = create_bot_instance(token=TOKEN)

    if not os.path.exists("/tmp/dao"):
        os.makedirs("/tmp/dao")

    db = DB()
    dp = Dispatcher(db=db)
    register_routes(dp)
    create_json()

    logger.info("start polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
