from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class SeleniumHelper:
    def __init__(self, browser="chrome"):
        """Khởi tạo trình duyệt Selenium"""
        self.driver = self._initialize_driver(browser)
        self.wait = WebDriverWait(self.driver, 10)  # Chờ tối đa 10 giây

    def _initialize_driver(self, browser):
        """Khởi tạo trình duyệt dựa trên loại browser"""
        if browser.lower() == "chrome":
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")  # Mở trình duyệt toàn màn hình
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        elif browser.lower() == "firefox":
            driver = webdriver.Firefox()
        else:
            raise ValueError("Browser không được hỗ trợ. Chọn 'chrome' hoặc 'firefox'.")
        return driver

    def open_url(self, url):
        """Mở một URL"""
        try:
            self.driver.get(url)
            print(f"Đã mở URL: {url}")
        except Exception as e:
            print(f"Lỗi khi mở URL: {e}")

    def find_element(self, by=By.XPATH, value=None):
        """Tìm một phần tử trên trang"""
        try:
            element = self.wait.until(EC.presence_of_element_located((by, value)))
            return element
        except Exception as e:
            print(f"Lỗi khi tìm phần tử {value}: {e}")
            return None

    def find_elements(self, by=By.XPATH, value=None):
        """Tìm nhiều phần tử trên trang"""
        try:
            elements = self.wait.until(EC.presence_of_all_elements_located((by, value)))
            return elements
        except Exception as e:
            print(f"Lỗi khi tìm danh sách phần tử {value}: {e}")
            return []

    def click_element(self, by=By.XPATH, value=None):
        """Click vào một phần tử sau khi cuộn đến vị trí của nó"""
        try:
            # Tìm phần tử
            element = self.find_element(by, value)
            if not element:
                print(f"Không tìm thấy phần tử: {value}")
                return
            
            # Cuộn đến phần tử
            self.execute_javascript("arguments[0].scrollIntoView(true);", element)
            
            # Chờ phần tử có thể click được và click
            element = self.wait.until(EC.element_to_be_clickable((by, value)))
            element.click()
            print(f"Đã click vào phần tử: {value}")
        except Exception as e:
            print(f"Lỗi khi click phần tử {value}: {e}")

    def input_text(self, by=By.XPATH, value=None, text=None):
        """Nhập văn bản vào một phần tử"""
        try:
            element = self.find_element(by, value)
            if element:
                element.clear()
                element.send_keys(text)
                print(f"Đã nhập '{text}' vào phần tử: {value}")
        except Exception as e:
            print(f"Lỗi khi nhập văn bản vào {value}: {e}")

    def select_dropdown_by_value(self, by=By.XPATH, value=None, option_value=None):
        """Chọn một giá trị trong dropdown"""
        from selenium.webdriver.support.ui import Select
        try:
            element = self.find_element(by, value)
            if element:
                select = Select(element)
                select.select_by_value(option_value)
                print(f"Đã chọn giá trị '{option_value}' trong dropdown: {value}")
        except Exception as e:
            print(f"Lỗi khi chọn giá trị dropdown {value}: {e}")

    def wait_for_element_visible(self, by=By.XPATH, value=None):
        """Chờ cho đến khi phần tử hiển thị"""
        try:
            element = self.wait.until(EC.visibility_of_element_located((by, value)))
            print(f"Phần tử {value} đã hiển thị")
            return element
        except Exception as e:
            print(f"Lỗi khi chờ phần tử hiển thị {value}: {e}")
            return None

    def switch_to_new_window(self):
        """Chuyển sang cửa sổ/tab mới"""
        try:
            windows = self.driver.window_handles
            self.driver.switch_to.window(windows[-1])
            print("Đã chuyển sang cửa sổ/tab mới")
        except Exception as e:
            print(f"Lỗi khi chuyển cửa sổ: {e}")

    def take_screenshot(self, filename="screenshot.png"):
        """Chụp ảnh màn hình"""
        try:
            self.driver.save_screenshot(filename)
            print(f"Đã chụp ảnh màn hình và lưu tại: {filename}")
        except Exception as e:
            print(f"Lỗi khi chụp ảnh màn hình: {e}")

    def execute_javascript(self, script, *args):
        """Thực thi mã JavaScript với các tham số bổ sung"""
        try:
            result = self.driver.execute_script(script, *args)
            print("Đã thực thi mã JavaScript")
            return result
        except Exception as e:
            print(f"Lỗi khi thực thi JavaScript: {e}")
            return None

    def close_browser(self):
        """Đóng trình duyệt"""
        try:
            self.driver.quit()
            print("Đã đóng trình duyệt")
        except Exception as e:
            print(f"Lỗi khi đóng trình duyệt: {e}")