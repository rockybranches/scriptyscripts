import unittest
from unittest.mock import patch
from scriptyscripts.tools.interactive_pager import interactive_pager


class TestCLI(unittest.TestCase):
    @patch('scriptyscripts.tools.interactive_pager.Application.run', return_value="Option 2")
    @patch('builtins.print')
    def test_interactive_pager(self, mocked_print, mock_run):
        """Test the interactive_pager function."""
        test_items = ["Option 1", "Option 2", "Option 3"]
        selection = interactive_pager(test_items)
        mocked_print.assert_called_with(f"You selected: Option 2")
        self.assertEqual(selection, "Option 2")


if __name__ == '__main__':
    unittest.main()
