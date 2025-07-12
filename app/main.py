import asyncio

from app.users.user_router import user_router
from app.admin.admin import admin_router
from app.users.catalog_router import catalog_router

from loguru import logger
from aiogram.types import BotCommand, BotCommandScopeDefault

from app.DAO.db_middleware import DatabaseMiddlewareWithCommit, DatabaseMiddlewareWithoutCommit
from app.config import settings, bot, dp


async def set_commands():
    commands = [BotCommand(command='start', description='Starts the bot.')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def start_bot():
    await set_commands()
    for user_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(user_id, 'Бот запушен')
        except:
            pass
    logger.info("Бот запушен")


async def stop_bot():
    try:
        for admin_id in settings.ADMIN_IDS:
            await bot.send_message(admin_id, 'Бот остановлен. За что?😔')
    except:
        pass
    logger.error("Бот остановлен!")


async def main():
    dp.update.middleware.register(DatabaseMiddlewareWithoutCommit())
    dp.update.middleware.register(DatabaseMiddlewareWithCommit())

    dp.include_router(user_router)
    dp.include_router(catalog_router)
    dp.include_router(admin_router)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())