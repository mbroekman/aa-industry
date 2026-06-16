"""
Industry Test
"""

# Django
from django.test import TestCase


class TestIndustry(TestCase):
    """
    TestIndustry
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Test setup
        :return:
        :rtype:
        """

        super().setUpClass()

    def test_industry(self):
        """
        Dummy test function
        :return:
        :rtype:
        """

        self.assertEqual(True, True)
