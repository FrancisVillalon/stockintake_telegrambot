import tomllib
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.engine import URL
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import close_all_sessions
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date

Base = declarative_base()


class Stock(Base):
    __name__ = "stock"
    item_id = Column(Integer, primary_key=True)
    item_eos = Column(String)
    item_description = Column(String)
    item_quantity = Column(Integer)
    item_name = Column(String)
    img_path = Column(String)
    cat_id = Column(Integer)

    def __repr__(self):
        return (
            f"<Stock(item_id='{self.item_id}', item_eos='{self.item_eos}',\n"
            f"item_description='{self.item_description}', item_quantity='{self.item_quantity},'\n"
            f"item_name='{self.item_name}', img_path='{self.img_path}',cat_id='{self.cat_id}')>"
        )


class Category(Base):
    __name__ = "category"
    cat_id = Column(Integer, primary_key=True)
    cat_name = Column(String)

    def __repr__(self):
        return f"<Category(cat_id='{self.cat_id}', cat_name='{self.cat_name}')>"


class User(Base):
    __name__ = "user"
    telegram_id = Column(Integer, primary_key=True)
    telegram_name = Column(String)
    role = Column(String)
