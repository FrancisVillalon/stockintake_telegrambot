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
    log_id = Column(String, primary_key=True)
    log_datetime = Column(DateTime)
    telegram_id = Column(String)
    log_action = Column(String)
    log_description = Column(String)

    def __repr__(self):
        return (
            f"<Audit(\n"
            f"log_id='{self.log_id}', log_datetime='{self.log_datetime}',\n"
            f"telegram_id='{self.telegram_id}',\n"
            f"log_action='{self.log_action}',log_description='{self.log_description}',\n"
            f")>"
        )


class Loan(Base):
    __tablename__ = "loan"
    loan_id = Column(String, primary_key=True)
    telegram_id = Column(String)
    loan_status = Column(String)
    item_id = Column(Integer)
    item_quantity = Column(String)
    approved_by = Column(String)
    approved_datetime = Column(DateTime)
    order_id = Column(String)

    def __repr__(self):
        return (
            f"<Loan(\ntelegram_id='{self.telegram_id}',order_id='{self.order_id}',\n"
            f"loan_id ='{self.loan_id}',loan_status='{self.loan_status}',\n"
            f"item_id='{self.item_id}',item_quantity='{self.item_quantity}',\n"
            f"approved_by='{self.approved_by}',approved_datetime='{self.approved_datetime}',\n"
            f")>"
        )


class Ordr(Base):
    __tablename__ = "ordr"
    order_id = Column(String, primary_key=True)
    telegram_id = Column(String)
    order_datetime = Column(DateTime)

    def __repr__(self):
        return f"<Ordr(order_id='{self.order_id}',telegram_id='{self.telegram_id}',order_datetime='{self.order_datetime}')>"


class Category(Base):
    __tablename__ = "category"
    cat_id = Column(Integer, primary_key=True)
    cat_name = Column(String)

    def __repr__(self):
        return f"<Category(cat_id='{self.cat_id}', cat_name='{self.cat_name}')>"


class Usr(Base):
    __tablename__ = "usr"
    telegram_id = Column(String, primary_key=True)
    telegram_username = Column(String)
    role = Column(String)

    def __repr__(self):
        return f"<User(telegram_id='{self.telegram_id}', telegram_username='{self.telegram_username}, role='{self.role}')>"


class Applicant(Base):
    __tablename__ = "applicant"
    telegram_id = Column(String, primary_key=True)
    telegram_username = Column(String)

    def __repr__(self):
        return f"<Applicant(telegram_id='{self.telegram_id}', telegram_username='{self.telegram_username}')>"
