import re

from tabulate import tabulate
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from methods.acl_methods import *
from methods.data_methods import *
from methods.rkey_methods import *

ACTION_START, LOAN_STATE, REG_STATE, LAUN_STATE = range(4)
# ACTION_START
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
    laundry_last = get_laundry_last()
    if laundry_last:
        last_updated_id, last_updated_time = (
            laundry_last.telegram_id,
            laundry_last.log_datetime,
        )
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
        if int(new_val) < 0:
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

