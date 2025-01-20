from sqlmodel import SQLModel, Field
from typing import Optional, List

class Products(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    category_id: Optional[int] = Field(default=None)
    calorien: float
    alcohol: float
    vooraad: int
    korting:int

class Categories(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    
class CategoryWithProducts(SQLModel):
    id: int
    name: str
    products: List[Products]
