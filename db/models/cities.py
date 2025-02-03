from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Integer, String
from db.models.base import Base

class Cities(Base):
    __tablename__ = 'cities'

    citiId: Mapped[int] = mapped_column(Integer, primary_key=True,autoincrement=True)
    citiName: Mapped[str] = mapped_column(String, use_existing_column=False)
    temp: Mapped[int] = mapped_column(Integer, use_existing_column=False)
    speed: Mapped[int] = mapped_column(Integer, use_existing_column=False)
    pressure: Mapped[int] = mapped_column(Integer, use_existing_column=False)