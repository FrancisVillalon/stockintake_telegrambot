import pandas as pd
from database.db_conn import *
from database.db_models import *
import os


c = db.get_connection()
s = db.create_session(c)


def load_in_db(file_path, c, table_name):
    df = pd.read_excel(file_path, index_col=False)
    conn = c.connect()
    df.to_sql(table_name, con=conn, if_exists="append", index=False)
    conn.commit()
    conn.close()


def load_df_into_db(df, c, table_name):
    conn = c.connect()
    df.to_sql(table_name, con=conn, if_exists="append", index=False)
    conn.commit()
    conn.close()


def get_cat_list() -> "Get list of categories in database, used for keyboard":
    cat_list = [cat_name for (cat_name,) in s.query(Category.cat_name).all()]
    cat_list = [cat_list[x : x + 3] for x in range(0, len(cat_list), 3)]
    return cat_list


def get_item_list(cat_name) -> "Get item list in category, used for keyboard":
    q = s.query(Category).filter(Category.cat_name == str(cat_name)).first()
    if q:
        cat_id = int(q.cat_id)
        item_list = [
            item_name
            for (item_name, cat_id) in s.query(Stock.item_name, Stock.cat_id)
            .filter(Stock.cat_id == int(cat_id))
            .all()
        ]
        item_list = [item_list[x : x + 3] for x in range(0, len(item_list), 3)]
    else:
        item_list = []
    return item_list


def get_all_item_list() -> "Retrieve list of all item names in stock":
    q = s.query(Stock.item_name).all()
    item_list = [x for (x,) in q]
    return item_list


def get_item_id(cat_name, item_name):
    # DetachedInstanceError
    q = (
        s.query(Stock)
        .join(Category, Stock.cat_id == Category.cat_id)
        .filter(
            (Stock.item_name == f"{item_name}") & (Category.cat_name == f"{cat_name}")
        )
    ).first()
    item_id = q.item_id
    return item_id


def get_item_details(item_id) -> "Get item details":
    q = s.query(Stock).filter(Stock.item_id == int(item_id)).first()
    return q


def verify_item_cat(item_id, cat_id) -> "Check if this item belongs to this category":
    q = (
        s.query(Stock)
        .filter((Stock.item_id == f"{item_id}") & (Stock.cat_id == int(cat_id)))
        .first()
    )
    return q is not None


def set_order(order_id, telegram_id, order_datetime):
    s_temp = db.create_session(c)
    _order = Ordr(
        order_id=order_id, telegram_id=telegram_id, order_datetime=order_datetime
    )
    s_temp.add(_order)
    db.commit_kill(s_temp)
    return


def set_loan(
    loan_id,
    telegram_id,
    loan_status,
    item_id,
    item_quantity,
    approved_by,
    approved_datetime,
    order_id,
):
    s_temp = db.create_session(c)
    _lr = Loan(
        loan_id=loan_id,
        telegram_id=telegram_id,
        loan_status=loan_status,
        item_id=item_id,
        item_quantity=item_quantity,
        approved_by=approved_by,
        approved_datetime=approved_datetime,
        order_id=order_id,
    )
    db.commit_kill(s_temp)
    return
