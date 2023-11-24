import uuid

import matplotlib.pyplot as plt
import pandas as pd
import plotly.figure_factory as ff
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from methods.acl_methods import *
from methods.rkey_methods import *

ACTION_START, LOAN_STATE, REG_STATE, LAUN_STATE = range(4)
# Loan route entry
async def loan_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Instantiate order id as well as empty order dictionary
    text = update.message.text
    context.user_data["choice"] = text
    context.user_data["order_id"] = str(uuid.uuid4())[:8]
    context.user_data["order"] = {}
    # User selects category
    await update.message.reply_text(
        f"What is the category of the item?", reply_markup=show_keyboard_cat()
    )
    return LOAN_STATE

#LOAN_STATE
async def loan_item_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    # User selects item and loan request disctionary is instantiated in user_data dict
    cat_name = update.message.text
    temp_lr = {}
    temp_lr["cat_name"] = cat_name
    context.user_data["temp_lr"] = temp_lr
    await update.message.reply_text(
        f"What item in {cat_name}?", reply_markup=show_keyboard_items(cat_name)
    ),
    return LOAN_STATE


async def loan_quant_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    # Check if lr exists
    user_data = context.user_data
    if "temp_lr" not in user_data.keys():
        usr_role = get_user_role(update.effective_chat.id)
        user_data["role"] = get_user_role(usr_role)
        await update.effective_chat.send_message(
            f"Invalid operation performed. Returning to start."
        )
        await update.effective_chat.send_message(
            f"Welcome back {update.effective_chat.username}! What would you like to do today?",
            reply_markup=show_keyboard_start(update.effective_chat.id, usr_role),
        )
        return ACTION_START

    # Update lr
    item_selected = update.message.text
    temp_lr = dict(context.user_data["temp_lr"])
    temp_lr["item_name"] = item_selected
    try:
        item_id = get_item_id(temp_lr["cat_name"], temp_lr["item_name"])
    except:
        await update.message.reply_text(
            f"Query for '{temp_lr['item_name']}' under '{temp_lr['cat_name']}' has failed.\nPlease reselect item from menu.",
            reply_markup=show_keyboard_items(temp_lr["cat_name"]),
        )
        return LOAN_STATE
    temp_lr["item_id"] = item_id
    context.user_data["temp_lr"] = temp_lr

    # Display current stock
    item_details = get_item_details(item_id)
    if item_details.item_quantity <= 0:
        if "temp_lr" in context.user_data.keys():
            del context.user_data["temp_lr"]
        await update.message.reply_text(
            f"This item is currently unavailable.\nLoan request for this item has been cancelled.\nPlease choose what to do next.",
            reply_markup=show_keyboard_conf_loan(),
        )
        return LOAN_STATE
    # Display item details in table
    await update.message.reply_photo(
        item_details.img_path,
        caption=f"Item Name: {item_details.item_name}\nItem Stock: {item_details.item_quantity}\n\n{item_details.item_description}",
    )
    await update.message.reply_text(
        f"How many of '{item_selected}' do you want to loan out?"
    )
    return LOAN_STATE


async def loan_order_conf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data

    # LR validation
    if "temp_lr" not in user_data.keys():
        usr_role = get_user_role(update.effective_chat.id)
        user_data["role"] = get_user_role(usr_role)
        await update.effective_chat.send_message(
            f"Invalid operation performed. Returning to start."
        )
        await update.effective_chat.send_message(
            f"Welcome back {update.effective_chat.username}! What would you like to do today?",
            reply_markup=show_keyboard_start(update.effective_chat.id, usr_role),
        )
        return ACTION_START
    elif "temp_lr" in user_data.keys():
        lr_dict = dict(user_data["temp_lr"])
        if "cat_name" not in lr_dict.keys():
            await update.message.reply_text(
                f"Please select a category.", reply_markup=show_keyboard_cat()
            )
            return LOAN_STATE
        elif "item_name" not in lr_dict.keys():
            selected_cat = lr_dict["cat_name"]
            await update.message.reply_text(
                f"Please select an item in {selected_cat}",
                reply_markup=show_keyboard_items(selected_cat),
            )
            return LOAN_STATE

    # loan request confirmation
    quant_selected = update.message.text
    # quant input validation
    item_quant = get_item_details(user_data["temp_lr"]["item_id"]).item_quantity
    if int(quant_selected) > int(item_quant) or int(quant_selected) == 0:
        await update.message.reply_text(
            f"You selected an invalid quantity.\nCurrent stock is '{item_quant}', you requested '{quant_selected}'.\nPlease reselect a quantity. "
        )
        return None
    # update lr
    temp_lr = dict(context.user_data["temp_lr"])
    temp_lr["item_quantity"] = int(quant_selected)
    context.user_data["temp_lr"] = temp_lr
    # Show current loan request
    selected_lr = context.user_data["temp_lr"]
    await update.message.reply_text(
        f"<pre>Loan Request Details\n--------------\nItem Name: {selected_lr['item_name']}\nItem Category: {selected_lr['cat_name']}\nItem Quantity: {selected_lr['item_quantity']}\n--------------\n</pre>",
        parse_mode=ParseMode.HTML,
    )
    await update.message.reply_text(
        f"What would you like to do?",
        reply_markup=show_keyboard_conf_loan(),
    )
    # Display existing order
    if len(context.user_data["order"].keys()) != 0:
        existing_order = dict(context.user_data["order"])
        order_df = pd.DataFrame.from_dict(existing_order).T
        fig_id = str(uuid.uuid4())
        fig = ff.create_table(order_df)
        fig.update_layout(autosize=True)
        fig.write_image(f"./database/data/images/df_images/{fig_id}.png", scale=2)
        await update.message.reply_photo(
            f"./database/data/images/df_images/{fig_id}.png", caption="Existing Order"
        )
    return LOAN_STATE


async def loan_conf_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    user_data = context.user_data

    # Check if all fields are valid for lr if exists
    if "temp_lr" in user_data.keys():
        temp_lr = user_data["temp_lr"]
        if "item_quantity" not in temp_lr.keys():
            await update.message.reply_text(
                f"How much of {temp_lr['item_name']} under category {temp_lr['cat_name']} do you want to request?"
            )
            return LOAN_STATE

    # Database intake and handling prompt reply
    reply_markup = show_keyboard_start(
        update.effective_chat.id, context.user_data["role"]
    )
    loan_conf_reply = update.message.text
    # Route for confirming an order
    if loan_conf_reply.lower() == "confirm order":
        # Save current LR and del LR placeholder, Only if LR is awaiting to be added to order
        existing_order = dict(context.user_data["order"])
        if "temp_lr" in user_data.keys():
            selected_lr = user_data["temp_lr"]
            del user_data["temp_lr"]
            loan_id = str(uuid.uuid4())[:16]
            # Check if the LR being put in already exists in order
            if len(existing_order) != 0:
                eo_df = pd.DataFrame.from_dict(existing_order).T
                cat_item_pd_filter = (eo_df["cat_name"] == selected_lr["cat_name"]) & (
                    eo_df["item_name"] == selected_lr["item_name"]
                )
                if not eo_df.loc[cat_item_pd_filter].empty:
                    await update.message.reply_text(
                        f"A loan request for '{selected_lr['item_name']}' is already in the order.\n Overwriting old LR with new one."
                    )
                    eo_df.loc[cat_item_pd_filter, "item_quantity"] = selected_lr[
                        "item_quantity"
                    ]
                    existing_order = eo_df.T.to_dict()
                else:
                    existing_order[loan_id] = selected_lr
                context.user_data["order"] = existing_order
            else:
                # Update existing order
                existing_order[loan_id] = selected_lr
                context.user_data["order"] = existing_order

        # Order is empty , possible case if user places LR and then cancels LR
        if len(user_data["order"].keys()) == 0:
            await update.message.reply_text(
                f"Your order cannot be confirmed because it is empty. Please request an item.",
                reply_markup=show_keyboard_conf_loan(),
            )
            return None

        # Instantiate order df for database intake
        order_df = pd.DataFrame.from_dict(existing_order).T
        order_df_abrv = order_df.copy()
        order_df["item_id"] = order_df.apply(
            lambda x: get_item_id(x["cat_name"], x["item_name"]), axis=1
        )

        order_df["order_id"] = context.user_data["order_id"]
        order_df.index.names = ["loan_id"]
        order_df = order_df.reset_index()
        order_df["telegram_id"] = update.effective_chat.id
        order_df["loan_status"] = "PENDING"
        order_df["approved_by"] = None
        order_df["approved_datetime"] = None
        # database intake
        intake_df = order_df.copy()
        intake_df.pop("cat_name")
        intake_df.pop("item_name")
        load_df_into_db(intake_df, c, "loan")
        set_order(
            context.user_data["order_id"], update.effective_chat.id, datetime.now()
        )
        # Show Completed Order
        fig_id = str(uuid.uuid4())
        fig = ff.create_table(order_df_abrv)
        fig.update_layout(autosize=True)
        fig.write_image(f"./database/data/images/df_images/{fig_id}.png", scale=2)
        await update.message.reply_photo(
            f"./database/data/images/df_images/{fig_id}.png",
            caption=f"Completed order submission. Here is a complete overview of your entire order.",
        )
        # Notify admins of order placed
        order_datetime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        notify_admins = get_admin_ids()
        for admin in notify_admins:
            if str(admin) == str(update.effective_chat.id):
                continue
            else:
                await context.bot.send_message(
                    chat_id=admin,
                    text=f"INFO: {update.effective_chat.username} has just placed in an order with order id {context.user_data['order_id']}",
                )
        # Completion message
        await update.message.reply_text(
            f"You placed an order with order id {context.user_data['order_id']}!\n What would you like to do next?",
            reply_markup=reply_markup,
        )
        user_data.clear()
        user_data["role"] = get_user_role(update.effective_chat.id)
        return ACTION_START

    # Route for cancelling the entire order
    elif loan_conf_reply.lower() == "cancel order":
        user_data.clear()
        user_data["role"] = get_user_role(update.effective_chat.id)
        await update.message.reply_text(
            "You cancelled the order.", reply_markup=reply_markup
        )
        return ACTION_START

    # Route for cancelling loan request
    elif loan_conf_reply.lower() == "cancel loan request":
        # Del current LR placeholder but retain order id
        if "temp_lr" in user_data.keys():
            del user_data["temp_lr"]

        await update.message.reply_text(
            f"Cancelled current loan request. What would you like to do?",
            reply_markup=show_keyboard_conf_loan(),
        )
        return None

    # Route request another item
    elif loan_conf_reply.lower() == "request another item":
        if "temp_lr" in user_data.keys():
            selected_lr = user_data["temp_lr"]
            del user_data["temp_lr"]
            loan_id = str(uuid.uuid4())
            existing_order = dict(context.user_data["order"])
            # Check if the LR being put in already exists in order
            if len(existing_order) != 0:
                eo_df = pd.DataFrame.from_dict(existing_order).T
                cat_item_pd_filter = (eo_df["cat_name"] == selected_lr["cat_name"]) & (
                    eo_df["item_name"] == selected_lr["item_name"]
                )
                if not eo_df.loc[cat_item_pd_filter].empty:
                    await update.message.reply_text(
                        f"A loan request for '{selected_lr['item_name']}' is already in the order.\n Overwriting old LR with new one."
                    )
                    eo_df.loc[cat_item_pd_filter, "item_quantity"] = selected_lr[
                        "item_quantity"
                    ]
                    existing_order = eo_df.T.to_dict()
                else:
                    existing_order[loan_id] = selected_lr
                context.user_data["order"] = existing_order
            else:
                # Update existing order
                existing_order[loan_id] = selected_lr
                context.user_data["order"] = existing_order

        # Show updated Order

        existing_order = dict(context.user_data["order"])
        if len(existing_order.keys()) != 0:
            order_df = pd.DataFrame.from_dict(existing_order).T
            fig_id = str(uuid.uuid4())
            fig = ff.create_table(order_df)
            fig.update_layout(autosize=True)
            fig.write_image(f"./database/data/images/df_images/{fig_id}.png", scale=2)
            await update.message.reply_photo(
                f"./database/data/images/df_images/{fig_id}.png",
                caption=f"Pending loan request is added to order.\nInitiating new loan request.",
            )
        # Initiated new LR
        await update.message.reply_text(
            f"What category is the item?", reply_markup=show_keyboard_cat()
        )
        return LOAN_STATE
