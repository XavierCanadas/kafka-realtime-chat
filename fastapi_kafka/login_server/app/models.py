from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    username: str = Field(primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(unique=True)
    password_hash: str
    disabled: bool = Field(default=False)