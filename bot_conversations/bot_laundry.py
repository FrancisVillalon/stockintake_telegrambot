"""
Handles laundry functions.
"""


import re
import uuid

from tabulate import tabulate
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from methods.acl_methods import get_admin_ids, get_user_name, get_user_role
from methods.audit_methods import audit_laundry_update_complete
from methods.data_methods import get_all_items_cat, get_laundry_last, update_laundry
from methods.rkey_methods import *

LAUN_UPDATE = 0
LAUN_CONF = 1
LAUN_CANCEL = 2

#! Add type hinting


# Handling premature exit of operation
async def laundry_premature_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_message(
        "Laundry update prematurely cancelled.",
        reply_markup=show_keyboard_start(
            update.effective_chat.id, context.user_data["role"]
        ),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def laundry_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Make user busy in this conversation and define role
    context.user_data["in_conversation"] = True
    context.user_data["role"] = get_user_role(update.effective_chat.id)

    laundry_list = get_all_items_cat("laundry")
    laundry_items = {}
    for x in laundry_list:
        laundry_items[x["item_name"]] = x["item_quantity"]
    context.user_data["laundry_dict"] = laundry_items
    context.user_data["update_dict"] = laundry_items
    context.user_data["starting_state"] = str(laundry_items)
    laundry_table = [
        [item_name, item_quantity] for item_name, item_quantity in laundry_items.items()
    ]
    await update.message.reply_text(
        f"<pre>Laundry Stock\n{tabulate(laundry_table)}</pre>",
        parse_mode=ParseMode.HTML,
    )
    laundry_last = get_laundry_last()
    if laundry_last:
        last_updated_id, last_updated_time = (
            laundry_last["telegram_id"],
            laundry_last["log_datetime"],
        )
        last_updated_name = get_user_name(last_updated_id)
        await update.message.reply_text(
            f"Last updated by\n<pre>{last_updated_name} @ {last_updated_time.strftime('%d %B %Y %H:%M')}</pre>",
            parse_mode=ParseMode.HTML,
        )
    await update.message.reply_text(
        f"Would you like to update the laundry?", reply_markup=show_keyboard_conf()
    )
    return LAUN_UPDATE


# LAUN_STATE
async def laun_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reg_pattern = re.compile(r"^[\+\-]*\d+$")
    user_data = context.user_data
    ans = update.message.text
    laundry_items = context.user_data["laundry_dict"]
    laundry_item_names = list(laundry_items.keys())

    # User has indicated that he wants to update the laundry
    if ans == "Confirm":
        context.user_data["force_reply"] = 1
        await update.message.reply_text(
            f"<pre>{laundry_item_names[0]}: {laundry_items[laundry_item_names[0]]}</pre>\nUpdate quantity of  <pre>{laundry_item_names[0]}</pre>  to what?",
            parse_mode=ParseMode.HTML,
        )
        return None
    # User cancelled
    elif ans == "Cancel":
        user_data.clear()
        user_data["role"] = get_user_role(update.effective_chat.id)
        reply_markup = show_keyboard_start(
            update.effective_chat.id, context.user_data["role"]
        )
        await update.message.reply_text(
            "Laundry update prematurely cancelled.", reply_markup=reply_markup
        )
        return ConversationHandler.END
    # User has already confirmed of intent to update, awaiting valid response for update
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
        if int(new_val) < 0:
            await update.message.reply_text(
                f"You cannot take out more than there are in stock!\nPlease choose an appropriate quantity."
            )
            return None
        else:
            laundry_static_dict = dict(context.user_data["update_dict"])
            laundry_static_dict[item_to_update] = new_val
            await update.message.reply_text(
                f"You updated the quantity of <pre>{item_to_update}</pre> from <pre>{current_count}</pre> to <pre>{new_val}</pre>",
                parse_mode=ParseMode.HTML,
            )

        # Item updated pop out of dict
        laundry_items.pop(laundry_item_names[0])
        laundry_item_names = list(laundry_items.keys())
        context.user_data["laundry_dict"] = laundry_items
        context.user_data["update_dict"] = laundry_static_dict

        # Check if all laundry items were updated
        if (
            len(laundry_item_names) != 0
        ):  # Not all items were updated yet, proceed to next item
            # Move on to next
            await update.message.reply_text(
                f"<pre>{laundry_item_names[0]}: {laundry_items[laundry_item_names[0]]}</pre>\nUpdate quantity of  <pre>{laundry_item_names[0]}</pre>  to what?",
                parse_mode=ParseMode.HTML,
            )

            return None
        else:  # All laundry items were updated. Ask user to confirm to commit changes
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
            return LAUN_CONF


async def laun_conf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ans = update.message.text
    user_data = context.user_data
    reply_markup = show_keyboard_start(
        update.effective_chat.id, get_user_role(update.effective_chat.id)
    )
    laundry_update_status = False
    if ans == "Do Not Update":
        user_data.clear()
        user_data["role"] = get_user_role(update.effective_chat.id)

        await update.message.reply_text("Laundry was not updated.")
        await update.message.reply_text(
            "What would you like to do?", reply_markup=reply_markup
        )
    elif ans == "Complete Laundry Update":
        # Check if initial state and current state of laundry items has changed during course of update
        log_id = f"{str(uuid.uuid4())[:8]}"
        laundry_items = get_all_items_cat("laundry")
        current_state = {}
        for x in laundry_items:
            current_state[x["item_name"]] = x["item_quantity"]
        initial_state = str(user_data["starting_state"])
        current_state = str(current_state)
        if current_state == initial_state:
            # update database
            update_dict = context.user_data["update_dict"]
            update_laundry(update_dict, log_id, update.effective_chat.id)
            laundry_update_status = True
        else:
            await update.message.reply_text(
                "Laundry values have changed since you started this update.\nPlease attempt to update laundry again using /start."
            )
            return ConversationHandler.END

        # Notify admins
        if laundry_update_status:
            notify_admins = get_admin_ids()
            for admin in notify_admins:
                if str(admin) == str(update.effective_chat.id):
                    await context.bot.send_message(
                        chat_id=admin,
                        text=f"INFO: A message has been sent to other admins that you have updated the laundry.",
                    )
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
        # Conversation over, update conversation status
        context.user_data.clear()
        await update.message.reply_text(f"/start to do something else!")
        return ConversationHandler.END
