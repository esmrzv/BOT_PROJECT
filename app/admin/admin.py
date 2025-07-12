from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.DAO.dao import UserDao, PurchaseDao, ProductDao, CategoryDao
from app.admin.kbs import admin_kb, product_management_kb, dell_product_kb, admin_kb_back, cancel_kb_inline, \
    catalog_admin_kb, admin_send_file_kb, admin_confirm_kb
from app.admin.shemas import ProductIDModel, ProductModel
from app.admin.utils import process_del_text_msg
from app.config import settings, bot

admin_router = Router()


class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    file_id = State()
    category_id = State()
    hidden_content = State()
    confirm_add = State()


@admin_router.callback_query(F.data == 'admin_panel', F.from_user.id.in_(settings.ADMIN_IDS))
async def start_admin(call: CallbackQuery):
    await call.answer('Доступ к админ панели разрешен')
    await call.message.edit_text(
        text="Вам разрешен доступ в админ панель.Выберите необходимое действие: ",
        reply_markup=admin_kb()
    )


@admin_router.callback_query(F.data == 'statistics', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_statistics(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer('Запрос на получение статистики')
    stats = await UserDao.get_statistics(session_without_commit)
    total_summ = await PurchaseDao.get_summ(session_without_commit)
    stats_msg = (
        "📈 Статистика пользователей:\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"🆕 Новых за сегодня: {stats['new_today']}\n"
        f"📅 Новых за неделю: {stats['new_week']}\n"
        f"📆 Новых за месяц: {stats['new_month']}\n\n"
        f"💰 Общая сумма заказов: {total_summ} руб.\n\n"
        "🕒 Данные актуальны на текущий момент."
    )
    await call.message.edit_text(
        text=stats_msg,
        reply_markup=admin_kb()
    )


@admin_router.callback_query(F.data == 'process_product', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_product(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer('Режим управления товарами')
    all_product = await ProductDao.count(session=session_without_commit)
    await call.message.edit_text(
        f'У нас {all_product} колличества продуктов. Что будем делать?', reply_markup=product_management_kb()
    )


@admin_router.callback_query(F.data == 'delete_product', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_delete_product(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.message.answer('Режим удаления товаров')
    all_products = await ProductDao.find_all(session=session_without_commit)
    await call.message.edit_text(
        f'Всего товаров в наличии {len(all_products)}'
    )
    for product_data in all_products:
        file_id = product_data.file_id
        file_text = "Товар с файлом" if file_id else "Товар без файла"
        product_text = (f'🛒 Описание товара:\n\n'
                        f'🔹 <b>Название товара:</b> <b>{product_data.name}</b>\n'
                        f'🔹 <b>Описание:</b>\n\n<b>{product_data.description}</b>\n\n'
                        f'🔹 <b>Цена:</b> <b>{product_data.price} ₽</b>\n'
                        f'🔹 <b>Описание (закрытое):</b>\n\n<b>{product_data.hidden_content}</b>\n\n'
                        f'<b>{file_text}</b>')
        if file_id:
            await call.message.answer_document(document=file_id, caption=product_text,
                                               reply_markup=dell_product_kb(product_data.id))
        else:
            await call.message.answer(text=product_text, reply_markup=dell_product_kb(product_data.id))


@admin_router.callback_query(F.data.startswith('dell_'), F.from_user.id.in_(settings.ADMIN_IDS))
async def process_admin_del(call: CallbackQuery, session_with_commit: AsyncSession):
    product_id = int(call.data.split('_')[-1])
    await ProductDao.delete(session=session_with_commit, filters=ProductIDModel(id=product_id))
    await call.message.answer(text=f'Продукт с ID{product_id} успешно удален', show_alert=True)
    await call.message.delete()


@admin_router.callback_query(F.data == 'cancel', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer('Отмена сценария при добалении товара')
    await call.message.delete()
    await call.message.edit_text(
        text='Отмена при добвлении товара', reply_markup=admin_kb_back()
    )


@admin_router.callback_query(F.data == 'add_product', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_add_product(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Режим добавления товара")
    await call.message.delete()
    msg = await call.message.answer(text='Укажите название товара: ', reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(AddProduct.name)


@admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), AddProduct.name)
async def admin_process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await process_del_text_msg(message=message, state=state)
    msg = await message.answer('Теперь дайте короткое описание товара', reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(AddProduct.description)


@admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), AddProduct.description)
async def admin_process_description(message: Message, state: FSMContext, session_without_commit: AsyncSession):
    await state.update_data(description=message.html_text)
    await process_del_text_msg(message=message, state=state)
    catalog_data = await CategoryDao.find_all(session_without_commit)
    msg = await message.answer('Теперь выберите категрию товара: ', reply_markup=catalog_admin_kb(catalog_data))
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(AddProduct.category_id)


@admin_router.callback_query(F.data.startswith('add_category_'), F.from_user.id.in_(settings.ADMIN_IDS),
                             AddProduct.category_id)
async def admin_process_add_category(call: CallbackQuery, state: FSMContext):
    category_id = int(call.data.split('_')[-1])
    await state.update_data(category_id=category_id)
    await  call.message.answer('Категория товара успешно выбрана')
    msg = await call.message.edit_text(text='Выберите цену товара: ', reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(AddProduct.price)


@admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), AddProduct.price)
async def admin_process_price(message: Message, state: FSMContext):
    text = message.text.strip()

    if not text.isdigit():
        await message.answer('Цена должна быть целым положительным числом')
        return

    await state.update_data(price=int(text))
    await process_del_text_msg(message=message, state=state)
    await message.answer('Выберите отправку файла, если файла нет, отправьте Без Файла',
                         reply_markup=admin_send_file_kb())
    await state.update_data(last_msg_id=message.message_id)
    await state.set_state(AddProduct.file_id)


@admin_router.callback_query(F.data == 'without_file', F.from_user.id.in_(settings.ADMIN_IDS), AddProduct.file_id)
async def admin_process_without_file(call: CallbackQuery, state: FSMContext):
    await state.update_data(file_id=None)
    await call.message.answer('файл не выбран')
    msg = await call.message.answer(
        text="Теперь отправьте контент, который отобразится после покупки товара внутри карточки",
        reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(AddProduct.file_id)


@admin_router.message(F.document, F.from_user.id.in_(settings.ADMIN_IDS), AddProduct.file_id)
async def admin_process_with_file(message: Message, state: FSMContext):
    await state.update_data(file_id=message.document.file_id)
    await process_del_text_msg(message=message, state=state)
    msg = await message.answer('Теперь отправьте контент, который отобразится после покупки товара внутри карточки',
                               reply_markup=cancel_kb_inline())
    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(AddProduct.hidden_content)


@admin_router.message(F.text, F.from_user.id.in_(settings.ADMIN_IDS), AddProduct.hidden_content)
async def admin_process_hidden_text(message: Message, state: FSMContext, session_without_commit: AsyncSession):
    await state.update_data(hidden_content=message.html_text)
    product_data = await state.get_data()
    category_info = await CategoryDao.find_one_or_none_by_id(data_id=product_data.get('category_id'),
                                                             session=session_without_commit)

    file_id = product_data.get('file_id')
    file_text = "📦 Товар с файлом" if file_id else "📄 Товар без файла"

    product_text = (f'🛒 Проверьте, все ли корректно:\n\n'
                    f'🔹 <b>Название товара:</b> <b>{product_data["name"]}</b>\n'
                    f'🔹 <b>Описание:</b>\n\n<b>{product_data["description"]}</b>\n\n'
                    f'🔹 <b>Цена:</b> <b>{product_data["price"]} ₽</b>\n'
                    f'🔹 <b>Описание (закрытое):</b>\n\n<b>{product_data["hidden_content"]}</b>\n\n'
                    f'🔹 <b>Категория:</b> <b>{category_info.category_name} (ID: {category_info.id})</b>\n\n'
                    f'<b>{file_text}</b>')
    await process_del_text_msg(message, state)

    if file_id:
        msg = await message.answer_document(document=file_id, caption=product_text, reply_markup=admin_confirm_kb())
    else:
        msg = await message.answer(text=product_text, reply_markup=admin_confirm_kb())

    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(AddProduct.confirm_add)


@admin_router.callback_query(F.data == 'confirm_add', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_confirm_add(call: CallbackQuery, state: FSMContext, session_with_commit: AsyncSession):
    await call.answer("Приступаем к сохранению продукта...")
    product_data = await state.get_data()
    await bot.delete_message(call.from_user.id, message_id=product_data['last_msg_id'])
    del product_data['last_msg_id']
    await ProductDao.add(session=session_with_commit, values=ProductModel(**product_data))
    await call.message.answer('Товар успешно добавлен в базу данных', reply_markup=admin_kb())


@admin_router.callback_query(F.data == 'home', F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_process_home(call: CallbackQuery):
    await call.message.edit_text(text='Вы вернулись на главный экран', reply_markup=admin_kb())