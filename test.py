import unittest

from main import App


class TestDataFormatting(unittest.TestCase):
    def test_data_is_captured_for_all_captors(self):
        test_str = 'BEGIN_DATA:200:-15:27'
        expected_output = [200, -15, 27]
        formatted_data = App().formatData(test_str)
        self.assertEqual(expected_output, formatted_data)


if __name__ == '__main__':
    unittest.main()