import telegram.ext as tg
from telegram import Update
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from tg_bot import DEV_USERS, MOD_USERS, OWNER_ID, SUDO_USERS, SYS_ADMIN, WHITELIST_USERS, SUPPORT_USERS
from pyrate_limiter import (
    BucketFullException,
    Duration,
    RequestRate,
    Limiter,
    MemoryListBucket,
)
import tg_bot.modules.sql.blacklistusers_sql as sql

try:
    from tg_bot import CUSTOM_CMD
except:
    CUSTOM_CMD = False

CMD_STARTERS = CUSTOM_CMD or ["/", "!"]


class AntiSpam:
    def __init__(self):
        self.whitelist = (
            (DEV_USERS or [])
            + (SUDO_USERS or [])
            + (WHITELIST_USERS or [])
            + (SUPPORT_USERS or [])
            + (MOD_USERS or [])
        )
        # Values are HIGHLY experimental, its recommended you pay attention to our commits as we will be adjusting the values over time with what suits best.
        Duration.CUSTOM = 15  # Custom duration, 15 seconds
        self.sec_limit = RequestRate(6, Duration.CUSTOM)  # 6 / Per 15 Seconds
        self.min_limit = RequestRate(20, Duration.MINUTE)  # 20 / Per minute
        self.hour_limit = RequestRate(100, Duration.HOUR)  # 100 / Per hour
        self.daily_limit = RequestRate(1000, Duration.DAY)  # 1000 / Per day
        self.limiter = Limiter(
            self.sec_limit,
            self.min_limit,
            self.hour_limit,
            self.daily_limit,
            bucket_class=MemoryListBucket,
        )

    @staticmethod
    def check_user(user):
        """
        Return True if user is to be ignored else False
        """
        return bool(sql.is_user_blacklisted(user))
        '''try: # this should be enabled but it disables the bot
            self.limiter.try_acquire(user)
            return False
        except BucketFullException:
            return True'''

SpamChecker = AntiSpam()
MessageHandlerChecker = AntiSpam()


class CustomCommandHandler(tg.CommandHandler):
    def __init__(self, command, callback, run_async=True, **kwargs):
        if "admin_ok" in kwargs:
            del kwargs["admin_ok"]
        super().__init__(command, callback, run_async=run_async, **kwargs)

    def check_update(self, update):
        if not isinstance(update, Update) or not update.effective_message:
            return
        message = update.effective_message

        try:
            user_id = update.effective_user.id
        except:
            user_id = None

        if message.text and len(message.text) > 1:
            fst_word = message.text.split(None, 1)[0]
            if len(fst_word) > 1 and any(
                fst_word.startswith(start) for start in CMD_STARTERS
            ):
                args = message.text.split()[1:]
                command = fst_word[1:].split("@")
                command.append(
                    message.bot.username
                )  # in case the command was sent without a username

                if not (
                    command[0].lower() in self.command
                    and command[1].lower() == message.bot.username.lower()
                ):
                    return None

                if SpamChecker.check_user(user_id):
                    return None

                filter_result = self.filters(update)
                if filter_result:
                    return args, filter_result
                else:
                    return False



class CustomMessageHandler(MessageHandler):
    def __init__(self, pattern, callback, run_async=True, friendly="", **kwargs):
        super().__init__(pattern, callback, run_async=run_async, **kwargs)
        self.friendly = friendly or pattern
    def check_update(self, update):
        if isinstance(update, Update) and update.effective_message:

            try:
                user_id = update.effective_user.id
            except:
                user_id = None

            if self.filters(update):
                if SpamChecker.check_user(user_id):
                    return None
                return True
            return False


