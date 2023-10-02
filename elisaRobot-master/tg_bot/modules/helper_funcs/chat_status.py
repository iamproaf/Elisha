from functools import wraps

from tg_bot import (
    DEL_CMDS,
    DEV_USERS,
    SUDO_USERS,
    SUPPORT_USERS,
    WHITELIST_USERS,
    SARDEGNA_USERS,
    dispatcher,
    MOD_USERS
)

from telegram import Update, TelegramError, ChatMember, Chat, User
from telegram.ext import CallbackContext


def is_whitelist_plus(user_id: int) -> bool:
    return any(
        user_id in user
        for user in [
            WHITELIST_USERS,
            SUPPORT_USERS,
            SUDO_USERS,
            DEV_USERS,
            MOD_USERS
        ]
    )


def is_support_plus(user_id: int) -> bool:
    return user_id in SUPPORT_USERS or user_id in SUDO_USERS or user_id in DEV_USERS


def is_sudo_plus(user_id: int) -> bool:
    return user_id in SUDO_USERS or user_id in DEV_USERS

def is_user_ban_protected(update: Update, user_id: int, member: ChatMember = None) -> bool:
    chat = update.effective_chat
    msg = update.effective_message
    if (
            chat.type == "private"
            or user_id in SUDO_USERS
            or user_id in DEV_USERS
            or user_id in WHITELIST_USERS
            or user_id in SARDEGNA_USERS
            or chat.all_members_are_administrators
            or (msg and msg.reply_to_message and msg.reply_to_message.sender_chat is not None
                and msg.reply_to_message.sender_chat.type != "channel")
    ):
        return True

    if not member:
        member = chat.get_member(user_id)

    return member.status in ("administrator", "creator")



def dev_plus(func):
    @wraps(func)
    def is_dev_plus_func(update: Update, context: CallbackContext, *args, **kwargs):
        # bot = context.bot
        user = update.effective_user

        if user.id in DEV_USERS:
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except TelegramError:
                pass
        else:
            update.effective_message.reply_text(
                "This is a developer restricted command."
                " You do not have permissions to run this."
            )

    return is_dev_plus_func


def sudo_plus(func):
    @wraps(func)
    def is_sudo_plus_func(update: Update, context: CallbackContext, *args, **kwargs):
        # bot = context.bot
        user = update.effective_user

        if user and is_sudo_plus(user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except TelegramError:
                pass
        else:
            update.effective_message.reply_text(
                "This command is restricted to users with special access, you can't use it."
            )

    return is_sudo_plus_func


def support_plus(func):
    @wraps(func)
    def is_support_plus_func(update: Update, context: CallbackContext, *args, **kwargs):
        # bot = context.bot
        user = update.effective_user

        if user and is_support_plus(user.id):
            return func(update, context, *args, **kwargs)
        elif DEL_CMDS and " " not in update.effective_message.text:
            try:
                update.effective_message.delete()
            except TelegramError:
                pass

    return is_support_plus_func


def whitelist_plus(func):
    @wraps(func)
    def is_whitelist_plus_func(
            update: Update, context: CallbackContext, *args, **kwargs
    ):
        user = update.effective_user

        if user and is_whitelist_plus(user.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                "You don't have access to use this.\nVisit @Elisha_support"
            )

    return is_whitelist_plus_func

def user_admin(func):
    @wraps(func)
    def is_admin(update, context, *args, **kwargs):
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        if user and is_user_admin(update.effective_chat, user.id):
            return func(update, context, *args, **kwargs)

        elif not user:
            pass

        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

        elif (admin_sql.command_reaction(chat.id) == True):
            update.effective_message.reply_text("Who dis non-admin telling me what to do?")

    return is_admin

def bot_admin(func):
    @wraps(func)
    def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            not_admin = "I'm not admin! - REEEEEE"
        else:
            not_admin = f"I'm not admin in <b>{update_chat_title}</b>! - REEEEEE"

        if is_bot_admin(chat, bot.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(not_admin, parse_mode=ParseMode.HTML)

    return is_admin

def user_admin_no_reply(func):
    @wraps(func)
    def is_admin(update, context, *args, **kwargs):
        user = update.effective_user  # type: Optional[User]
        if user and is_user_admin(update.effective_chat, user.id):
            return func(update, context, *args, **kwargs)

        elif not user:
            pass

        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

    return is_admin

def is_user_admin(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    if (
        chat.type == "private"
        or user_id in SUDO_USERS
        or chat.all_members_are_administrators
        or user_id in [777000, 1087968824]
    ):  # Count telegram and Group Anonymous as admin
        return True
    if not member:
        with THREAD_LOCK:
            # try to fetch from cache first.
            try:
                return user_id in ADMIN_CACHE[chat.id]
            except KeyError:
                # keyerror happend means cache is deleted,
                # so query bot api again and return user status
                # while saving it in cache for future useage...
                chat_admins = dispatcher.bot.getChatAdministrators(chat.id)
                admin_list = [x.user.id for x in chat_admins]
                ADMIN_CACHE[chat.id] = admin_list

                return user_id in admin_list
    else:
        return member.status in ("administrator", "creator")


def connection_status(func):
    @wraps(func)
    def connected_status(update: Update, context: CallbackContext, *args, **kwargs):
        if update.effective_chat is None or update.effective_user is None:
            return
        if conn := connected(
                context.bot,
                update,
                update.effective_chat,
                update.effective_user.id,
                need_admin=False,
        ):
            chat = dispatcher.bot.getChat(conn)
            update.__setattr__("_effective_chat", chat)
            return func(update, context, *args, **kwargs)
        elif update.effective_message.chat.type == "private":
            update.effective_message.reply_text(
                    "Send /connect in a group that you and I have in common first."
            )
            return connected_status
        return func(update, context, *args, **kwargs)

    return connected_status

# Workaround for circular import with connection.py
from tg_bot.modules import connection

connected = connection.connected
