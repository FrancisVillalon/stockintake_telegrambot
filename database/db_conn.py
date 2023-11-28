import tomllib
import urllib.parse
from contextlib import contextmanager

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, close_all_sessions

from database.db_models import *

with open("./config.toml", "rb") as f:
    data = tomllib.load(f)
    db_user = data["database"]["db_user"]
    db_secret = data["database"]["db_secret"]
    db_name = data["database"]["db_name"]


class Database:
    def __init__(self,db_url=f"postgresql://{db_user}:{db_secret}@127.0.0.1:5432/{db_name}"):
        self.engine = create_engine(db_url)
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations"""
        session = self.create_session()
        try: 
            yield session 
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_session(self):
        return Session(bind=self.engine)
    
    def load_excel_into_db(self,file_path,table_name):
        df = pd.read_excel(file_path,table_name)
        with self.engine.connect() as conn:
            df.to_sql(table_name,con=conn,if_exists="append",index=False)
    def load_df_into_db(self,df,table_name):
        with self.engine.connect() as conn:
            df.to_sql(table_name,con=conn, if_exists="append",index=False)
    
    def recreate_database(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)