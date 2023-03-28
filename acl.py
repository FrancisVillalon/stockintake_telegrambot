import secrets
import tomllib
from database.db_models import *
from database.db_conn import *
from sqlalchemy import and_

with open("./config.toml", "rb") as f:
    data = tomllib.load(f)
    bot_link = data["telegram_bot"]["bot_link"]

db = db_conn()


def get_bot_link():
    tk = secrets.token_urlsafe(nbytes=16)
    return_link = f"{bot_link}?start={tk}"
    return return_link


def register_user(telegram_id, telegram_username, role):
    s = db.create_session()
    usr = Usr(
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        role=role,
    )
    try:
        s.add(usr)
    except sqlalchemy.exc.IntegrityError:
        print("User already exists")
    db.commit_kill(s)
    return


def verify_user(telegram_id):
    s = db.create_session()
    usr_bool = (
        s.query(Usr.telegram_id).filter(telegram_id == telegram_id).first() is not None
    )
    s.close()
    return usr_bool


def verify_admin(telegram_id):
    s = db.create_session()
    admin_bool = (
        s.query(Usr.telegram_id, Usr.role)
        .filter((Usr.telegram_id == f"{telegram_id}") & (Usr.role == "admin"))
        .first()
    ) is not None
    s.close()
    return admin_bool
