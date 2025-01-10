from sqlmodel import SQLModel, Field
from typing import Optional

class Items(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
