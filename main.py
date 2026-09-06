import asyncio
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN
from game_engine import GameManager
from handlers import register_handlers

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

manager = GameManager()


async def post_init(application: Application) -> None:
    application.bot_data["manager"] = manager
    asyncio.create_task(manager.world_loop(application))


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is required.")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    register_handlers(application, manager)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
