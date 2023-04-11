from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from database.db_conn import *
from methods.data_methods import *


def show_keyboard_start(telegram_id, role):
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
    keyboard = [get_cat_list()]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)


def show_keyboard_items(cat_name):
    keyboard = [get_item_list(cat_name)]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
