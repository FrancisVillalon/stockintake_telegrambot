import pandas as pd
from database.db_conn import *
from database.db_models import *
import os

DATADIR = "./database/data/spreadsheets/"

s = db.create_session()


def load_in_db(file_path, c, table_name):
    df = pd.read_excel(file_path, index_col=False)
    try:
        df.to_sql(table_name, con=c, if_exists="append", index=False)
    except Exception as e:
        print(e)
        return


db.recreate_database()
load_in_db(os.path.join(DATADIR, "data_stock.xlsx"), db.DB_ENGINE, "stock")
load_in_db(os.path.join(DATADIR, "data_categories.xlsx"), db.DB_ENGINE, "category")
print([cat_name for (cat_name,) in s.query(Category.cat_name).all()])
print(
    [
        item_name
        for (item_name, cat_id) in s.query(Stock.item_name, Stock.cat_id)
        .filter(Stock.cat_id == 1)
        .all()
    ]
)
