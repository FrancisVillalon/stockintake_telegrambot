from telegram.ext.filters import MessageFilter

from methods.data_methods import get_all_item_list, get_cat_list

"""
Filter classes used in the bot MessageHandlers to ensure user response is appropriate
"""


class filter_category_only(MessageFilter):
    def filter(self, message):
        cat_list = get_cat_list()
        return message.text in cat_list


class filter_item_only(MessageFilter):
    def filter(self, message):
        item_list = get_all_item_list()
        return message.text in item_list


class filter_not_conf(MessageFilter):
    def filter(self, message):
        fil_bool = message.text not in [
            "Confirm Order",
            "Cancel Order",
            "Cancel Loan Request",
            "Request Another Item",
        ]
        return fil_bool


class filter_is_conf(MessageFilter):
    def filter(self, message):
        fil_bool = message.text in [
            "Confirm Order",
            "Cancel Order",
            "Cancel Loan Request",
            "Request Another Item",
        ]
        return fil_bool


filter_item_only = filter_item_only()
filter_category_only = filter_category_only()
filter_not_conf = filter_not_conf()
filter_is_conf = filter_is_conf()
