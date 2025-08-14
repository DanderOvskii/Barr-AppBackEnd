from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DECIMAL
from datetime import date
from decimal import Decimal
from typing import Optional, List

class Products(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: int
    amount: int
    category_id: Optional[int] = Field(default=None)
    calorien: float
    alcohol: float
    vooraad: int
    korting:int

class productResponse(SQLModel):
    id: int
    name: str
    price: float
    amount: int
    category_id: Optional[int] = Field(default=None)
    calorien: float
    alcohol: float
    vooraad: int
    korting:int
    discount_price:float


class Categories(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    
class CategoryWithProducts(SQLModel):
    id: int
    name: str
    products: List[Products]

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    password: str  # Hashed password
    birthdate: date
    is_admin: bool = Field(default=False)


class UserStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id") 
    wallet: int = Field(default=0)
    calories: float = Field(default=0.0)
    alcohol: float = Field(default=0.0)

class UserUpdate(SQLModel):
    username: str
    password: Optional[str] = None
    wallet: int

class Purchase(SQLModel,table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    product_id: int
    amount: int
    product_price:int
    total_price: int
    discount: int = Field(default=0)
    purchase_date:date