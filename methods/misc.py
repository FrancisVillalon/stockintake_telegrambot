import pandas as pd
from database.db_conn import *
from database.db_models import *
import os

DATADIR = "./database/data/spreadsheets/"

db = db_conn()
s = db.create_session()


def load_in_db(file_path, c, table_name):
    df = pd.read_excel(file_path, index_col=False)
    df.to_sql(table_name, con=c, if_exists="append", index=False)


db.recreate_database()
load_in_db(os.path.join(DATADIR, "data_stock.xlsx"), db.DB_ENGINE, "stock")
