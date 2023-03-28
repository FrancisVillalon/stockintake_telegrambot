import tomllib
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.engine import URL
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import close_all_sessions
import urllib.parse
from database.db_models import *

with open("./config.toml", "rb") as f:
    data = tomllib.load(f)
    db_user = data["database"]["db_user"]
    db_secret = data["database"]["db_secret"]
    db_name = data["database"]["db_name"]


class db_conn:
    def __init__(self):
        self.DB_STRING = f"postgresql://{db_user}:{db_secret}@127.0.0.1:5432/{db_name}"
        self.DB_ENGINE = create_engine(self.DB_STRING)

    def recreate_database(self):
        Base.metadata.drop_all(self.DB_ENGINE)
        Base.metadata.create_all(self.DB_ENGINE)
        return

    def create_session(self):
        return Session(bind=self.DB_ENGINE)

    def commit_kill(self, s):
        s.commit()
        s.close()
        return

    def kill_conn(self, conn):
        conn.close()
        return

    def kill_all_sessions(self):
        close_all_sessions()
        return
