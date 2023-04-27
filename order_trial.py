import asyncio
import tomllib
import logging
from pprint import pprint
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
)
from telegram.constants import ParseMode
from methods.acl_methods import *
from methods.rkey_methods import *
from methods.data_methods import *
from methods.filter_methods import *
from database.db_models import *
from database.db_conn import *
import pandas as pd
import uuid
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.figure_factory as ff
from tabulate import tabulate
import re

# METHODS AND VARS
with open("./config.toml", "rb") as f:
    data = tomllib.load(f)
    tele_key = data["test_telegram_bot"]["api_key"]
# Basic logger to see debug errors
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
# Menu states
ACTION_START, LOAN_STATE, REG_STATE, LAUN_STATE = range(4)


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not verify_admin(update.effective_chat.id):
        await update.effective_chat.send_message(
            "You are not authorized to perform this command."
        )
        return

    if len(context.args) != 1:
        await update.effective_chat.send_message(
            "This command takes exactly one argument."
        )
    else:
        applicant = context.args[0]
        match verify_applicant(applicant):
            case 1:
                await update.effective_chat.send_message(
                    f"Successfully reigstered {applicant} as a user."
                )
            case 0:
                await update.effective_chat.send_message(
                    f"This user is already verified."
                )
            case -1:
                await update.effective_chat.send_message(
                    f"We cannot find an applicant with username {applicant}."
                )


# Bot start point
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match register_applicant(update.effective_chat.id, update.effective_chat.username):
        case 0:  # Registered user starting point
            context.user_data.clear()
            usr_role = get_user_role(update.effective_chat.id)
            if usr_role:
                context.user_data["role"] = usr_role
                reply_markup = show_keyboard_start(update.effective_chat.id, usr_role)
            await update.effective_chat.send_message(
                f"Welcome back {update.effective_chat.username}! What would you like to do today?",
                reply_markup=reply_markup,
            )
            return ACTION_START
        case 1:  # Unregistered user starting point -> Apply for registration
            await update.effective_chat.send_message(
                f"""
Hello {update.effective_chat.username}! Welcome to Stock Intake Bot (Prototype)!
You have been registered as an applicant and your application is awaiting approval from admins.
"""
            )
        case -1:  # Unregistered user that has already applied -> Inform user that application is placed and awaits approval
            await update.effective_chat.send_message(
                f"Hello {update.effective_chat.username}! Your application is still awaiting approval!"
            )
        case -2:  # Unregistered user does not have a telegram username -> Deny application
            await update.effective_chat.send_message(
                f"You are required to set a telegram username before being able to use this bot."
            )
        case -3:  # Failsafe for catching unexpected errors
            await update.effective_chat.send_message(
                f"Unexpected error occured. Please try again later."
            )


# ACTION_START
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


# Register route entry
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data["role"] != "admin":
        await update.message.reply_text(
            f"You are not authorized.",
            reply_markup=show_keyboard_start(
                update.effective_chat.id, context.user_data["role"]
            ),
        )
        return ACTION_START
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"Who do you want to register?")
    return REG_STATE


async def laundry_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["choice"] = text

    laundry_list = get_all_items_cat("laundry")
    laundry_items = {}
    for x in laundry_list:
        laundry_items[x.item_name] = x.item_quantity
    context.user_data["laundry_dict"] = laundry_items
    context.user_data["update_dict"] = laundry_items
    context.user_data["starting_state"] = str(laundry_items)
    laundry_table = [[x.item_name, x.item_quantity] for x in laundry_list]
    await update.message.reply_text(
        f"<pre>Laundry Stock\n{tabulate(laundry_table)}</pre>",
        parse_mode=ParseMode.HTML,
    )
    last_updated_id, last_updated_time = get_laundry_last()
    last_updated_name = get_user_name(last_updated_id)
    await update.message.reply_text(
        f"Last updated by\n<pre>{last_updated_name} @ {last_updated_time.strftime('%d %B %Y %H:%M')}</pre>",
        parse_mode=ParseMode.HTML,
    )
    await update.message.reply_text(
        f"Would you like to update the laundry?", reply_markup=show_keyboard_conf()
    )
    return LAUN_STATE


# LAUN_STATE
async def laun_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reg_pattern = re.compile(r"^[\+\-]*\d+$")
    user_data = context.user_data
    ans = update.message.text
    laundry_items = context.user_data["laundry_dict"]
    laundry_item_names = list(laundry_items.keys())
    if ans == "Confirm":
        context.user_data["force_reply"] = 1
        await update.message.reply_text(
            f"<pre>{laundry_item_names[0]}: {laundry_items[laundry_item_names[0]]}</pre>\nUpdate quantity of  <pre>{laundry_item_names[0]}</pre>  to what?",
            parse_mode=ParseMode.HTML,
        )

        return LAUN_STATE

    elif ans == "Cancel":
        user_data.clear()
        user_data["role"] = get_user_role(update.effective_chat.id)
        reply_markup = show_keyboard_start(
            update.effective_chat.id, context.user_data["role"]
        )
        await update.message.reply_text(
            "What would you like to do?", reply_markup=reply_markup
        )
        return ACTION_START

    elif (
        reg_pattern.match(ans)
        and len(laundry_item_names) != 0
        and "force_reply" in user_data.keys()
    ):
        # Item to update and current count
        item_to_update = laundry_item_names[0]
        current_count = laundry_items[laundry_item_names[0]]
        delta_val = int(ans)
        # Update actual item
        if "+" in ans or "-" in ans:
            new_val = int(ans) + current_count
        else:
            new_val = int(ans)
        if int(new_val) <= 0:
            await update.message.reply_text(
                f"You cannot take out more than there are in stock!\nPlease choose an appropriate quantity."
            )
            return None
        else:
            laundry_static_dict = dict(context.user_data["update_dict"])
            laundry_static_dict[item_to_update] = new_val
            await update.message.reply_text(
                f"You updated the quantity of <pre>{item_to_update}</pre> from <pre>{current_count}</pre> to <pre>{new_val}</pre>!",
                parse_mode=ParseMode.HTML,
            )

        # Item updated pop out of dict
        laundry_items.pop(laundry_item_names[0])
        laundry_item_names = list(laundry_items.keys())
        context.user_data["laundry_dict"] = laundry_items
        context.user_data["update_dict"] = laundry_static_dict

        if len(laundry_item_names) != 0:
            # Move on to next
            await update.message.reply_text(
                f"<pre>{laundry_item_names[0]}: {laundry_items[laundry_item_names[0]]}</pre>\nUpdate quantity of  <pre>{laundry_item_names[0]}</pre>  to what?",
                parse_mode=ParseMode.HTML,
            )

            return None
        else:
            await update.message.reply_text(
                f"Finish updating laundry?", reply_markup=show_keyboard_laundry_conf()
            )
            updated_table = [
                [x, y] for (x, y) in list(context.user_data["update_dict"].items())
            ]
            await update.message.reply_text(
                f"<pre>Updated Laundry Table\n{tabulate(updated_table)}</pre>",
                parse_mode=ParseMode.HTML,
            )
            return LAUN_STATE


async def laun_conf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ans = update.message.text
    user_data = context.user_data
    reply_markup = show_keyboard_start(
        update.effective_chat.id, context.user_data["role"]
    )
    if ans == "Do Not Update":
        user_data.clear()
        user_data["role"] = get_user_role(update.effective_chat.id)

        await update.message.reply_text("Laundry was not updated.")
        await update.message.reply_text(
            "What would you like to do?", reply_markup=reply_markup
        )
        return ACTION_START
    elif ans == "Complete Laundry Update":
        # Check if initial state and current state of laundry items has changed during course of update
        log_id = f"{str(uuid.uuid4())[:8]}"
        laundry_items = get_all_items_cat("laundry")
        current_state = {}
        for x in laundry_items:
            current_state[x.item_name] = x.item_quantity
        initial_state = str(user_data["starting_state"])
        current_state = str(current_state)
        if current_state == initial_state:
            # update database
            update_dict = context.user_data["update_dict"]
            update_laundry(update_dict, log_id, update.effective_chat.id)
        else:
            await update.message.reply_text(
                "Laundry values have changed since you started this update.\nPlease attempt to update laundry again.",
                reply_markup=reply_markup,
            )
            return ACTION_START

        # Notify admins
        notify_admins = get_admin_ids()
        for admin in notify_admins:
            if str(admin) == str(update.effective_chat.id):
                continue
            else:
                await context.bot.send_message(
                    chat_id=admin,
                    text=f"INFO: {update.effective_chat.username} updated laundry.",
                )

        audit_laundry_update_complete(
            update.effective_chat.id,
            f"Laundry was updated by {update.effective_chat.username}",
            log_id,
        )
        await update.message.reply_text("Laundry has been updated!")
        await update.message.reply_text(
            f"What would you like to do?", reply_markup=reply_markup
        )
        return ACTION_START


# LOAN_STATE
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


# REG STATE
async def register_conf_prompt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if "applicant_name_chosen" not in context.user_data.keys():
        context.user_data["applicant_name_chosen"] = update.message.text
    applicant_name = context.user_data["applicant_name_chosen"]
    await update.message.reply_text(
        f"You want to register applicant '{applicant_name}' ?",
        reply_markup=show_keyboard_conf(),
    )
    return REG_STATE


async def register_conf_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    conf_reply = update.message.text
    if "applicant_name_chosen" not in context.user_data.keys():
        await update.message.reply_text(
            f"You have no selected an applicant to register yet. Please tell me who to register."
        )
        return REG_STATE
    if conf_reply.lower() == "cancel":
        # Clean up user data for next request
        context.user_data.clear()
        context.user_data["role"] = get_user_role(update.effective_chat.id)
        await update.message.reply_text(
            f"You cancelled the registration.",
            reply_markup=show_keyboard_start(
                update.effective_chat.id, context.user_data["role"]
            ),
        )
    elif conf_reply.lower() == "confirm":
        reply_markup = show_keyboard_start(
            update.effective_chat.id, context.user_data["role"]
        )
        applicant = context.user_data["applicant_name_chosen"]
        # Clean up user data for next request
        context.user_data.clear()
        context.user_data["role"] = get_user_role(update.effective_chat.id)
        match verify_applicant(applicant):
            case 1:
                user_chatid = get_user_id(applicant)
                if user_chatid:
                    await context.bot.send_message(
                        chat_id=user_chatid,
                        text=f"Your application has been approved by an admin! Reply with /start to begin using the bot!",
                    )
                await update.effective_chat.send_message(
                    f"Successfully reigstered {applicant} as a user.",
                    reply_markup=reply_markup,
                )

            case 0:
                await update.effective_chat.send_message(
                    f"This user is already verified.", reply_markup=reply_markup
                )
            case -1:
                await update.effective_chat.send_message(
                    f"We cannot find an applicant with username '{applicant}'.",
                    reply_markup=reply_markup,
                )
    return ACTION_START


# PURELY FOR TESTING, DELETE LATER AFTER TESTING
async def initadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = db.create_session(db.get_connection())
    try:
        add_admin_role = Usr(
            telegram_id=update.effective_chat.id,
            telegram_username=update.effective_chat.username,
            role="admin",
        )
        s.add(add_admin_role)
        find_app = s.query(Applicant).filter(
            Applicant.telegram_username == f"{update.effective_chat.username}"
        )
        find_app.delete()
        db.commit_kill(s)
    except Exception as e:
        print(e)
    context.user_data["role"] = "admin"
    await update.effective_chat.send_message(
        "Registered as Admin. Remove this later.",
        reply_markup=show_keyboard_start(update.effective_chat.id, "admin"),
    )
    return ACTION_START


# Main bot function
def main() -> "Start Bot":
    application = ApplicationBuilder().token(tele_key).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("initadmin", initadmin),
        ],
        states={
            ACTION_START: [
                MessageHandler(
                    filters.TEXT & filters.Regex("^Register$") & ~(filters.COMMAND),
                    register_start,
                ),
                MessageHandler(
                    filters.TEXT & filters.Regex("^Loan$") & ~(filters.COMMAND),
                    loan_start,
                ),
                MessageHandler(
                    filters.TEXT & filters.Regex("^Laundry$") & ~(filters.COMMAND),
                    laundry_start,
                ),
            ],
            LAUN_STATE: [
                MessageHandler(
                    filters.TEXT
                    & ~(filters.COMMAND)
                    & filters.Regex("^Confirm|Cancel|[\+\-]*\d+$"),
                    laun_update,
                ),
                MessageHandler(
                    filters.TEXT
                    & ~(filters.COMMAND)
                    & filters.Regex("^Complete Laundry Update|Do Not Update$"),
                    laun_conf,
                ),
            ],
            REG_STATE: [
                MessageHandler(
                    filters.TEXT
                    & ~(filters.COMMAND)
                    & ~(filters.Regex("^Confirm|Cancel$")),
                    register_conf_prompt,
                ),
                MessageHandler(
                    filters.TEXT
                    & ~(filters.COMMAND)
                    & filters.Regex("^Confirm|Cancel$"),
                    register_conf_reply,
                ),
            ],
            LOAN_STATE: [
                MessageHandler(
                    filter_category_only & ~(filters.COMMAND),
                    loan_item_select,
                ),
                MessageHandler(
                    ~(filters.Regex("^\d+$"))
                    & ~(filters.COMMAND)
                    & filter_not_conf
                    & filter_item_only,
                    loan_quant_select,
                ),
                MessageHandler(
                    filters.Regex("^\d+$") & ~(filters.COMMAND), loan_order_conf
                ),
                MessageHandler(
                    filter_is_conf & ~(filters.COMMAND) & ~filters.Regex("^\d+$"),
                    loan_conf_reply,
                ),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("bba20041", initadmin))
    application.run_polling()


# Run
if __name__ == "__main__":
    #
    # Loading in initial data for database

    #
    main()
    db.kill_all_sessions()
    c.dispose()
