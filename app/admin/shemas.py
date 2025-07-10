from dataclasses import Field

from pydantic import BaseModel, Field


class ProductIDModel(BaseModel):
    id: int



class ProductModel(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: str = Field(..., min_length=3)
    price: float = Field(..., gt=0)
    category_id: int = Field(..., gt=0)
    file_id: str | None = None
    hidden_content: str = Field(..., min_length=3)