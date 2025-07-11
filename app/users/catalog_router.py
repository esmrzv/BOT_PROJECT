from gettext import Catalog

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.DAO.dao import CategoryDao, ProductDao
from app.users.kbs import catalog_db, products_kb
from app.users.schemas import ProductCategoryIDModel

catalog_router = Router()


@catalog_router.callback_query(F.text == 'catalog')
async def page_catalog(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.message.answer(text='Подгружаем каталог....')
    catalog_data = await CategoryDao.find_all(session=session_without_commit)
    await call.message.edit_text(text='Выберите категорию: ', reply_markup=catalog_db(catalog_data))


@catalog_router.callback_query(F.data.startswith('catalog_'))
async def page_catalog_products(call: CallbackQuery, session_without_commit: AsyncSession):
    category_id = int(call.data.split('_')[1])
    products_category = await ProductDao.find_all(session=session_without_commit,
                                               filters=ProductCategoryIDModel(category_id=category_id))

    count_products = len(products_category)

    if count_products > 0:
        await call.message.answer(text=f'В данной категории {count_products} продуктов')
        for product in products_category:
            product_text = (
                f"📦 <b>Название товара:</b> {product.name}\n\n"
                f"💰 <b>Цена:</b> {product.price} руб.\n\n"
                f"📝 <b>Описание:</b>\n<i>{product.description}</i>\n\n"
                f"━━━━━━━━━━━━━━━━━━"
            )
            await call.message.answer(text=product_text, reply_markup=products_kb(product.id, product.price))

    else:
        await call.answer(text='В данной категории нет товаров')


