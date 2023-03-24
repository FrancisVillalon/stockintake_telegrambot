from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()


class Stock(Base):
    __tablename__ = "stock"
    item_id = Column(Integer, primary_key=True)
    item_eos = Column(String)
    item_description = Column(String)
    item_quantity = Column(Integer)
    item_name = Column(String)
    img_path = Column(String)
    cat_id = Column(Integer)

    def __repr__(self):
        return (
            f"<Stock(\n"
            f"item_id='{self.item_id}', item_eos='{self.item_eos}',\n"
            f"item_description='{self.item_description}', item_quantity='{self.item_quantity},'\n"
            f"item_name='{self.item_name}', img_path='{self.img_path}',cat_id='{self.cat_id}'"
            f")>"
        )


class Audit(Base):
    __tablename__ = "audit"
    log_id = Column(Integer, primary_key=True)
    log_datetime = Column(DateTime)
    telegram_id = Column(String)
    telegram_name = Column(String)
    item_name = Column(String)
    item_id = Column(String)
    action_quantity = Column(Integer)
    action_type = Column(String)

    def __repr__(self):
        return (
            f"<Audit(\n"
            f"log_id='{self.log_id}', log_datetime='{self.log_datetime}',\n"
            f"telegram_id='{self.telegram_id}', telegram_name='{self.telegram_name}',\n"
            f"item_name='{self.item_name}',item_id='{self.item_id}',\n"
            f"action_quantity='{self.action_quantity}', action_type='{self.action_type}'"
            f")>"
        )


class Category(Base):
    __tablename__ = "category"
    cat_id = Column(Integer, primary_key=True)
    cat_name = Column(String)

    def __repr__(self):
        return f"<Category(cat_id='{self.cat_id}', cat_name='{self.cat_name}')>"


class User(Base):
    __tablename__ = "user"
    telegram_id = Column(String, primary_key=True)
    telegram_name = Column(String)
    role = Column(String)

    def __repr__(self):
        return f"<User(telegram_id='{self.telegram_id}', telegram_name='{self.telegram_name}, role='{self.role}')>"
