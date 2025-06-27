import json
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium_helper import SeleniumHelper

# Cấu hình logging
logging.basicConfig(
    filename='logging.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    encoding='utf-8'  # Giúp log ghi được tiếng Việt
)

def load_account(file_path="account.json"):
    """Đọc thông tin tài khoản từ file JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get("account", {}).get("url", "")
    except Exception as e:
        logging.error(f"Lỗi khi đọc file {file_path}: {e}")
        return ""

def load_topics(file_path="topic.json"):
    """Đọc danh sách topic từ file JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Lỗi khi đọc file {file_path}: {e}")
        return []

def load_processed_topics(file_path="processed_topics.json"):
    """Đọc danh sách topic đã xử lý từ file JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except Exception as e:
        logging.error(f"Lỗi khi đọc file {file_path}: {e}")
        return []

def save_processed_topic(topic, file_path="processed_topics.json"):
    """Lưu topic đã xử lý vào file JSON"""
    try:
        processed_topics = load_processed_topics(file_path)
        if topic not in processed_topics:
            processed_topics.append(topic)
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(processed_topics, file, ensure_ascii=False, indent=4)
            logging.info(f"Đã lưu topic '{topic}' vào {file_path}")
    except Exception as e:
        logging.error(f"Lỗi khi lưu topic '{topic}' vào {file_path}: {e}")

def delete_key_by_topic(selenium, topic, url):
    """Xóa key theo topic đã cho trong tab mới"""
    # Định nghĩa các locator
    INPUT_SEARCH = "//input[@placeholder='Filter by Key Name or Pattern']"
    BULK_ACTION = "//span[contains(text(),'Bulk Actions')]"
    COUNT_TOTAL = "/html/body/div/div/div[1]/main/div[2]/div[1]/div/div/div[1]/div/div[2]/div[1]/div/div[2]/div/div/div/div[2]/div/div[2]/div[3]/div/div[1]/span[1]"
    DELETE_BUTTON = "//button[@class='euiButton euiButton--secondary euiButton--fill']//span[@class='euiButtonContent euiButton__content']"
    CONFIRM_DELETE = "//button[contains(@class, '_deleteApproveBtn_') and contains(@class, 'euiButton--warning') and contains(@class, 'euiButton--small')]"

    try:
        # Mở tab mới và truy cập URL
        selenium.execute_javascript("window.open('');")
        selenium.switch_to_new_window()
        selenium.open_url(url)
        time.sleep(5)  # Chờ trang tải

        logging.info(f"Xử lý topic: {topic} trong tab mới")
        search_keyword = f"collaborative_recommend/*/{topic}"
        
        # Nhập từ khóa vào ô input
        selenium.input_text(By.XPATH, INPUT_SEARCH, search_keyword)
        logging.info(f"Đã nhập từ khóa: {search_keyword}")
        
        # Nhấn Enter
        search_input = selenium.find_element(By.XPATH, INPUT_SEARCH)
        if search_input:
            search_input.send_keys(Keys.ENTER)
            logging.info(f"Đã nhấn Enter cho từ khóa: {search_keyword}")
        
        # Click nút Bulk Actions
        selenium.click_element(By.XPATH, BULK_ACTION)
        logging.info(f"Đã click nút Bulk Actions cho topic: {topic}")
        
        # Chờ để trang tải kết quả
        selenium.wait_for_element_visible(By.XPATH, COUNT_TOTAL)
        
        # Kiểm tra số lượng key
        count_element = selenium.find_element(By.XPATH, COUNT_TOTAL)
        if count_element:
            count_text = count_element.text
            logging.info(f"Số lượng key tìm được: {count_text}")
            
            if "Expected amount: N/A" in count_text:
                logging.info(f"Không có key để xóa cho topic {topic}. Reload trang...")
                selenium.driver.refresh()
                return
            
            elif "Expected amount: ~" in count_text:
                # Click nút Delete
                selenium.click_element(By.XPATH, DELETE_BUTTON)
                
                # Click nút Confirm Delete
                selenium.click_element(By.XPATH, CONFIRM_DELETE)
                
                logging.info(f"Đã xóa key cho topic {topic}")
        
        # Reload trang
        selenium.driver.refresh()
        logging.info(f"Đã reload trang sau khi xử lý topic {topic}")
        
    except Exception as e:
        logging.error(f"Lỗi khi xử lý topic {topic} trong tab mới: {e}")
        selenium.driver.refresh()
    finally:
        # Đóng tab mới và quay lại tab ban đầu
        selenium.driver.close()
        selenium.switch_to_new_window()
        logging.info("Đã đóng tab mới và quay lại tab ban đầu")

def main():
    selenium = SeleniumHelper(browser="chrome")

    try:
        url = load_account()
        if not url:
            logging.error("Không tìm thấy URL trong file account.json")
            return

        selenium.open_url(url)
        time.sleep(5)

        topics = load_topics()
        if not topics:
            logging.error("Không tìm thấy topic trong file topic.json")
            return

        processed_topics = load_processed_topics()
        if not processed_topics:
            logging.info("Không có topic nào trong processed_topics.json, bắt đầu từ danh sách rỗng")

        ITEMS = "/html/body/div/div/div[1]/main/div[2]/div[1]/div/div/div[1]/div/div[2]/div[1]/div/div[1]/div/div/div[2]/div/div/div/div/div/div[2]/div/div[{index}]/div[2]/div/div/div/div/div/span"
        LIST = "/html/body/div/div/div[1]/main/div[2]/div[1]/div/div/div[1]/div/div[2]/div[1]/div/div[1]/div/div/div[2]/div/div/div/div/div/div[2]"
        SCAN_MORE = "//span[contains(text(),'Scan more')]"

        index = 1
        while True:
            try:
                item_xpath = ITEMS.format(index=index)
                item_element = selenium.find_element(By.XPATH, item_xpath)
                if not item_element:
                    # Cuộn trong element LIST cho đến khi tìm thấy item
                    while True:
                        list_element = selenium.find_element(By.XPATH, LIST)
                        if list_element:
                            # Lưu vị trí cuộn trước đó
                            scroll_position_before = selenium.execute_javascript("return arguments[0].scrollTop;", list_element)
                            # Cuộn xuống cuối element LIST
                            selenium.execute_javascript("arguments[0].scrollTop = arguments[0].scrollHeight;", list_element)
                            logging.info("Đã cuộn xuống cuối element LIST để tải thêm item")
                            time.sleep(2)  # Chờ item mới tải
                            # Kiểm tra lại item
                            item_element = selenium.find_element(By.XPATH, item_xpath)
                            if item_element:
                                break
                            # Kiểm tra vị trí cuộn mới
                            scroll_position_after = selenium.execute_javascript("return arguments[0].scrollTop;", list_element)
                            if scroll_position_before == scroll_position_after:
                                logging.info("Không thể cuộn thêm trong element LIST")
                                break
                    
                    if not item_element:
                        # Thử click nút Scan more nếu không tìm thấy item sau khi cuộn
                        scan_more = selenium.find_element(By.XPATH, SCAN_MORE)
                        if scan_more:
                            selenium.click_element(By.XPATH, SCAN_MORE)
                            logging.info("Đã click nút 'Scan more' để tải thêm item")
                            selenium.wait_for_element_visible(By.XPATH, item_xpath)
                            item_element = selenium.find_element(By.XPATH, item_xpath)
                        else:
                            logging.info("Không tìm thấy nút 'Scan more'. Kết thúc lặp item.")
                            break

                item_text = item_element.text
                logging.info(f"Kiểm tra item: {item_text}")

                topic = item_text.split('/')[-1] if '/' in item_text else item_text

                # Kiểm tra xem topic đã được xử lý trước đó chưa
                if topic in processed_topics:
                    logging.info(f"Topic '{topic}' đã được xử lý trước đó. Bỏ qua...")
                    save_processed_topic(topic)  # Vẫn lưu để đảm bảo nhất quán
                    index += 1
                    continue

                if topic not in topics:
                    logging.info(f"Topic '{topic}' không có trong topic.json. Thực hiện xóa...")
                    delete_key_by_topic(selenium, topic, url)  # Truyền url để mở tab mới
                    save_processed_topic(topic)  # Lưu topic sau khi xóa
                else:
                    logging.info(f"Topic '{topic}' có trong topic.json. Bỏ qua...")
                    save_processed_topic(topic)  # Lưu topic dù không xóa

                index += 1

            except Exception as e:
                logging.error(f"Lỗi khi kiểm tra item tại index {index}: {e}")
                # Cuộn trong element LIST cho đến khi tìm thấy item
                while True:
                    list_element = selenium.find_element(By.XPATH, LIST)
                    if list_element:
                        # Lưu vị trí cuộn trước đó
                        scroll_position_before = selenium.execute_javascript("return arguments[0].scrollTop;", list_element)
                        # Cuộn xuống cuối element LIST
                        selenium.execute_javascript("arguments[0].scrollTop = arguments[0].scrollHeight;", list_element)
                        logging.info("Đã cuộn xuống cuối element LIST để tải thêm item sau lỗi")
                        time.sleep(2)  # Chờ item mới tải
                        # Kiểm tra lại item
                        item_element = selenium.find_element(By.XPATH, item_xpath)
                        if item_element:
                            break
                        # Kiểm tra vị trí cuộn mới
                        scroll_position_after = selenium.execute_javascript("return arguments[0].scrollTop;", list_element)
                        if scroll_position_before == scroll_position_after:
                            logging.info("Không thể cuộn thêm trong element LIST")
                            break
                
                if not item_element:
                    # Thử click nút Scan more nếu không tìm thấy item sau khi cuộn
                    scan_more = selenium.find_element(By.XPATH, SCAN_MORE)
                    if scan_more:
                        selenium.click_element(By.XPATH, SCAN_MORE)
                        logging.info("Đã click nút 'Scan more' để tải thêm item sau lỗi")
                        continue
                    else:
                        logging.info("Không tìm thấy nút 'Scan more'. Kết thúc lặp item.")
                        break

    except Exception as e:
        logging.error(f"Lỗi trong quá trình xử lý: {e}")

    finally:
        selenium.close_browser()
        logging.info("Đã đóng trình duyệt")

if __name__ == "__main__":
    main()