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
from methods.data_methods import *
from database.db_models import *

# METHODS AND VARS
with open("./config.toml", "rb") as f:
    data = tomllib.load(f)
    tele_key = data["telegram_bot"]["api_key"]
# Basic logger to see debug errors
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Menu states
AWAITING_REPLY, RECEIVED_REPLY, LOAN_STATE = range(3)


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
            usr_role = get_user_role(update.effective_chat.id)
            if usr_role:
                context.user_data["role"] = usr_role
                reply_markup = show_keyboard_start(update.effective_chat.id, usr_role)
            await update.effective_chat.send_message(
                f"Welcome back {update.effective_chat.username}! What would you like to do today?",
                reply_markup=reply_markup,
            )
            return AWAITING_REPLY
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


# action methods
async def loan_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["choice"] = text
    context.user_data["orders"] = {}
    await update.message.reply_text(f"What is the category of the item?")
    return LOAN_STATE


async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data["role"] != "admin":
        await update.message.reply_text(f"You are not authorized.")
        return AWAITING_REPLY
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"Who do you want to register?")
    return RECEIVED_REPLY


# Terminus
async def user_received_info(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> "Terminus":
    reply_markup = show_keyboard_start(
        update.effective_chat.id, context.user_data["role"]
    )
    user_data = context.user_data
    chosen_action = user_data["choice"]
    if chosen_action.lower() == "register":
        applicant = update.message.text
        match verify_applicant(applicant):
            case 1:
                user_chatid = get_user_id(applicant)
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
                    f"We cannot find an applicant with username {applicant}.",
                    reply_markup=reply_markup,
                )
    if chosen_action.lower() == "loan":
        await update.effective_chat.send_message(
            f"You have completed a loan action", reply_markup=reply_markup
        )
    del user_data["choice"]
    return AWAITING_REPLY


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
    return AWAITING_REPLY


# Main bot function
def main() -> "Start Bot":
    application = ApplicationBuilder().token(tele_key).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("initadmin", initadmin),
        ],
        states={
            AWAITING_REPLY: [
                MessageHandler(
                    filters.TEXT & filters.Regex("^Register$") & ~(filters.COMMAND),
                    register_user,
                ),
                MessageHandler(
                    filters.TEXT & filters.Regex("^Loan$") & ~(filters.COMMAND),
                    loan_start,
                ),
            ],
            RECEIVED_REPLY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND),
                    user_received_info,
                )
            ],
            # LOAN_STATE: [
            #     MessageHandler(filters.TEXT),
            #     MessageHandler(),
            #     MessageHandler(),
            # ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("initadmin", initadmin))
    application.run_polling()


# Run
if __name__ == "__main__":

    # Loading in initial data for database
    db.recreate_database(c)
    DATADIR = "./database/data/spreadsheets/"
    load_in_db(os.path.join(DATADIR, "data_stock.xlsx"), c, "stock")
    load_in_db(os.path.join(DATADIR, "data_categories.xlsx"), c, "category")

    main()
    print(get_cat_list())
    print(get_item_list("cat1"))
    db.kill_all_sessions()
    c.dispose()
