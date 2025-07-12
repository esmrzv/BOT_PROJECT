from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.DAO.dao import UserDao

from app.users.kbs import main_user_kb
from app.users.schemas import TelegramIDModel, UserModel

user_router = Router()


@user_router.message(CommandStart())
async def cmd_start(message: Message, session_with_commit: AsyncSession):
    user_id = message.from_user.id
    user_info = await UserDao.find_one_or_none(session_with_commit,
                                               filters=TelegramIDModel(telegram_id=user_id))
    values = UserModel(
        telegram_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    if user_info:
        await message.answer(f'Добро пожаловать {message.from_user.full_name}\n'
                             f'Выберите действие: ',
                             reply_markup=main_user_kb(user_id))
    try:
        await UserDao.add(session=session_with_commit, values=values)
    except IntegrityError as e:
        logger.warning(f"Пользователь с telegram_id {user_id} уже существует")
        await message.answer("Похоже, вы уже зарегистрированы.")
    await message.answer(text='Вы успешно зарегистрировались')
    await message.answer(f"🎉 <b>Благодарим за регистрацию!</b>. Теперь выберите необходимое действие.",
                         reply_markup=main_user_kb(user_id))
