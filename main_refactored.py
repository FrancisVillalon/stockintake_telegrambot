import logging
import tomllib

import pandas as pd
from telegram.ext import (ApplicationBuilder, CommandHandler,
                          ConversationHandler, MessageHandler, filters)

from bot_conversations.bot_laundry import *
from bot_conversations.bot_loan import *
from bot_conversations.bot_misc import *
from bot_conversations.bot_register import *
from bot_conversations.bot_start import *
from methods.filter_methods import *


# Main bot function
def main():
    # METHODS AND VARS
    with open("./config.toml", "rb") as f:
        data = tomllib.load(f)
        tele_key = data["test_telegram_bot"]["api_key"]
    # Basic logger to see debug errors
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)

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
                MessageHandler(
                    filters.TEXT & filters.Regex("^Laundry$") & ~(filters.COMMAND),
                    laundry_start,
                ),
            ],
            LAUN_STATE: [
                MessageHandler(
                    filters.TEXT
                    & ~(filters.COMMAND)
                    & filters.Regex("^Confirm|Cancel|[\+\-]*\d+$"),
                    laun_update,
                ),
                MessageHandler(
                    filters.TEXT
                    & ~(filters.COMMAND)
                    & filters.Regex("^Complete Laundry Update|Do Not Update$"),
                    laun_conf,
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
                    filter_category_only & ~(filters.COMMAND),
                    loan_item_select,
                ),
                MessageHandler(
                    ~(filters.Regex("^\d+$"))
                    & ~(filters.COMMAND)
                    & filter_not_conf
                    & filter_item_only,
                    loan_quant_select,
                ),
                MessageHandler(
                    filters.Regex("^\d+$") & ~(filters.COMMAND), loan_order_conf
                ),
                MessageHandler(
                    filter_is_conf & ~(filters.COMMAND) & ~filters.Regex("^\d+$"),
                    loan_conf_reply,
                ),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(
        CommandHandler("bba20041", initadmin)
    )  # Testing admin functions
    application.run_polling()


# Run
if __name__ == "__main__":
    main()
    db.kill_all_sessions()
    c.dispose()
