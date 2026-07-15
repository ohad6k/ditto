import unittest

from calculator import divide


class CalculatorTest(unittest.TestCase):
    def test_divides_total_by_count(self):
        self.assertEqual(4, divide(12, 3))


if __name__ == "__main__":
    unittest.main()
