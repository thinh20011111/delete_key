from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class SeleniumHelper:
    def __init__(self, browser="chrome"):
        if browser.lower() == "chrome":
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        else:
            raise ValueError("Unsupported browser!")

    def open_url(self, url):
        self.driver.get(url)

    def find_element(self, by, value):
        return self.driver.find_element(by, value)

    def click_element(self, by, value):
        element = self.wait_for_element_to_appear(by, value)
        if element:
            element.click()

    def input_text(self, by, value, text):
        element = self.wait_for_element_to_appear(by, value)
        if element:
            element.clear()
            element.send_keys(text)

    def wait_for_element_to_appear(self, by, value, timeout=120):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except:
            return None

    def execute_javascript(self, script, *args):
        return self.driver.execute_script(script, *args)

    def switch_to_new_window(self):
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def close_browser(self):
        self.driver.quit()