from telegram import Update
from telegram.ext import ContextTypes

from methods.acl_methods import *
from methods.rkey_methods import *

ACTION_START, LOAN_STATE, REG_STATE, LAUN_STATE = range(4)
# Register route entry
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data["role"] != "admin":
        await update.message.reply_text(
            f"You are not authorized.",
            reply_markup=show_keyboard_start(
                update.effective_chat.id, context.user_data["role"]
            ),
        )
        return ACTION_START
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"Who do you want to register?")
    return REG_STATE

# Register route state
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
            case -1:
                await update.effective_chat.send_message(
                    f"We cannot find an applicant with username {applicant}."
                )

async def register_conf_prompt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if "applicant_name_chosen" not in context.user_data.keys():
        context.user_data["applicant_name_chosen"] = update.message.text
    applicant_name = context.user_data["applicant_name_chosen"]
    await update.message.reply_text(
        f"You want to register applicant '{applicant_name}' ?",
        reply_markup=show_keyboard_conf(),
    )
    return REG_STATE


async def register_conf_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    conf_reply = update.message.text
    if "applicant_name_chosen" not in context.user_data.keys():
        await update.message.reply_text(
            f"You have no selected an applicant to register yet. Please tell me who to register."
        )
        return REG_STATE
    if conf_reply.lower() == "cancel":
        # Clean up user data for next request
        context.user_data.clear()
        context.user_data["role"] = get_user_role(update.effective_chat.id)
        await update.message.reply_text(
            f"You cancelled the registration.",
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
    return ACTION_START