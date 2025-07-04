import os.path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from config import settings


BOT_TOKEN = '6915846876:AAGyf6KAGXvQfp1c9KVwrkUR25bxtKAEzeM'
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
admins = settings.ADMINS_ID

log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.txt')
logger.add(log_file_path, format=settings.LOG_FORMAT, level="INFO", rotation=settings.LOG_ROTATION)

