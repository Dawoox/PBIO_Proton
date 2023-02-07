import unittest

from main import formatData


class TestDataFormatting(unittest.TestCase):
    def test_data_is_captured_for_all_captors(self):
        test_str = '617:615:612'
        expected_output = [617, 615, 612]
        formatted_data = formatData(test_str)
        self.assertEqual(expected_output, formatted_data)


if __name__ == '__main__':
    unittest.main()
