from django.test import SimpleTestCase
from .calc import add_numbers


class TestCal(SimpleTestCase):
    def test_add_numbers(self):
        answer = add_numbers(1, 11)
        self.assertEqual(answer, 12)
