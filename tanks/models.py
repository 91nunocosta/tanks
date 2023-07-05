from sqlmodel import Field, SQLModel


class Thank(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
