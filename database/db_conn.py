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

    def get_connection(self):
        global _engine
        if not _engine:
            _engine = create_engine(self.DB_STRING)
        return _engine

    def recreate_database(self, c):
        Base.metadata.drop_all(c)
        Base.metadata.create_all(c)
        return

    def create_session(self, c):
        return Session(bind=c)

    def commit_kill(self, s):
        s.commit()
        s.close()
        return

    def kill_conn(self, c):
        c.close()
        return

    def kill_all_sessions(self):
        close_all_sessions()
        return


_engine = None
db = db_conn()
