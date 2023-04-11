from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import tomllib
import logging


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
with open("./config.toml", "rb") as f:
    data = tomllib.load(f)
    tele_key = data["telegram_bot"]["api_key"]

k1 = [["Loan", "Register"]]
k2 = [["Cat1", "Cat2", "Cat3"]]
c1_k = [["Item1", "Item2"]]
c2_k = [["Item3"]]
c3_k = [["Item5", "Item6", "Item7"]]
ca_k = [["confirm", "cancel"]]
ck_dict = {
    "Cat1": c1_k,
    "Cat2": c2_k,
    "Cat3": c3_k,
}

START_STATE, LOAN_STATE, END_STATE = range(3)

print(START_STATE, LOAN_STATE, END_STATE)


def show_keyboard(k):
    return ReplyKeyboardMarkup(k, one_time_keyboard=True, resize_keyboard=True)


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Trial test for capturing loan data.", reply_markup=show_keyboard(k1)
    )
    return START_STATE


# LOAN STATE
async def loan_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["choice"] = update.message.text
    await update.message.reply_text(
        f"What is the category of the item?", reply_markup=show_keyboard(k2)
    )
    return LOAN_STATE


async def item_cat_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    item_cat = update.message.text
    context.user_data["item_cat_selected"] = item_cat
    await update.message.reply_text(
        f"What item in {item_cat}?", reply_markup=show_keyboard(ck_dict[item_cat])
    )
    return LOAN_STATE


async def item_name_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data["item_cat_selected"]:
        item_name = update.message.text
        context.user_data["item_name_selected"] = item_name
        await update.message.reply_text(f"How many?")
        return LOAN_STATE
    else:
        await update.message.reply_text(
            f"Please select a category.", reply_markup=show_keyboard(k2)
        )
        return LOAN_STATE


async def loan_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data["item_cat_selected"]:
        await update.message.reply_text(
            f"Please select a category", reply_markup=show_keyboard(k2)
        )
        return LOAN_STATE
    elif not context.user_data["item_name_selected"]:
        item_cat = context.user_data["item_cat_selected"]
        await update.message.reply_text(
            f"Please select an item", reply_markup=show_keyboard(ck_dict[item_cat])
        )
        return LOAN_STATE
    else:
        item_quantity = update.message.text
        context.user_data["item_quantity_selected"] = item_quantity
        await update.message.reply_text(
            f"Are you sure?", reply_markup=show_keyboard(ca_k)
        )
        return END_STATE


# REGISTER STATE
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Are you sure?", reply_markup=show_keyboard(ca_k))
    return END_STATE


# TERMINUS
async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_confirmation = update.message.text
    if user_confirmation == "Confirm":
        user_data = context.user_data
        item_cat = user_data["item_cat_selected"]
        item_name = user_data["item_name_selected"]
        item_quantity = user_data["item_quantity_selected"]
        user_data.clear()
        await update.message.reply_text(
            f"LOAN(Item Category:{item_cat}, Item Name:{item_name}, Item Quantity:{item_quantity})",
            reply_markup=show_keyboard(k1),
        )
    elif user_confirmation == "Cancel":
        await update.message.reply_text(
            f"TRANSACTION_CANCELLED", reply_markup=show_keyboard(k1)
        )
    return START_STATE


def main() -> None:
    application = Application.builder().token(tele_key).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_STATE: [
                MessageHandler(
                    filters.TEXT & filters.Regex("^Loan$") & ~(filters.COMMAND),
                    loan_start,
                )
            ],
            LOAN_STATE: [
                MessageHandler(
                    filters.TEXT
                    & filters.Regex("^Cat1|Cat2|Cat3$")
                    & ~(filters.COMMAND),
                    item_cat_selected,
                ),
                MessageHandler(
                    filters.TEXT & ~(filters.Regex("^\d+")) & ~(filters.COMMAND),
                    item_name_selected,
                ),
                MessageHandler(filters.Regex("^\d+$") & ~(filters.COMMAND), loan_end),
            ],
            END_STATE: [
                MessageHandler(
                    filters.TEXT
                    & filters.Regex("^Confirm|Cancel$")
                    & ~(filters.COMMAND),
                    start_over,
                )
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("start", start))
    application.run_polling()


if __name__ == "__main__":
    main()
