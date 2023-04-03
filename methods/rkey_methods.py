from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from database.db_conn import *

s = db.create_session()


def show_keyboard(telegram_id, role):
    if role == "admin":
        keyboard = [["Register", "Loan"]]
        return ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        )
    elif role == "user":
        keyboard = [["Loan"]]
        return ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        )


def show_keyboard_cat():
    keyboard = [[cat_name for (cat_name,) in s.query(Category.cat_name).all()]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)


def show_keyboard_items(cat_name):
    cat_id = int(
        s.query(Category).filter(Category.cat_name == str(cat_name)).first().cat_id
    )
    keyboard = [
        item_name
        for (item_name, cat_id) in s.query(Stock.item_name, Stock.cat_id)
        .filter(Stock.cat_id == int(cat_id))
        .all()
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
