from unittest import TestCase, skip
from ga_resources.test_data import create_test_data, clear_test_data
from ga_resources.utils import authorize


class TestPermissions(TestCase):
    def setUpClass(cls):
        cls.test_data = create_test_data()

    def tearDownClass(cls):
        clear_test_data()

    def test_private_page(self):
        authorize