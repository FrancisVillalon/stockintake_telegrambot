from telegram import Update
from telegram.ext import ContextTypes

from methods.acl_methods import get_user_role, register_applicant
from methods.rkey_methods import show_keyboard_start

# Bot start point
# Menu states
ACTION_START, LOAN_STATE, REG_STATE, LAUN_STATE = range(4)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match register_applicant(update.effective_chat.id, update.effective_chat.username):
        case 0:  # Registered user starting point
            context.user_data.clear()
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