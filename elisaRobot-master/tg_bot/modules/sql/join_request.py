import threading

from sqlalchemy import Boolean, BigInteger
from sqlalchemy.sql.sqltypes import String
from sqlalchemy import Column

from tg_bot.modules.sql import BASE, SESSION


class JoinRequestSettings(BASE):
    __tablename__ = "join_request_settings"

    chat_id = Column(BigInteger, primary_key=True)
    setting = Column(Boolean, default=False, nullable=False)

    def __init__(self, chat_id: int, setting: bool):
        self.chat_id = chat_id
        self.setting = setting

    def __repr__(self):
        return "<JoinRequest setting {} ({})>".format(self.chat_id, self.setting)


JoinRequestSettings.__table__.create(checkfirst=True)
JOINREQUEST_SETTING_LOCK = threading.RLock()
DISABLED_CHATS = set()


def enable_join_req(chat_id: int):
    with JOINREQUEST_SETTING_LOCK:
        chat = SESSION.query(JoinRequestSettings).get(chat_id)
        if not chat:
            chat = JoinRequestSettings(chat_id, True)

        chat.setting = True
        try:
            DISABLED_CHATS.remove(chat_id)
        except KeyError:
            pass
        SESSION.add(chat)
        SESSION.commit()


def disable_join_req(chat_id: int):
    with JOINREQUEST_SETTING_LOCK:
        chat = SESSION.query(JoinRequestSettings).get(chat_id)
        if not chat:
            chat = JoinRequestSettings(chat_id, False)

        chat.setting = False
        DISABLED_CHATS.add(chat_id)
        SESSION.add(chat)
        SESSION.commit()


def join_req_status(chat_id: int) -> bool:
    return chat_id not in DISABLED_CHATS


def migrate_chat(old_chat_id, new_chat_id):
    with JOINREQUEST_SETTING_LOCK:
        chat = SESSION.query(JoinRequestSettings).get(old_chat_id)
        if chat:
            chat.chat_id = new_chat_id
            SESSION.add(chat)

        SESSION.commit()


def __load_disabled_join_req():
    global DISABLED_CHATS
    try:
        all_chats = SESSION.query(JoinRequestSettings).all()
        DISABLED_CHATS = {chat.chat_id for chat in all_chats if chat.setting is False}
    finally:
        SESSION.close()


__load_disabled_join_req()
