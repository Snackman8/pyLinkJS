""" Unit tests for example app """
# --------------------------------------------------
#    Imports
# --------------------------------------------------
import time
import pytest
from selenium.webdriver.common.by import By
from pylinkjs.utils.testing import download_and_compare_selenium
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
        def exercise_func(driver, url):
            """ function to exercise the selenium instance """
            e = driver.find_element(By.XPATH, '//button[text()="Click me"]')
            e.click()
            time.sleep(1)

        download_and_compare_selenium(server_func=example_main, url='http://localhost', exercise_func=exercise_func, update_truth=UPDATE_TRUTH,
                                      redacted = [[100, 50, 150, 30]])


    def test_example_page2(self):
        """check that the basic render is ok"""
        def exercise_func(driver, url):
            """ function to exercise the selenium instance """
            e = driver.find_element(By.XPATH, '//a[text()="Click here to go to example 2 page"]')
            e.click()
            time.sleep(1)

        download_and_compare_selenium(server_func=example_main, url='http://localhost', exercise_func=exercise_func, update_truth=UPDATE_TRUTH)


# --------------------------------------------------
#    Main
# --------------------------------------------------
if __name__ == "__main__":
    pytest.main(args=['-s'])
