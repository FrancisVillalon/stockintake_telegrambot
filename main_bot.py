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
from methods.filter_methods import *
from database.db_models import *
import pandas as pd
import uuid

# METHODS AND VARS
with open("./config.toml", "rb") as f:
    data = tomllib.load(f)
    tele_key = data["telegram_bot"]["api_key"]
# Basic logger to see debug errors
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Menu states
ACTION_START, LOAN_STATE, REG_STATE = range(3)


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
async def loan_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["choice"] = text
    context.user_data["orders"] = {}
    context.user_data["temp_order"] = {"order_id": str(uuid.uuid4())}
    await update.message.reply_text(
        f"What is the category of the item?", reply_markup=show_keyboard_cat()
    )
    return LOAN_STATE


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


# LOAN_STATE


async def loan_item_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cat_name = update.message.text
    temp_order = dict(context.user_data["temp_order"])
    temp_order["cat_name"] = cat_name
    context.user_data["temp_order"] = temp_order
    await update.message.reply_text(
        f"What item in {cat_name}?", reply_markup=show_keyboard_items(cat_name)
    ),
    return LOAN_STATE


async def loan_quant_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    item_selected = update.message.text
    temp_order = dict(context.user_data["temp_order"])
    temp_order["item_name"] = item_selected
    context.user_data["temp_order"] = temp_order
    await update.message.reply_text(
        f"How many of '{item_selected}' do you want to loan out?"
    )
    return LOAN_STATE


async def loan_order_conf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    quant_selected = update.message.text
    temp_order = dict(context.user_data["temp_order"])
    temp_order["item_quantity"] = int(quant_selected)
    context.user_data["temp_order"] = temp_order
    order_df = pd.DataFrame.from_dict(dict(context.user_data["temp_order"], index=[0]))
    order_df = order_df.set_index("order_id")
    order_df.pop("index")
    print(order_df)
    await update.message.reply_text(
        f"Is this all you would like to request?",
        reply_markup=show_keyboard_conf_loan(),
    )
    return LOAN_STATE


async def loan_conf_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = show_keyboard_start(
        update.effective_chat.id, context.user_data["role"]
    )
    loan_conf_reply = update.message.text
    if loan_conf_reply.lower() == "confirm":
        await update.message.reply_text(
            "Completed loan test route.", reply_markup=reply_markup
        )

    elif loan_conf_reply.lower() == "cancel":
        await update.message.reply_text(
            "You cancelled the loan order.", reply_markup=reply_markup
        )

    elif loan_conf_reply.lower() == "request another item":
        pass
    return ACTION_START


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
                    filter_category_only & ~(filters.COMMAND) & filters.TEXT,
                    loan_item_select,
                ),
                MessageHandler(
                    filters.TEXT
                    & ~(filters.Regex("^\d+$"))
                    & ~(filters.COMMAND)
                    & filter_not_conf,
                    loan_quant_select,
                ),
                MessageHandler(
                    filters.Regex("^\d+$") & ~(filters.COMMAND), loan_order_conf
                ),
                MessageHandler(
                    filters.TEXT
                    & filters.Regex("^Confirm|Cancel|Request Another Item$")
                    & ~(filters.COMMAND),
                    loan_conf_reply,
                ),
            ],
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
    # db.recreate_database(c)
    # DATADIR = "./database/data/spreadsheets/"
    # load_in_db(os.path.join(DATADIR, "data_stock.xlsx"), c, "stock")
    # load_in_db(os.path.join(DATADIR, "data_categories.xlsx"), c, "category")

    main()
    db.kill_all_sessions()
    c.dispose()
