""" Unit tests for example app """
# --------------------------------------------------
#    Imports
# --------------------------------------------------
import pytest
from selenium.webdriver.common.by import By
from pylinkjs.utils.testing import selenium_test_begin, selenium_test_compare_and_finish 
from examples.example.example import main as example_main


# --------------------------------------------------
#    Constants
# --------------------------------------------------
UPDATE_TRUTH = False


# --------------------------------------------------
#    Helper Functions
# --------------------------------------------------
class TestExample:
    """ tests for example app """
    def test_example_button_click(self):
        """check that the basic render is ok"""
        # setup for selenium test        
        driver, _url_with_port = selenium_test_begin(server_func=example_main, url='http://localhost')

        # exercise the web apge        
        e = driver.find_element(By.XPATH, '//button[text()="Click me"]')
        e.click()

        # final comparison with redacted rectangles
        redacted = [[100, 50, 150, 30]]
        selenium_test_compare_and_finish(driver=driver, update_truth=UPDATE_TRUTH, redacted=redacted)


    def test_example_page2(self):
        """check that page 2 of the example works"""
        # setup for selenium test        
        driver, _url_with_port = selenium_test_begin(server_func=example_main, url='http://localhost')

        # exercise the web apge        
        e = driver.find_element(By.XPATH, '//a[text()="Click here to go to example 2 page"]')
        e.click()

        # final comparison with redacted rectangles
        selenium_test_compare_and_finish(driver=driver, update_truth=UPDATE_TRUTH, redacted=[])


# --------------------------------------------------
#    Main
# --------------------------------------------------
if __name__ == "__main__":
    pytest.main(args=['-s'])
