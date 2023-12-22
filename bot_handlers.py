from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters

from bot_conversations import bot_laundry, bot_loan, bot_register, bot_start
from methods import filter_methods


# Loan handler -> Admin & User ONLY
def create_loan_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.TEXT & filters.Regex("^Loan$") & ~(filters.COMMAND),
                bot_loan.loan_start,
            ),
        ],
        states={
            bot_loan.LOAN_CAT_SELECT: [
                MessageHandler(
                    filters.TEXT
                    & filter_methods.filter_category_only
                    & ~(filters.COMMAND),
                    bot_loan.loan_cat_select,
                ),
            ],
            bot_loan.LOAN_ITEM_SELECT: [
                MessageHandler(
                    ~(filters.Regex("^\d+$"))
                    & ~(filters.COMMAND)
                    & filter_methods.filter_not_conf
                    & filter_methods.filter_item_only,
                    bot_loan.loan_item_select,
                ),
            ],
            bot_loan.LOAN_QUANT_SELECT: [
                MessageHandler(
                    filter_methods.filter_not_conf & ~(filters.COMMAND),
                    bot_loan.loan_quant_select,
                )
            ],
            bot_loan.LOAN_REQUEST_CONF: [
                MessageHandler(
                    ~(filters.COMMAND) & (filters.Regex("^Confirm|Cancel$")),
                    bot_loan.loan_request_conf,
                ),
            ],
            bot_loan.LOAN_ORDER_CONF: [
                MessageHandler(
                    ~(filters.COMMAND),
                    callback=bot_loan.loan_order_conf,
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", bot_loan.loan_premature_cancel),
            CommandHandler("new_ordr", bot_loan.loan_start),
            CommandHandler("new_lr", bot_loan.loan_start),
        ],
    )


# Registration handler -> Admin ONLY
def create_register_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.TEXT & filters.Regex("^Register$") & ~(filters.COMMAND),
                bot_register.register_start,
            )
        ],
        states={
            bot_register.REG_CONF_PROMPT: [
                MessageHandler(
                    filters.TEXT
                    & ~(filters.COMMAND)
                    & ~(filters.Regex("^Confirm|Cancel$")),
                    bot_register.register_conf_prompt,
                ),
            ],
            bot_register.REG_TERMINUS: [
                MessageHandler(
                    filters.TEXT
                    & ~(filters.COMMAND)
                    & filters.Regex("^Confirm|Cancel$"),
                    bot_register.register_conf_reply,
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", bot_register.register_premature_cancel)],
    )


# Laundry handler -> Admin & User ONLY
def create_laundry_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.TEXT & filters.Regex("^Laundry$") & ~(filters.COMMAND),
                bot_laundry.laundry_start,
            )
        ],
        states={
            bot_laundry.LAUN_UPDATE: [
                MessageHandler(
                    filters.TEXT
                    & ~(filters.COMMAND)
                    & filters.Regex("^Confirm|Cancel|[\+\-]*\d+$"),
                    bot_laundry.laun_update,
                ),
            ],
            bot_laundry.LAUN_CONF: [
                MessageHandler(
                    filters.TEXT
                    & ~(filters.COMMAND)
                    & filters.Regex("^Complete Laundry Update|Do Not Update$"),
                    bot_laundry.laun_conf,
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", bot_laundry.laundry_premature_cancel)],
    )


# Start handler -> Public
def create_start_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", bot_start.start),
        ],
        states={
            bot_start.ACTION_START: [
                MessageHandler(
                    filters.TEXT & filters.Regex("^Register$") & ~(filters.COMMAND),
                    bot_register.register_start,
                ),
                MessageHandler(
                    filters.TEXT & filters.Regex("^Loan$") & ~(filters.COMMAND),
                    bot_loan.loan_start,
                ),
                MessageHandler(
                    filters.TEXT & filters.Regex("^Laundry$") & ~(filters.COMMAND),
                    bot_laundry.laundry_start,
                ),
            ],
        },
        fallbacks=[CommandHandler("start", bot_start.start)],
    )
