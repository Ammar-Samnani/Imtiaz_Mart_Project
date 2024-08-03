from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    full_name: str
    email: str
    number: str
    address: str | None


class User_Update(SQLModel):
    full_name: str
    email: str
    number: str
    address: str | None