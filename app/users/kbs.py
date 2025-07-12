from typing import List

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.DAO.models import Category
from app.config import settings


def main_user_kb(user_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text='Мои покупки', callback_data='profile')
    kb.button(text='Каталог', callback_data='catalog')
    kb.button(text='О магазине', callback_data='about')
    if user_id in settings.ADMIN_IDS:
        kb.button(text='Админ панель', callback_data='admin_panel')

    kb.adjust(1)
    return kb.as_markup()


def catalog_db(catalog_data: List[Category]):
    kb = InlineKeyboardBuilder()
    for category in catalog_data:
        kb.button(text=category.category_name, callback_data=f'catalog_{category.id}')
    kb.button(text='На главную', callback_data='home')
    kb.adjust(2)
    return kb.as_markup()

def purchases_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='Смотретьт покупки', callback_data='purchases')
    kb.button(text='На главную', callback_data='home')
    kb.adjust(1)
    return kb.as_markup()


def products_kb(price, product_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="Купить", callback_data=f'By_{product_id}_{price}')
    kb.button(text='На главную', callback_data='home')
    kb.adjust(2)
    return kb.as_markup()




