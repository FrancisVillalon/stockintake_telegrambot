from sqlalchemy import desc

from database.db_conn import Database
from database.db_models import *
from methods.audit_methods import audit_laundry_quantity_update

db = Database()
# Get list of categories in database, used for keyboard
def get_cat_list():
    with db.session_scope() as s:
        cat_list = [cat_name for (cat_name,) in s.query(Category.cat_name).all()]
        cat_list = [cat_list[x : x + 3] for x in range(0, len(cat_list), 3)]
        return cat_list

# Get item list in category, used for keyboard
def get_item_list(cat_name):
    with db.session_scope() as s:
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

# Retrieve list of all item names in stock
def get_all_item_list():
    with db.session_scope() as s:
        q = s.query(Stock.item_name).all()
        item_list = [x for (x,) in q]
        return item_list

# Retrieve list of all item names in category
def get_all_items_cat(cat_name):
    with db.session_scope() as s:
        q = (
            s.query(Stock)
            .join(Category, Stock.cat_id == Category.cat_id)
            .filter((Category.cat_name == f"{cat_name}"))
        ).all()
        return q


def get_item_id(cat_name, item_name):
    with db.session_scope() as s:
        q = (
            s.query(Stock)
            .join(Category, Stock.cat_id == Category.cat_id)
            .filter(
                (Stock.item_name == f"{item_name}") & (Category.cat_name == f"{cat_name}")
            )
        ).first()
        item_id = q.item_id
        return item_id


def get_item_details(item_id):
    with db.session_scope() as s:
        q = s.query(Stock).filter(Stock.item_id == int(item_id)).first()
        return q

# Check if this item belongs to this category
def verify_item_cat(item_id, cat_id):
    with db.session_scope() as s:
        q = (
            s.query(Stock)
            .filter((Stock.item_id == f"{item_id}") & (Stock.cat_id == int(cat_id)))
            .first()
        )
        return q is not None


# Loan system related
def set_order(order_id, telegram_id, order_datetime):
    with db.session_scope() as s:
        _order = Ordr(
            order_id=order_id, telegram_id=telegram_id, order_datetime=order_datetime
        )
        s.add(_order)



# Laundry system related
def get_laundry_last():
    with db.session_scope() as s:
        q = (
            s.query(Audit)
            .order_by(desc(Audit.log_datetime))
            .filter(Audit.log_action == "LAUNDRY_UPDATE_COMPLETE")
            .limit(1)
            .first()
        )
        return q


def update_laundry(update_dict, log_id, tid):
    l = list(update_dict.items())
    with db.session_scope() as s:
        for item, new_quant in l:
            q = s.query(Stock).filter(Stock.item_name == f"{item}")
            cur_quant = q.first().item_quantity
            q.update({Stock.item_quantity: int(new_quant)})
            audit_laundry_quantity_update(
                tid,
                f"Laundry quantity update related to log_id: {log_id}, {item}: {cur_quant} -> {new_quant} ",
            )



