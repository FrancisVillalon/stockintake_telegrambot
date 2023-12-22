from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from methods.data_methods import get_all_items_cat, get_cat_list

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


# Dynamic Keyboards
def show_keyboard_cat():
    cat_list = get_cat_list()
    keyboard = [cat_list[x : x + 3] for x in range(0, len(cat_list), 3)]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def show_keyboard_items(cat_name):
    item_list = get_all_items_cat(cat_name)
    item_list = [x["item_name"] for x in item_list]
    keyboard = [item_list[x : x + 3] for x in range(0, len(item_list), 3)]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


# Static Keyboards
def show_keyboard_conf():
    keyboard = [["Confirm", "Cancel"]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def show_keyboard_conf_order():
    keyboard = [["Submit Order", "View Order"], ["/new_lr", "/new_ordr"], ["/cancel"]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def show_keyboard_laundry_conf():
    keyboard = [["Complete Laundry Update", "Do Not Update"]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
