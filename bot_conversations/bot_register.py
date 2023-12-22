"""
This conversation handles the registration of users by admins.
Applicants need to be registered by an admin through this conversation before being able to use the bot
"""


from re import match

from tabulate import tabulate
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from methods.acl_methods import get_user_id, get_user_role, verify_applicant
from methods.rkey_methods import show_keyboard_conf, show_keyboard_start

# Defining Conversation state
REG_CONF_PROMPT = 0
REG_TERMINUS = 1
REG_CANCEL = 2


#! Add type hinting
# Handling premature exit of operation
async def register_premature_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_message(
        "Registration prematurely cancelled.",
        reply_markup=show_keyboard_start(
            update.effective_chat.id, context.user_data["role"]
        ),
    )
    context.user_data.clear()
    return ConversationHandler.END


# Start of registration route -> Checks if admin as only admins can register other users
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Conversations can only take place one at a time. Hence, the usage of a user status
    context.user_data["in_conversation"] = True
    context.user_data["role"] = get_user_role(update.effective_chat.id)
    if context.user_data["role"] != "admin":
        await update.message.reply_text(
            f"You are not authorized.",
            reply_markup=show_keyboard_start(
                update.effective_chat.id, context.user_data["role"]
            ),
        )
        return ConversationHandler.END
    text = update.message.text
    await update.message.reply_text(f"Who do you want to register?")
    return REG_CONF_PROMPT


# Admin inputs name to register here
async def register_conf_prompt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    applicant_name = update.message.text
    # Input validation
    if match(r"^[A-Za-z0-9_]{5,}$", applicant_name) and str(applicant_name).upper():
        await update.message.reply_text(
            f"You want to register applicant '{applicant_name}' ?",
            reply_markup=show_keyboard_conf(),
        )
        context.user_data["applicant_name_chosen"] = applicant_name
        return REG_TERMINUS
    else:
        await update.message.reply_text(
            "That is not a valid telegram name. Please enter a name that is not too short and only contains letters, numbers, and underscores."
        )
        return None


# Admin confirmation reply -> CONVERSATION.END
async def register_conf_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    conf_reply = update.message.text
    if conf_reply.lower() == "cancel":
        context.user_data["role"] = get_user_role(update.effective_chat.id)
        await update.message.reply_text(
            f"Registration prematurely cancelled.",
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
            case -1:
                await update.effective_chat.send_message(
                    f"We cannot find an applicant with username '{applicant}'.",
                    reply_markup=reply_markup,
                )
    context.user_data.clear()
    return ConversationHandler.END
