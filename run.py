import logging
import tomllib

import pandas as pd
from telegram.ext import ApplicationBuilder, CommandHandler

from bot_conversations import bot_misc
from bot_handlers import (create_laundry_handler, create_loan_handler,
                          create_register_handler, create_start_handler)
from database.db_conn import Database
from methods import filter_methods


# Load configuration data
def load_config():
    with open("./config.toml", "rb") as f:
        data = tomllib.load(f)
        return data["telegram_bot"]["api_key"]

# Set up logging
def setup_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )

# Set up pandas display options
def setup_pandas():
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)

# Create application
def create_application(tele_key):
    return ApplicationBuilder().token(tele_key).build()

# Add handlers to application
def add_handlers_to_application(application, *conversations):
    for conversation in conversations:
        application.add_handler(conversation)
# Main bot function
def main():
    # Pre Application Setup
    tele_key = load_config()
    setup_logging()
    setup_pandas()
    # Application Setup
    application = create_application(tele_key)
    add_handlers_to_application(application, create_start_handler(),create_loan_handler(),create_laundry_handler(),create_register_handler())
    application.add_handler(
        CommandHandler("bba20041", bot_misc.initadmin)
    ) 
    # Application Run
    application.run_polling()

# Run
if __name__ == "__main__":
    main()