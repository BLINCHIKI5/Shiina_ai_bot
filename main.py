import asyncio
from aiogram import Bot, Dispatcher
from os import getenv
from dotenv import load_dotenv
from handler.user_reply import router
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats
)
from database import (
    init_db,
    cleanup_old_messages,
    cleanup_old_metrics,
    cleanup_old_interactions,
)
from handler.welcome import router as welcome_router


load_dotenv()
dp = Dispatcher()
dp.include_router(router)
dp.include_router(welcome_router)
TOKEN = getenv("BOT_TOKEN")


async def main():
    bot = Bot(token=TOKEN)

    commands = [
        BotCommand(command="start", description="Запустить бота 🟢"),
        BotCommand(command="help", description="Список команд 📋"),
        BotCommand(command="coin", description="Подбросить монету 🟡"),
        BotCommand(command="quote", description="Случайная цитата 📜"),
        BotCommand(command="heart", description="Получить сердечко 💗"),
        BotCommand(command="hearts", description="Мой счёт сердечек 💗"),
        BotCommand(command="top_hearts", description="Топ любимчиков 🏆"),
    ]

    await bot.set_my_commands(commands[:2], scope=BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(commands, scope=BotCommandScopeAllGroupChats())

    init_db()

    msg = cleanup_old_messages(days=30)
    met = cleanup_old_metrics(days=90)
    inter = cleanup_old_interactions(days=30)

    print(f"Очистка: messages={msg}, metrics={met}, interactions={inter}")
    print("Bot is started")

    await dp.start_polling(bot, allowed_updates=["message", "chat_member", "my_chat_member"])


if __name__ == "__main__":
    asyncio.run(main())