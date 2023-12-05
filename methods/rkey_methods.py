from telegram import ReplyKeyboardMarkup

from methods.data_methods import get_cat_list, get_item_list

"""
Methods for generating the button keyboards shown to the user 
Example: When a user is asked what category does the item they are requesting belong to, they are shown
a keyboard showing all the possible categories.
"""

def show_keyboard_start(telegram_id, role):
    if role == "admin":
        keyboard = [["Register", "Loan"], ["Laundry"]]
        return ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        )
    elif role == "user":
        keyboard = [["Laundry", "Loan"]]
        return ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        )


def show_keyboard_cat():
    keyboard = get_cat_list()
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def show_keyboard_items(cat_name):
    keyboard = get_item_list(cat_name)
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def show_keyboard_conf():
    keyboard = [["Confirm", "Cancel"]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def show_keyboard_conf_loan():
    keyboard = [
        ["Request Another Item", "Cancel Loan Request"],
        ["Confirm Order", "Cancel Order"],
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def show_keyboard_laundry_conf():
    keyboard = [["Complete Laundry Update", "Do Not Update"]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
