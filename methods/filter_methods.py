from telegram.ext.filters import MessageFilter
from methods.data_methods import *


class filter_category_only(MessageFilter):
    def filter(self, message):
        return message.text in get_cat_list()


class filter_not_conf(MessageFilter):
    def filter(self, message):
        return message.text not in ["Confirm", "Cancel", "Request Another Item"]


filter_category_only = filter_category_only()
