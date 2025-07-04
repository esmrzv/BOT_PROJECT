from typing import Optional, List

from sqlalchemy import BigInteger, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.DAO.database import Base


class User(Base):
    telegram_id: Mapped[int] = mapped_column(BigInteger,unique=True, nullable=False)
    username: Mapped[Optional[str]]
    first_name: Mapped[Optional[str]]
    last_name: Mapped[Optional[str]]
    purchases:Mapped[List["Purchase"]] = relationship("Purchase", back_populates="user",
                                                      cascade="all, delete-orphan")

    def __repr__(self):
        return (f'<User(id{self.id}, telegram_id={self.telegram_id}, username={self.username}, '
                f'first_name={self.first_name}, last_name={self.last_name})>')


class Category(Base):
    __tablename__ = 'categories'


    category_name: Mapped[str] = mapped_column(Text, nullable=False)
    products: Mapped[List["Product"]] = relationship("Product",
                                        back_populates="category",
                                                     cascade="all,delete-orphan")

    def __repr__(self) -> str:
        return f'<Category id:{self.id}, name:{self.category_name}>'



class Product(Base):
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[int]
    file_id: Mapped[Optional[str]] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    hidden_content: Mapped[str] = mapped_column(Text)
    category: Mapped[Category] = relationship("Category", back_populates='products')
    purchases: Mapped[List['Purchase']] = relationship("Purchase", back_populates="product",
                                                       cascade="all,delete-orphan")




class Purchase(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    price: Mapped[int]
    user: Mapped[User] = relationship("User", back_populates="purchases")
    product: Mapped[Product] = relationship("Product", back_populates="purchases")

    def __repr__(self) -> str:
        return f'<Purchase id:{self.id}, user_id:{self.user_id}, product_id:{self.product_id}>'





