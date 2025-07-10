from typing import TypeVar, Generic

from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, func
from app.DAO.database import Base

T = TypeVar("T", bound=Base)


class BaseDao(Generic[T]):
    model: type[T]

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int, session: AsyncSession):
        logger.info(f'Поиск {cls.model.__name__} c ID: {data_id}')
        try:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f'Запись с ID{data_id} найдена')
            else:
                logger.info(f'Запись с ID{data_id} не найдена')
            return record
        except SQLAlchemyError as e:
            logger.error(f'Ошибка при поиске записи с ID{data_id} {e}')
            raise

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel):
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}
        logger.info(f'Поиск {cls.model.__name__} по фильтрам: {filters}')
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f'Запись с фильтрами{filter_dict} найдена')
            else:
                logger.info(f'Запись с фильтрами{filter_dict} не найдена')
                return record
        except SQLAlchemyError as e:
            logger.error(f'Ошибка при поиске записи по фильтрам {filter_dict}')
            raise
    @classmethod
    async def add(cls, values: BaseModel, session: AsyncSession):
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(f'Добавление {values_dict}')
        new_instance = cls.model(**values_dict)
        session.add(new_instance)
        try:
            await session.flush()
            logger.info(f'запсиь успешно добавлена')
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(e)
            raise e
        return new_instance


    @classmethod
    async def delete(cls, session: AsyncSession, filters: BaseModel):
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f'удaление записи {cls.model.__name__} по фильтрам: {filter_dict}')
        if not filter_dict:
            logger.info('Нужен хотя бы один фильтр для удаления')
            raise ValueError('Нужен хотя бы один фильтр для удаления')

        query = sqlalchemy_delete(cls.model).filter_by(**filter_dict)
        try:
            result = await session.execute(query)
            await session.flush()
            logger.info(f'Удалено колличество записей {result.rowcount}')
            return result.rowcount
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(e)
            raise e


    @classmethod
    async def count(cls, session: AsyncSession, filters: BaseModel | None = None):
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}
        logger.info(f'Подчет колличества записей по фильтру: {filter_dict}')
        try:
            query = select(func.count(cls.model.id)).filter_by(**filter_dict)
            result = await session.execute(query)
            count = result.scalar()
            logger.info(f'Найдено{count} колличество записей')
            return count
        except SQLAlchemyError as e:
            logger.info(f'Ошибка при подчете записей {e}')
            raise

    @classmethod
    async def find_all(cls, session: AsyncSession, filters: BaseModel | None = None):
        query = select(cls.model).filter_by(**filters.model_dump(exclude_unset=True))
        result = await session.execute(query)
        return result.scalars().all()

