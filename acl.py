import secrets
import tomllib
from database.db_models import *
from database.db_conn import *
from sqlalchemy import and_

with open("./config.toml", "rb") as f:
    data = tomllib.load(f)
    bot_link = data["telegram_bot"]["bot_link"]

db = db_conn()


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


def register_applicant(telegram_id, telegram_username):
    s = db.create_session()
    if s.query(Usr.telegram_id).filter(telegram_id == telegram_id).first() is not None:
        db.commit_kill(s)
        return 0
    elif (
        s.query(Applicant.telegram_id).filter(telegram_id == telegram_id).first()
        is not None
    ):
        db.commit_kill(s)
        return -1
    else:
        try:
            applicant = Applicant(
                telegram_id=telegram_id, telegram_username=telegram_username
            )
            s.add(applicant)
        except sqlalchemy.exc.IntegrityError:
            print("User already exists")
        db.commit_kill(s)
        return 1


def verify_user(telegram_id):
    s = db.create_session()
    usr_bool = (
        s.query(Usr.telegram_id).filter(telegram_id == telegram_id).first() is not None
    )
    db.commit_kill(s)
    return usr_bool


def verify_admin(telegram_id):
    s = db.create_session()
    admin_bool = (
        s.query(Usr.telegram_id, Usr.role)
        .filter((Usr.telegram_id == f"{telegram_id}") & (Usr.role == "admin"))
        .first()
    ) is not None
    db.commit_kill(s)
    return admin_bool


def verify_applicant(telegram_username):
    s = db.create_session()
    find_user_query = s.query(Applicant).filter(
        telegram_username == f"{telegram_username}"
    )
    find_user = find_user_query.first()
    if find_user:
        verified_applicant = Usr(
            telegram_id=find_user.telegram_id,
            telegram_username=find_user.telegram_username,
            role="user",
        )
        s.add(verified_applicant)
        find_user_query.delete()
        db.commit_kill(s)
        return 1
    else:
        db.commit_kill(s)
        return -1
