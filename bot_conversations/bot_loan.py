"""
Loan conversation 

Conversation flow:
ACTION_START (comes bot_start.py) -> LOAN_START -> LOAN_CAT_SELECT -> LOAN_ITEM_SELECT -> LOAN_QUANTITY_SELECT -> LOAN_REQUEST_CONF -> LOAN_ORDER_CONF->END
LOAN_REQUEST_CONF -> LOAN_ORDER_CONF (If user cancels loan request at this point)
LOAN_ORDER_CONF (This state has 4 options, create new loan request to add, submit, cancel , recreate order)


An Order is made up of Loan Requests -> A Loan Request is made up of Item category, Item quantity, Item name
"""

import uuid
from datetime import datetime
from re import match
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import plotly.figure_factory as ff
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from database.db_conn import Database
from methods.acl_methods import *
from methods.data_methods import *
from methods.rkey_methods import *

db = Database()

LOAN_CAT_SELECT = 0
LOAN_ITEM_SELECT = 1
LOAN_QUANT_SELECT = 2
LOAN_REQUEST_CONF = 3
LOAN_ORDER_CONF = 4

# * Button Map
button_map = {
    "New Loan Request": "new_lr",
    "New Order": "new_ordr",
}


# * Fallbacks
# Handling premature exit of operation
async def loan_premature_cancel(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.effective_chat.send_message(
        "Loan prematurely cancelled.",
        reply_markup=show_keyboard_start(
            update.effective_chat.id, context.user_data["role"]
        ),
    )
    context.user_data.clear()
    return ConversationHandler.END


# * Conversation States
# Loan route entry
async def loan_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Var to check if user has visisted this state before
    if (
        "in_conversation" in context.user_data.keys()
        and context.user_data["in_conversation"]
    ):
        been_here = True
    else:
        been_here = False
    # Set user as busy
    context.user_data["in_conversation"] = True
    context.user_data["role"] = get_user_role(update.effective_chat.id)
    # Handling situations where the user cancelled a lr or order before maturity or when creating new loan request from final state
    command = (
        update.message.text
        if button_map.get(update.message.text) is None
        else button_map[update.message.text]
    )
    if "new_lr" in command and "temp_lr" in context.user_data.keys():
        context.user_data.pop("temp_lr")
        await update.message.reply_text(f"Current loan request cancelled")
    elif "new_ordr" in command and "order" in context.user_data.keys():
        context.user_data.pop("order")
        await update.message.reply_text(f"Current order cleared.")
    elif "new_lr" in command:
        await update.message.reply_text(f"New loan request started.")
    # Check if there is an existing order
    if (
        "order" in context.user_data.keys()
        and context.user_data["order"].get("order_id", None)
        and len(context.user_data["order"]["loans"].keys()) != 0
    ):
        # Show existing order
        existing_order = dict(context.user_data["order"]["loans"])
        order_df = pd.DataFrame.from_dict(existing_order).T[
            ["cat_name", "item_name", "item_quantity"]
        ]
        order_df.index.name = "item_id"
        fig_id = str(uuid.uuid4())
        fig = ff.create_table(order_df)
        fig.update_layout(autosize=True)
        fig.write_image(f"./database/data/images/df_images/{fig_id}.png", scale=2)
        await update.message.reply_photo(
            f"./database/data/images/df_images/{fig_id}.png",
            caption="Existing Order",
        )
        await update.message.reply_text(
            f"Shown is your current order with added loan requests. \n'/new_ordr' to start a new order."
        )
    elif (
        not been_here or "order" not in context.user_data.keys()
    ):  # First time visiting this route or /new_ordr
        context.user_data["order"] = {}
        context.user_data["order"]["loans"] = {}
        context.user_data["order"]["order_id"] = str(uuid.uuid4())[:8]
        await update.message.reply_text(
            f"You have started a new order with order id: {context.user_data['order']['order_id']}!"
        )
    # Prompt user to select category, we start the loan request after this question is answered
    await update.message.reply_text(
        f"Please select a category to create a loan request for an item!",
        reply_markup=show_keyboard_cat(),
    )
    return LOAN_CAT_SELECT


async def loan_cat_select(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> Optional[int]:
    cat_name = update.message.text
    # Ensure category provided is in valid categories
    if cat_name not in get_cat_list():
        await update.message.reply_text(
            f"That is not a valid category. Please select a category.",
            reply_markup=show_keyboard_cat(),
        )
        return None
    else:
        # Instantiate temp_lr dictionary to hold values of loan request as it gets edited
        context.user_data["temp_lr"] = {}
        context.user_data["temp_lr"]["cat_name"] = cat_name
        await update.message.reply_text(
            f"You have created a loan request for an item in category: {cat_name} !\n Please select the item you wish to loan.",
            reply_markup=show_keyboard_items(cat_name),
        )
        return LOAN_ITEM_SELECT


async def loan_item_select(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> Optional[int]:
    # Ensuring temp_lr and cat_name is present in context otherwise end conversation
    if "temp_lr" not in context.user_data.keys() or not context.user_data[
        "temp_lr"
    ].get("cat_name", None):
        await update.message.reply_text(
            f"There is no existing loan request or the request is invalid. \n Please redo the loan request."
        )
        return ConversationHandler.END
    # Check item name
    item_name = update.message.text
    # Check if item exists in category
    item_names_in_cat = [
        x["item_name"]
        for x in get_all_items_cat(context.user_data["temp_lr"]["cat_name"])
    ]
    # Ensure the selected item is actually found in this category
    if item_name not in item_names_in_cat:
        await update.message.reply_text(
            f"That item does not exists in category: {context.user_data['temp_lr']['cat_name']}.",
            reply_markup=show_keyboard_items(context.user_data["temp_lr"]["cat_name"]),
        )
        return None
    else:
        # Item belongs in this category
        context.user_data["temp_lr"]["item_name"] = item_name
        item_id = get_item_id(context.user_data["temp_lr"]["cat_name"], item_name)
        # Item quantity and id validation
        if item_id:
            item_details = get_item_details(item_id)
        else:
            await update.message.reply_text(
                f"We were not able to retrieve the item id of this item.\n Please try again."
            )
            return None
        # Check if item available
        if item_details["item_quantity"] <= 0:
            await update.message.reply_text(
                f"This item is not currently available, please choose another one in this category or cancel the current loan request with '/new_lr'.",
                reply_markup=show_keyboard_items(
                    context.user_data["temp_lr"]["cat_name"]
                ),
            )
            return None
        # Display item details in table
        else:
            await update.message.reply_photo(
                item_details["img_path"],
                caption=f"Item Name: {item_details['item_name']}\nItem Stock: {item_details['item_quantity']}\n\n{item_details['item_description']}",
            )
            # Item is in stock, prompt user for how much to loan
            await update.message.reply_text(
                f"You have selected '{item_name}' in category: {context.user_data['temp_lr']['cat_name']}.\n\nHow much of this item do you wish to loan?"
            )
            # update context
            context.user_data["item_id"] = item_id
            context.user_data["selected_item_details"] = item_details
            return LOAN_QUANT_SELECT


async def loan_quant_select(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> Optional[int]:
    # Ensuring temp_lr, cat_name, item_name is present in context otherwise end conversation
    if (
        "temp_lr" not in context.user_data.keys()
        or not context.user_data["temp_lr"].get("cat_name", None)
        or not context.user_data["temp_lr"].get("item_name", None)
    ):
        await update.message.reply_text(
            f"There is no existing loan request or the request is invalid. \n Please redo the loan request."
        )
        return ConversationHandler.END
    # Quantity selection for item
    quantity_selected = update.message.text
    current_item_quant = context.user_data["selected_item_details"]["item_quantity"]
    # Input validation
    if (
        not match(r"^\d+$", quantity_selected)
        or int(quantity_selected) > int(current_item_quant)
        or int(quantity_selected) == 0
    ):
        await update.message.reply_text(
            f"You selected an invalid quantity.\nCurrent stock is '{current_item_quant}'. "
        )
        return None
    else:
        item_name = context.user_data["temp_lr"]["item_name"]
        cat_name = context.user_data["temp_lr"]["cat_name"]
        await update.message.reply_text(
            f"Are you sure you want to loan {quantity_selected} of {item_name} from category: {cat_name}",
            reply_markup=show_keyboard_conf(),
        )
        # Update loan request values -> By this point the loan request should contain item_id,item_quantity,item_category,item_name
        context.user_data["temp_lr"]["item_quantity"] = quantity_selected
        return LOAN_REQUEST_CONF


async def loan_request_conf(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> Optional[int]:
    user_response = update.message.text

    if str(user_response).lower() == "confirm":
        # Add uid to loan request, used for lookup in loans table
        loan_id = str(uuid.uuid4())[:16]
        context.user_data["temp_lr"]["loan_id"] = loan_id
        context.user_data["temp_lr"]["cat_id"] = context.user_data[
            "selected_item_details"
        ]["cat_id"]
        item_id = context.user_data.pop("item_id")  # used as key in loans
        # Add loan request to order dictionary and remove temp_lr from context
        selected_item_details = context.user_data.get("selected_item_details", None)
        if selected_item_details:
            context.user_data.pop("selected_item_details")
        if context.user_data["order"]["loans"].get(item_id, None):
            current_quantity = context.user_data["order"]["loans"][item_id][
                "item_quantity"
            ]
            new_quantity = context.user_data["temp_lr"]["item_quantity"]
            item_name = context.user_data["order"]["loans"][item_id]["item_name"]
            if current_quantity != new_quantity:
                await update.message.reply_text(
                    f"Updating quantity of loan for {item_name} from {current_quantity} -> {new_quantity}"
                )
        context.user_data["order"]["loans"][item_id] = context.user_data.pop("temp_lr")
        await update.message.reply_text(
            f"Loan request successfully added to order.\n\nWhat would you like to do?\n\nView Order - Shows current order\nSubmit Order - Confirms order and submits it\n/new_lr - Starts new loan request\n/new_ordr - Starts new order and clears current one\n/cancel - Exits loan process",
            reply_markup=show_keyboard_conf_order(),
        )

        return LOAN_ORDER_CONF
    elif str(user_response).lower() == "cancel":
        context.user_data.pop("temp_lr")
        await update.message.reply_text(
            f"You have cancelled the current loan request.\n\nWhat would you like to do?\n\nView Order - Shows current order\nSubmit Order - Confirms order and submits it\n/new_lr - Starts new loan request\n/new_ordr - Starts new order and clears current one\n/cancel - Exits loan process",
            reply_markup=show_keyboard_conf_order(),
        )
        return LOAN_ORDER_CONF
    else:
        await update.message.reply_text(
            f"Please only reply with 'Confirm' or 'Cancel' to proceed.",
            reply_markup=show_keyboard_conf(),
        )
        return None


async def loan_order_conf(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> Optional[int]:
    command = update.message.text
    if command == "Submit Order":
        # Submit order to database
        order_id = context.user_data["order"]["order_id"]
        tid = update.effective_chat.id
        # Submit loan request
        for item_id, item_details in context.user_data["order"]["loans"].items():
            set_pending_loan(item_id, item_details, order_id, tid)
        # Submit order
        set_order(
            order_id,
            tid,
            datetime.now(),
        )
        # conversation over, update conversation status
        context.user_data.clear()
        await update.message.reply_text("Successfully submitted your order.")
        await update.message.reply_text(f"/start to do something else!")
        return ConversationHandler.END
    elif command == "View Order":
        # Show existing order
        existing_order = dict(context.user_data["order"]["loans"])
        order_df = pd.DataFrame.from_dict(existing_order).T[
            ["cat_name", "item_name", "item_quantity"]
        ]
        order_df.index.name = "item_id"
        fig_id = str(uuid.uuid4())
        fig = ff.create_table(order_df)
        fig.update_layout(autosize=True)
        fig.write_image(f"./database/data/images/df_images/{fig_id}.png", scale=2)
        await update.message.reply_photo(
            f"./database/data/images/df_images/{fig_id}.png",
            caption="Existing Order",
        )
        await update.message.reply_text(
            f"What would you like to do?", reply_markup=show_keyboard_conf_order()
        )
    else:
        await update.message.reply_text(
            "Please only select from the menu.", reply_markup=show_keyboard_conf_order()
        )
        return None
