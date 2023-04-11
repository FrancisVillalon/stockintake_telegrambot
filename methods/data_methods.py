import pandas as pd
from database.db_conn import *
from database.db_models import *
import os


c = db.get_connection()
s = db.create_session(c)


def load_in_db(file_path, c, table_name):
    df = pd.read_excel(file_path, index_col=False)
    print(df)
    conn = c.connect()
    df.to_sql(table_name, con=conn, if_exists="append", index=False)
    conn.commit()
    conn.close()


def get_cat_list() -> "Get list of categories in database":
    return [cat_name for (cat_name,) in s.query(Category.cat_name).all()]


def get_item_list(cat_name) -> "Get item list in category":
    q = s.query(Category).filter(Category.cat_name == str(cat_name)).first()
    if q:
        cat_id = int(q.cat_id)
        item_list = [
            item_name
            for (item_name, cat_id) in s.query(Stock.item_name, Stock.cat_id)
            .filter(Stock.cat_id == int(cat_id))
            .all()
        ]
    else:
        item_list = []
    return item_list
