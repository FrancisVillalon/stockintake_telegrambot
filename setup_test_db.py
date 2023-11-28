import os

import pandas as pd

from database.db_conn import Database
from database.db_models import Category, Stock

DATADIR = "./database/data/spreadsheets/"



db = Database()



db.recreate_database()
db.load_excel_into_db(os.path.join(DATADIR, "data_stock.xlsx"), db.DB_ENGINE, "stock")
db.load_excel_into_db(os.path.join(DATADIR, "data_categories.xlsx"), db.DB_ENGINE, "category")
with db.session_scope as s:
    print([cat_name for (cat_name,) in s.query(Category.cat_name).all()])
    print(
        [
            item_name
            for (item_name, cat_id) in s.query(Stock.item_name, Stock.cat_id)
            .filter(Stock.cat_id == 1)
            .all()
        ]
    )