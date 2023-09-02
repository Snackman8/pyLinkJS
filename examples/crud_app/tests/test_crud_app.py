""" Unit tests for crud app """
# --------------------------------------------------
#    Imports
# --------------------------------------------------
import pytest
from pylinkjs.utils.testing import download_and_compare
from examples.crud_app.crud_app import main as crud_app_main


# --------------------------------------------------
#    Constants
# --------------------------------------------------
UPDATE_TRUTH = False


# --------------------------------------------------
#    Helper Functions
# --------------------------------------------------
class TestCrudApp:
    """ tests for crud app """
    def test_crud_app(self):
        """check that the basic render is ok"""
        download_and_compare(server_func=crud_app_main, url='http://localhost', update_truth=UPDATE_TRUTH)


# --------------------------------------------------
#    Main
# --------------------------------------------------
if __name__ == "__main__":
    pytest.main(args=['-s'])
