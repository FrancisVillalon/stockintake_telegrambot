import uuid
from datetime import datetime

from database.db_conn import Database
from database.db_models import Audit

db = Database()
# Audit system related
def audit_laundry_update_complete(tid, log_description, log_id):
    with db.session_scope() as s:
        new_log = Audit(
            log_id=log_id,
            log_datetime=datetime.now(),
            telegram_id=f"{tid}",
            log_action=f"LAUNDRY_UPDATE_COMPLETE",
            log_description=f"{log_description}",
        )
        s.add(new_log)


def audit_laundry_quantity_update(tid, log_description):
    with db.session_scope() as s:
        new_log = Audit(
            log_id=f"{str(uuid.uuid4())[:8]}",
            log_datetime=datetime.now(),
            telegram_id=f"{tid}",
            log_action=f"LAUNDRY_QUANTITY_UPDATE",
            log_description=f"{log_description}",
        )
        s.add(new_log)

def audit_dump(date_start,date_end):
    pass