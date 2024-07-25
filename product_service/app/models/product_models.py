from sqlmodel import SQLModel, Field


class Product(SQLModel, table=True):
  id: int = Field(default=None , primary_key=True)
  name: str
  price: float
  expiry: str
  brand: str
  weight: float
  category: str

class Product_Update(SQLModel):
  name: str
  price: float
  expiry: str
  brand: str
  weight: float
  category: str