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
    if verify_admin(update.effective_chat.id):
        await update.effective_chat.send_message(f"Registered {context.args}")
    else:
        await update.effective_chat.send_message(
            "You are not authorized to use this command."
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if verify_user(update.effective_chat.id):
        await update.effective_chat.send_message(
            f"Welcome {update.message.chat.firstname}!"
        )
    else:
        await update.effective_chat.send_message("You are not registered.")


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
