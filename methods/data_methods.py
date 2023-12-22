from typing import Any, Dict, List, Optional

from sqlalchemy import desc

from database.db_conn import Database
from database.db_models import *
from methods.audit_methods import audit_laundry_quantity_update

""""
Methods for retrieving data that is not user details.
Examples: Getting list of items in a given category.
"""

db = Database()


# Retrieve list of all category names in stock
def get_cat_list() -> List[str]:
    with db.session_scope() as s:
        cat_list = [cat_name for (cat_name,) in s.query(Category.cat_name).all()]
        return cat_list


# Retrieve list of all item names in stock
def get_all_item_list() -> List[str]:
    with db.session_scope() as s:
        q = s.query(Stock.item_name).all()
        item_list = [x for (x,) in q]
        return item_list


# Retrieve list of all items in category
def get_all_items_cat(cat_name) -> List[Dict[str, Any]]:
    with db.session_scope() as s:
        q = (
            s.query(Stock)
            .join(Category, Stock.cat_id == Category.cat_id)
            .filter((Category.cat_name == f"{cat_name}"))
        ).all()
        result = [item.to_dict() for item in q]
        return result


# Retrieve item id of a given item in a given category
def get_item_id(cat_name, item_name) -> Optional[int]:
    with db.session_scope() as s:
        q = (
            s.query(Stock)
            .join(Category, Stock.cat_id == Category.cat_id)
            .filter(
                (Stock.item_name == f"{item_name}")
                & (Category.cat_name == f"{cat_name}")
            )
        ).first()
        return q.item_id if q and q.item_id else None


# Retrieve a dictionary of item details given an item_id
def get_item_details(item_id) -> Optional[Dict[str, Any]]:
    with db.session_scope() as s:
        q = s.query(Stock).filter(Stock.item_id == int(item_id)).first().to_dict()
        return q if q else None


# Check if this item belongs to this category
def verify_item_cat(item_id, cat_id) -> bool:
    with db.session_scope() as s:
        q = (
            s.query(Stock)
            .filter((Stock.item_id == f"{item_id}") & (Stock.cat_id == int(cat_id)))
            .first()
        )
        return q is not None


# Loan system related
# Verif
def set_order(order_id, telegram_id, order_datetime) -> None:
    with db.session_scope() as s:
        _order = Ordr(
            order_id=order_id, telegram_id=telegram_id, order_datetime=order_datetime
        )
        s.add(_order)


def set_pending_loan(item_id, loan_details, order_id, telegram_id):
    with db.session_scope() as s:
        _loan = Loan(
            loan_id=loan_details["loan_id"],
            telegram_id=telegram_id,
            loan_status="PENDING",
            item_id=item_id,
            item_quantity=loan_details["item_quantity"],
            approved_by=None,
            approved_datetime=None,
            order_id=order_id,
        )
        s.add(_loan)


# Laundry system related
def get_laundry_last() -> Optional[Dict[str, Any]]:
    with db.session_scope() as s:
        q = (
            s.query(Audit)
            .order_by(desc(Audit.log_datetime))
            .filter(Audit.log_action == "LAUNDRY_UPDATE_COMPLETE")
            .limit(1)
            .first()
        )
        if q:
            return q.to_dict()
        else:
            return None


def update_laundry(update_dict, log_id, tid) -> None:
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
