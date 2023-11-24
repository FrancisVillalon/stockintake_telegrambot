from telegram import Update
from telegram.ext import ContextTypes

from database.db_conn import *

ACTION_START, LOAN_STATE, REG_STATE, LAUN_STATE = range(4)
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
        "Registered as Admin.\nType '/start' to get started.",
    )
    return ACTION_START

