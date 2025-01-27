from sqlmodel import SQLModel, Field
from datetime import date
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

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    password: str  # Hashed password
    birthdate: date


class UserStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id") 
    wallet: float = Field(default=0.0)
    calories: float = Field(default=0.0)