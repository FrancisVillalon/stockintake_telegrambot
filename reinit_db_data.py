from database.db_conn import *
from database.db_models import *
from methods.data_methods import *

db.recreate_database(c)
DATADIR = "./database/data/spreadsheets/"
load_in_db(os.path.join(DATADIR, "data_stock.xlsx"), c, "stock")
load_in_db(os.path.join(DATADIR, "data_categories.xlsx"), c, "category")
