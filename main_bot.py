import asyncio
import tomllib
import logging
from pprint import pprint
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters
from acl import *

with open("./config.toml", "rb") as f:
    data = tomllib.load(f)
    tele_key = data["telegram_bot"]["api_key"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


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
    match register_applicant(update.effective_chat.id, update.message.chat.username):
        case 0:
            await update.effective_chat.send_message(
                f"Welcome back {update.message.chat.username}! What would you like to do today?"
            )
        case 1:
            await update.effective_chat.send_message(
                f"""
Hello {update.message.chat.username}! Welcome to Stock Intake Bot (Prototype)!
You have been registered as an applicant and your application is awaiting approval from admins.
"""
            )
        case -1:
            await update.effective_chat.send_message(
                f"Hello {update.message.chat.username}! Your application is still awaiting approval!"
            )


# PURELY FOR TESTING
async def initadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(
        update.effective_chat.id,
        update.message.chat.username,
        "admin",
    )
    await update.effective_chat.send_message("Registered as Admin. Remove this later.")


def main() -> "Start Bot":
    application = ApplicationBuilder().token(tele_key).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("initadmin", initadmin))
    application.run_polling()


if __name__ == "__main__":
    db = db_conn()
    db.recreate_database()
    import time

    time.sleep(2)
    main()
