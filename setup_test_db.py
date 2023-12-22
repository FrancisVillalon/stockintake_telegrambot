"""
Basic setup file that drops all tables in the database and recreates 
the tables using excel files. 

This is used to put test data into the database for testing various application functions.

"""


import os

import pandas as pd

from database.db_conn import Database
from database.db_models import Category, Stock

DATADIR = "./database/data/spreadsheets/"


db = Database()


db.recreate_database()
print("Database has been purged.")
db.load_excel_into_db(os.path.join(DATADIR, "data_stock.xlsx"), "stock")
print("Stock data reinserted.")
db.load_excel_into_db(os.path.join(DATADIR, "data_categories.xlsx"), "category")
print("Categories data reinserted.")
