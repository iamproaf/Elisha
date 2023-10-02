from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from tg_bot.modules.disable import DisableAbleCommandHandler, DisableAbleMessageHandler
from telegram.ext import CallbackQueryHandler, InlineQueryHandler
from telegram.ext.filters import BaseFilter, Filters
from tg_bot import dispatcher as d, log, telethn, OWNER_ID
from typing import Optional, Union, List
from tg_bot.modules.helper_funcs.handlers import CustomCommandHandler as CommandHandler, CustomMessageHandler as MessageHandler, SpamChecker
from telethon import events
import traceback, html, requests
class KigyoTelegramHandler:
    def __init__(self, d):
        self._dispatcher = d

    def command(
            self, command: str, filters: Optional[BaseFilter] = None, admin_ok: bool = False, pass_args: bool = False,
            pass_chat_data: bool = False, run_async: bool = True, can_disable: bool = True,
            group: Optional[int] = 40
    ):
        if filters:
           filters = filters & ~Filters.update.edited_message
        else:
            filters = ~Filters.update.edited_message
        def _command(func):
            try:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleCommandHandler(command, func, filters=filters, run_async=run_async,
                                                  pass_args=pass_args, admin_ok=admin_ok), group
                    )
                else:
                    self._dispatcher.add_handler(
                        CommandHandler(command, func, filters=filters, run_async=run_async, pass_args=pass_args), group
                    )
                log.debug(f"[KIGCMD] Loaded handler {command} for function {func.__name__} in group {group}")
            except TypeError:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleCommandHandler(command, func, filters=filters, run_async=run_async,
                                                  pass_args=pass_args, admin_ok=admin_ok, pass_chat_data=pass_chat_data)
                    )
                else:
                    self._dispatcher.add_handler(
                        CommandHandler(command, func, filters=filters, run_async=run_async, pass_args=pass_args,
                                       pass_chat_data=pass_chat_data)
                    )
                log.debug(f"[KIGCMD] Loaded handler {command} for function {func.__name__}")

            return func

        return _command

    def message(self, pattern: Optional[BaseFilter] = None, can_disable: bool = True, run_async: bool = True,
                group: Optional[int] = 60, friendly=None):
        if pattern:
           pattern = pattern & ~Filters.update.edited_message
        else:
           pattern = ~Filters.update.edited_message
        def _message(func):
            try:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleMessageHandler(pattern, func, friendly=friendly, run_async=run_async), group
                    )
                else:
                    self._dispatcher.add_handler(
                        MessageHandler(pattern, func, run_async=run_async), group
                    )
                log.debug(f"[KIGMSG] Loaded filter pattern {pattern} for function {func.__name__} in group {group}")
            except TypeError:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleMessageHandler(pattern, func, friendly=friendly, run_async=run_async)
                    )
                else:
                    self._dispatcher.add_handler(
                        MessageHandler(pattern, func, run_async=run_async)
                    )
                log.debug(f"[KIGMSG] Loaded filter pattern {pattern} for function {func.__name__}")

            return func

        return _message

    def callbackquery(self, pattern: str = None, run_async: bool = True):
        def _callbackquery(func):
            self._dispatcher.add_handler(CallbackQueryHandler(pattern=pattern, callback=func, run_async=run_async))
            log.debug(f'[KIGCALLBACK] Loaded callbackquery handler with pattern {pattern} for function {func.__name__}')
            return func

        return _callbackquery

    def inlinequery(self, pattern: Optional[str] = None, run_async: bool = True, pass_user_data: bool = True,
                    pass_chat_data: bool = True, chat_types: List[str] = None):
        def _inlinequery(func):
            self._dispatcher.add_handler(
                InlineQueryHandler(pattern=pattern, callback=func, run_async=run_async, pass_user_data=pass_user_data,
                                   pass_chat_data=pass_chat_data, chat_types=chat_types))
            log.debug(
                f'[KIGINLINE] Loaded inlinequery handler with pattern {pattern} for function {func.__name__} | PASSES '
                f'USER DATA: {pass_user_data} | PASSES CHAT DATA: {pass_chat_data} | CHAT TYPES: {chat_types}')
            return func

        return _inlinequery


kigcmd = KigyoTelegramHandler(d).command
kigmsg = KigyoTelegramHandler(d).message
kigcallback = KigyoTelegramHandler(d).callbackquery
kiginline = KigyoTelegramHandler(d).inlinequery


def register(**args):
    pattern = args.get('pattern', None)
    disable_edited = args.get('disable_edited', False)
    groups_only = args.get('groups_only', False)
    no_args = args.get('no_args', False)
    raw = args.get('raw', False)

    if pattern is not None:
        if raw:
            reg = "(?i)[/!>]"
            args['pattern'] = reg + pattern
        else:
            reg = "(?i)[/!>]"
            reg += pattern
            if no_args:
                reg += "($|@OdinRobot$)"
            else:
                reg += "( |@OdinRobot )?(.*)"
            args['pattern'] = reg

    if "disable_edited" in args:
        del args['disable_edited']

    if "no_args" in args:
        del args['no_args']

    if "raw" in args:
        del args['raw']

    if "groups_only" in args:
        del args['groups_only']

    def decorator(func):
        async def wrapper(check):
            if check.edit_date and check.is_channel and not check.is_group:
                return
            user_id = check.sender_id
            if SpamChecker.check_user(user_id):
                return
            if groups_only and not check.is_group:
                await check.respond("This command can only be used in groups")
                return
            try:
                await func(check)
            except events.StopPropagation:
                raise events.StopPropagation
            except KeyboardInterrupt:
                pass
            except BaseException:
                e = html.escape(f"{check.text}")

                tb_list = traceback.format_exception(
                    None, check.error, check.error.__traceback__
                )
                tb = "".join(tb_list)
                pretty_message = (
                    "An exception was raised while handling an update\n"
                    "User: {}\n"
                    "Chat: {} {}\n"
                    "Callback data: {}\n"
                    "Message: {}\n\n"
                    "Full Traceback: {}"
                ).format(
                    check.from_id or "None",
                    check.chat.title or "",
                    check.chat_id or "",
                    check.callback_query or "None",
                    check.text.text or "No message",
                    tb,
                )

                key = requests.post(
                    "https://nekobin.com/api/documents", json={"content": pretty_message}
                ).json()
                if not key.get("result", {}).get("key"):
                    with open("error.txt", "w+") as f:
                        f.write(pretty_message)
                    check.client.send_media(
                        OWNER_ID,
                        open("error.txt", "rb"),
                        caption=f"#{check.error.identifier}\n<b>Your sugar mommy got an error for you, you cute guy:</b>\n<code>{e}</code>",
                        parse_mode="html",
                    )
                    return
                key = key.get("result").get("key")
                url = f"https://nekobin.com/{key}.py"
                check.client.send_message(
                    OWNER_ID,
                    text=f"#{check.error.identifier}\n<b>Your sugar mommy got an error for you, you cute guy:</b>\n<code>{e}</code>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Nekobin", url=url)]]),
                    parse_mode="html",
                )
                # log.error(pretty_message)

        if not disable_edited:
            telethn.add_event_handler(wrapper, events.MessageEdited(**args))
        telethn.add_event_handler(wrapper, events.NewMessage(**args))
        log.debug(f"[TLTHNCMD] Loaded handler {pattern} for function {func.__name__}")

        return wrapper

    return decorator