import tomllib

from sqlalchemy import func

from database.db_conn import Database
from database.db_models import *

""""
Methods for handling user details and access control
Example: Check if user is admin
"""

db = Database()


# Get list of users that contains this string (case-insensitive)
def search_user(searchString):
    with db.session_scope() as s:
        queryResult = (
            s.query(Usr)
            .filter(Usr.telegram_username.ilike(searchString))
            .all()
            .to_dict()
        )
        return queryResult if queryResult else None


# Delete user in database
def delete_user(telegram_id):
    with db.session_scope() as s:
        query_str = s.query(Usr).filter(Usr.telegram_id == f"{telegram_id}")
        usr_exists = query_str.first() is not None
        if usr_exists:
            query_str.delete()


# Update user_role in database
def update_user_role(telegram_id, role):
    with db.session_scope() as s:
        query_str = s.query(Usr).filter(Usr.telegram_id == f"{telegram_id}")
        usr_exists = query_str.first() is not None
        if usr_exists:
            query_str.update({"role": role})


# Update username of current user in database
def update_username(telegram_id, telegram_username):
    with db.session_scope() as s:
        query_str = s.query(Usr).filter(Usr.telegram_id == f"{telegram_id}")
        usr_exists = query_str.first() is not None
        if usr_exists:
            query_str.update({"telegram_username": telegram_username})


# Register applicant -> Add applicant to Applicant table, This DOES NOT make the applicant a verified user
def register_applicant(telegram_id, telegram_username):
    if telegram_username is None:
        return -2
    else:
        with db.session_scope() as s:
            user_lookup = (
                s.query(Usr.telegram_id)
                .filter(Usr.telegram_id == f"{telegram_id}")
                .first()
            ) is not None
            applicant_lookup = (
                s.query(Applicant.telegram_id)
                .filter(Applicant.telegram_id == f"{telegram_id}")
                .first()
            ) is not None
            if applicant_lookup:
                return -1
            elif user_lookup:
                return 0
            else:
                try:
                    applicant = Applicant(
                        telegram_id=telegram_id, telegram_username=telegram_username
                    )
                    s.add(applicant)
                    return 1
                except Exception as e:
                    return -3


# Verify functions
# Check if current conversation is with a registered user
def verify_user(telegram_id):
    with db.session_scope() as s:
        usr_bool = (
            s.query(Usr).filter(Usr.telegram_id == f"{telegram_id}").first() is not None
        )
        db.commit_kill(s)
        return usr_bool


# Check if user is an admin
def verify_admin(telegram_id):
    with db.session_scope() as s:
        admin_bool = (
            s.query(Usr.telegram_id, Usr.role)
            .filter((Usr.telegram_id == f"{telegram_id}") & (Usr.role == "admin"))
            .first()
        ) is not None
        return admin_bool


# Verify an applicant by their username, case insensitive search -> Makes an applicant a registered user
def verify_applicant(telegram_username):
    with db.session_scope() as s:
        find_user_query = s.query(Applicant).filter(
            func.lower(Applicant.telegram_username)
            == func.lower(f"{telegram_username}")
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
            return 1
        else:
            return -1


# Get user details
def get_user_role(telegram_id):
    with db.session_scope() as s:
        query_str = s.query(Usr).filter(Usr.telegram_id == f"{telegram_id}")
        usr_exists = query_str.first() is not None
        if usr_exists:
            r = query_str.first().role
            return r
        else:
            return None


def get_user_id(telegram_username):
    with db.session_scope() as s:
        query_str = s.query(Usr).filter(
            func.lower(Usr.telegram_username) == func.lower(f"{telegram_username}")
        )
        usr_exists = query_str.first() is not None
        if usr_exists:
            r = query_str.first().telegram_id
            return r
        else:
            return None


def get_user_name(telegram_id):
    with db.session_scope() as s:
        q = (
            s.query(Usr)
            .filter(Usr.telegram_id == f"{telegram_id}")
            .first()
            .telegram_username
        )
        return q


def get_admin_ids():
    with db.session_scope() as s:
        query_str = s.query(Usr.telegram_id).filter(Usr.role == "admin").all()
        list_admin_id = [x for (x,) in query_str]
        return list_admin_id
