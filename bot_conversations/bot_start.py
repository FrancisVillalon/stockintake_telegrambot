from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from methods.acl_methods import (
    get_user_name,
    get_user_role,
    register_applicant,
    update_username,
)
from methods.rkey_methods import show_keyboard_start

ACTION_START = 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if user is in a conversation, if not then show the menu to start a new conversation
    # Else inform user that he is in a conversation currently and do not change conversation state
    if "in_conversation" in context.user_data.keys():
        await update.effective_chat.send_message(
            "You are currently in a conversation. Please complete the conversation or type '/cancel' to start a new conversation."
        )
        return None if context.user_data["in_conversation"] else ACTION_START

    match register_applicant(update.effective_chat.id, update.effective_chat.username):
        case 0:  # Registered user starting point
            usr_role = get_user_role(update.effective_chat.id)
            if usr_role:
                usr_name = get_user_name(update.effective_chat.id)
                if (
                    usr_name != update.effective_chat.username
                ):  # Update database if username changed
                    update_username(
                        update.effective_chat.id, update.effective_chat.username
                    )
                reply_markup = show_keyboard_start(update.effective_chat.id, usr_role)
            await update.effective_chat.send_message(
                f"Welcome back {update.effective_chat.username}! What would you like to do today?",
                reply_markup=reply_markup,
            )
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
    return ConversationHandler.END
