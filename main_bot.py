import asyncio
import tomllib
import logging
from pprint import pprint
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters

with open("./config.toml", "rb") as f:
    data = tomllib.load(f)
    tele_key = data["telegram_bot"]["api_key"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="STOCK INTAKE BOT PROTOTYPE"
    )


def main() -> "Start Bot":
    application = ApplicationBuilder().token(tele_key).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
