from pydantic import BaseModel, ConfigDict


class TelegramIDModel(BaseModel):
    telegram_id: int

    model_config = ConfigDict(from_attributes=True)


class UserModel(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None
    last_name: str | None

class ProductIDModel(BaseModel):
    id: int


class ProductCategoryIDModel(BaseModel):
    category_id: int


