import contextlib
from io import BytesIO
from time import sleep

import tg_bot.modules.sql.users_sql as sql
from tg_bot import DEV_USERS, log, OWNER_ID, dispatcher, SYS_ADMIN, spamcheck
from .helper_funcs.chat_status import dev_plus, sudo_plus
from .sql.users_sql import get_all_users, update_user
from telegram import TelegramError, Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters
from .helper_funcs.decorators import kigcmd, kigmsg

USERS_GROUP = 4
CHAT_GROUP = 5
# DEV_AND_MORE = DEV_USERS.append(int(OWNER_ID)).append(int(SYS_ADMIN))


def get_user_id(username):
    # ensure valid userid
    if len(username) <= 5:
        return None

    if username.startswith("@"):
        username = username[1:]

    users = sql.get_userid_by_name(username)

    if not users:
        return None

    elif len(users) == 1:
        return users[0].user_id

    else:
        for user_obj in users:
            try:
                userdat = dispatcher.bot.get_chat(user_obj.user_id)
                if userdat.username == username:
                    return userdat.id

            except BadRequest as excp:
                if excp.message != "Chat not found":
                    log.exception("Error extracting user ID")

    return None


@kigcmd(command='broadcast', filters=Filters.user((SYS_ADMIN|OWNER_ID)))
def broadcast(update: Update, context: CallbackContext):
    to_send = update.effective_message.text.split(None, 1)

    if len(to_send) >= 2:
        to_group = False
        to_user = False
        if to_send[0] == "/broadcastgroups":
            to_group = True
        if to_send[0] == "/broadcastusers":
            to_user = True
        else:
            to_group = to_user = True
        chats = sql.get_all_chats() or []
        users = get_all_users()
        failed = 0
        failed_user = 0
        if to_group:
            for chat in chats:
                try:
                    context.bot.sendMessage(
                        int(chat.chat_id),
                        to_send[1],
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                    )
                    sleep(0.1)
                except TelegramError:
                    failed += 1
        if to_user:
            for user in users:
                try:
                    context.bot.sendMessage(
                        int(user.user_id),
                        to_send[1],
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                    )
                    sleep(0.1)
                except TelegramError:
                    failed_user += 1
        update.effective_message.reply_text(
            f"Broadcast complete.\nGroups failed: {failed}.\nUsers failed: {failed_user}."
        )


@kigmsg((Filters.all & Filters.chat_type.groups), group=USERS_GROUP)
def log_user(update: Update, _: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message

    update_user(msg.from_user.id, msg.from_user.username, chat.id, chat.title)

    if rep := msg.reply_to_message:
        update_user(
            rep.from_user.id,
            rep.from_user.username,
            chat.id,
            chat.title,
        )

        if rep.forward_from:
            update_user(
                rep.forward_from.id,
                rep.forward_from.username,
            )

        if rep.entities:
            for entity in rep.entities:
                if entity.type in ["text_mention", "mention"]:
                    with contextlib.suppress(AttributeError):
                        update_user(entity.user.id, entity.user.username)
        if rep.sender_chat and not rep.is_automatic_forward:
            update_user(
                rep.sender_chat.id,
                rep.sender_chat.username,
                chat.id,
                chat.title,
            )

    if msg.forward_from:
        update_user(msg.forward_from.id, msg.forward_from.username)

    if msg.entities:
        for entity in msg.entities:
            if entity.type in ["text_mention", "mention"]:
                with contextlib.suppress(AttributeError):
                    update_user(entity.user.id, entity.user.username)
    if msg.sender_chat and not msg.is_automatic_forward:
        update_user(msg.sender_chat.id, msg.sender_chat.username, chat.id, chat.title)

    if msg.new_chat_members:
        for user in msg.new_chat_members:
            if user.id == msg.from_user.id:  # we already added that in the first place
                continue
            update_user(user.id, user.username, chat.id, chat.title)

    if req := update.chat_join_request:
        update_user(req.from_user.id, req.from_user.username, chat.id, chat.title)


@kigcmd(command='chatlist')
@spamcheck
@sudo_plus
def chats(update: Update, context: CallbackContext):
    all_chats = sql.get_all_chats() or []
    chatfile = "List of chats.\n0. Chat name | Chat ID | Members count\n"
    P = 1
    for chat in all_chats:
        try:
            curr_chat = context.bot.getChat(chat.chat_id)
            bot_member = curr_chat.get_member(context.bot.id)
            chat_members = curr_chat.get_member_count(context.bot.id)
            chatfile += "{}. {} | {} | {}\n".format(
                P, chat.chat_name, chat.chat_id, chat_members
            )
            P += 1
        except:
            pass

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "glist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="glist.txt",
            caption="Here be the list of groups in my database.",
        )

@kigmsg((Filters.all & Filters.chat_type.groups), group=USERS_GROUP)
def chat_checker(update: Update, context: CallbackContext):
    bot = context.bot
    if update.effective_message.chat.get_member(bot.id).can_send_messages is False:
        bot.leaveChat(update.effective_message.chat.id)


#def __user_info__(user_id):
#    if user_id in [777000, 1087968824]:
#        return """Groups count: <code>N/A</code>"""
#    if user_id == dispatcher.bot.id:
#        return """Groups count: Why are you stalking me?"""
#    if user_id == OWNER_ID:
#        return """Groups count: <code>N/A</code>"""
#    num_chats = sql.get_user_num_chats(user_id)
#    return f"""Groups count: <code>{num_chats}</code>"""


def __stats__():
    return f"• {sql.num_users()} users, across {sql.num_chats()} chats"


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = ""  # no help string

__mod_name__ = "Users"
