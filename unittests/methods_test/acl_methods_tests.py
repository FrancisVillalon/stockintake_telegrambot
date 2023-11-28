import os
import sys

sys.path.append(os.path.abspath("./."))

import unittest

from database.db_conn import *
from database.db_models import *


class TestACL(unittest.TestCase):
    def test_delete_user(self):
        pass
    def test_update_user_role(self):
        pass
    def test_update_username(self):
        pass
    def test_register_applicant(self):
        # 1. If not user -> Add to applicant
        # 2. If applicant -> return -1
        # 3. If user -> return 0
        # 4. Exception -> return -3
        pass
    def test_verify_applicant(self):
        # 1. if applicant exists -> register as user
        # 2. if applicant does not exist in applicant table -> return -1
        pass
    def test_get_user_role(self):
        pass
    def test_get_user_id(self):
        pass
    def test_get_user_name(self):
        pass
    def test_get_admin_ids(self):
        pass