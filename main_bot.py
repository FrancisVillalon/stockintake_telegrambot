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
from methods.acl_methods import *
from methods.rkey_methods import *
from database.db_models import *

# METHODS AND VARS
with open("./config.toml", "rb") as f:
    data = tomllib.load(f)
    tele_key = data["telegram_bot"]["api_key"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

AWAITING_REPLY, RECEIVED_REPLY = range(2)
# LOAN_CATEGORY, LOAN_ITEM, LOAN_AMOUNT = range(3)


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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match register_applicant(update.effective_chat.id, update.effective_chat.username):
        case 0:
            usr_role = get_user_role(update.effective_chat.id)
            if usr_role:
                context.user_data["role"] = usr_role
                reply_markup = show_keyboard(update.effective_chat.id, usr_role)
            await update.effective_chat.send_message(
                f"Welcome back {update.effective_chat.username}! What would you like to do today?",
                reply_markup=reply_markup,
            )
            return AWAITING_REPLY
        case 1:
            await update.effective_chat.send_message(
                f"""
Hello {update.effective_chat.username}! Welcome to Stock Intake Bot (Prototype)!
You have been registered as an applicant and your application is awaiting approval from admins.
"""
            )
        case -1:
            await update.effective_chat.send_message(
                f"Hello {update.effective_chat.username}! Your application is still awaiting approval!"
            )
        case -2:
            await update.effective_chat.send_message(
                f"You are required to set a telegram username before being able to use this bot."
            )
        case -3:
            await update.effective_chat.send_message(
                f"Unexpected error occured. Please try again later."
            )


# Conversation bot methods


async def loan_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"You have chosen to loan an item.")
    return RECEIVED_REPLY


async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data["role"] != "admin":
        await update.message.reply_text(f"You are not authorized.")
        return AWAITING_REPLY
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"Who do you want to register?")
    return RECEIVED_REPLY


async def user_received_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = show_keyboard(update.effective_chat.id, context.user_data["role"])
    user_data = context.user_data
    chosen_action = user_data["choice"]
    if chosen_action.lower() == "register":
        applicant = update.message.text
        match verify_applicant(applicant):
            case 1:
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
                    f"We cannot find an applicant with username {applicant}.",
                    reply_markup=reply_markup,
                )
    if chosen_action.lower() == "loan":
        await update.effective_chat.sened_message(f"You have completed a loan action")
    del user_data["choice"]
    return AWAITING_REPLY


# PURELY FOR TESTING
async def initadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = db_conn()
    s = db_conn().create_session()
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
    await update.effective_chat.send_message(
        "Registered as Admin. Remove this later.",
        reply_markup=show_keyboard(update.effective_chat.id, "admin"),
    )
    return RECEIVED_REPLY


def main() -> "Start Bot":
    application = ApplicationBuilder().token(tele_key).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AWAITING_REPLY: [
                MessageHandler(
                    filters.TEXT & filters.Regex("^Register$") & ~(filters.COMMAND),
                    register_user,
                ),
                MessageHandler(
                    filters.TEXT & filters.Regex("^Loan$") & ~(filters.COMMAND),
                    loan_item,
                ),
            ],
            RECEIVED_REPLY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND),
                    user_received_info,
                )
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("initadmin", initadmin))
    application.run_polling()


if __name__ == "__main__":
    db_conn().recreate_database()
    main()
