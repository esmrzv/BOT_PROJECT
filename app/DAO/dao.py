from cgitb import reset

from app.DAO.BaseDao import BaseDao
from app.DAO.models import Category, Product, Purchase, User
from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict

from loguru import logger
from sqlalchemy import select, func, case, except_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class CategoryDao(BaseDao[Category]):
    model = Category


class ProductDao(BaseDao[Product]):
    model = Product


class PurchaseDao(BaseDao[Purchase]):
    model = Purchase

    @classmethod
    async def get_summ(cls, session: AsyncSession):
        query = select(func.sum(cls.model.price).label('total_price'))
        result = await session.execute(query)
        record = result.scalar().one_or_none()
        return record if record is not None else 0


class UserDao(BaseDao[User]):
    model = User

    @classmethod
    async def get_purchase_statistics(cls, session: AsyncSession, telegram_id: int):
        try:
            smtp = (
                select(
                    func.count(Purchase.id).label('total_purchases'),
                    func.sum(Purchase.price).label('total_amount')
                ).join(Purchase.user).where(Purchase.user.telegram_id == telegram_id).select_from(Purchase)

            )
            stats = await session.execute(smtp)
            total_purchases, total_amount = stats
            return {
                'total_purchases': total_purchases,
                'total_amount': total_amount if total_amount is not None else 0,
            }

        except SQLAlchemyError as e:
            print(f'Ошибка при подчете колличества покупок {e}')
            return None

    @classmethod
    async def get_purchased_products(cls, session: AsyncSession, telegram_id: int):
        try:
            result = await session.execute(
                select(User).options(
                    selectinload(User.purchases).selectinload(Purchase.product)
                ).filter(Purchase.user.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user is None:
                return None
            return user
        except SQLAlchemyError as e:
            print(f'Ошибка при получении информации о покупках{e}')
            return None

    @classmethod
    async def get_statistics(cls, session: AsyncSession):
        try:
            now = datetime.now(UTC)

            query = select(
                func.count().label("total_users"),
                func.sum(case((cls.model.created_at >= now - timedelta(days=1), 1), else_=0)).label('new_today'),
                func.sum(case((cls.model.created_at >= now - timedelta(days=7), 1), else_=0)).label('new_week'),
                func.sum(case((cls.model.created_at >= now - timedelta(days=30), 1), else_=0)).label('new_month')
            )
            result = await session.execute(query)
            stats = result.fetchone()

            statistics = {
                'total_users': stats.total_users,
                'new_today': stats.new_today,
                'new_week': stats.new_week,
                'new_month': stats.new_month
            }

            logger.info('статистика получена')
            return statistics
        except SQLAlchemyError as e:
            logger.info(f'ошибка при получении статистики{e}')
            raise
