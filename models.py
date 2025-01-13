from sqlmodel import SQLModel, Field
from typing import Optional

class Products(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    category_id: Optional[int] = Field(default=None)

class Categories(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
