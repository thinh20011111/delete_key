import json
import logging
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium_helper import SeleniumHelper


# Cấu hình logging chỉ ghi vào file
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Xóa các handler cũ (nếu có) để tránh in ra terminal
logger.handlers = []

# Tạo FileHandler với mode='a' để ghi đè log
file_handler = logging.FileHandler('logging.log', mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

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

def save_deleted_topic(topic, file_path="deleted_topic.json"):
    """Lưu topic đã xóa thành công vào file JSON"""
    try:
        deleted_topics = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                deleted_topics = json.load(file)
        except FileNotFoundError:
            pass
        if topic not in deleted_topics:
            deleted_topics.append(topic)
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(deleted_topics, file, ensure_ascii=False, indent=4)
            logging.info(f"Đã lưu topic '{topic}' vào {file_path}")
    except Exception as e:
        logging.error(f"Lỗi khi lưu topic '{topic}' vào {file_path}: {e}")

def save_key_count(keys_deleted, file_path="key_count.json"):
    """Lưu số key đã xóa cộng dồn vào file JSON"""
    try:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                total_keys_deleted = data.get("total_keys_deleted", 0)
        except FileNotFoundError:
            total_keys_deleted = 0
        total_keys_deleted += keys_deleted
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump({"total_keys_deleted": total_keys_deleted}, file, ensure_ascii=False, indent=4)
        logging.info(f"Đã lưu số key đã xóa: {keys_deleted}, tổng cộng: {total_keys_deleted} vào {file_path}")
    except Exception as e:
        logging.error(f"Lỗi khi lưu số key đã xóa vào {file_path}: {e}")

def delete_key_by_topic(selenium, topic, url):
    """Xóa key theo topic đã cho trong tab mới"""
    # Định nghĩa các locator
    INPUT_SEARCH = "//input[@placeholder='Filter by Key Name or Pattern']"
    BULK_ACTION = "//span[contains(text(),'Bulk Actions')]"
    COUNT_TOTAL = "/html/body/div/div/div[1]/main/div[2]/div[1]/div/div/div[1]/div/div[2]/div[1]/div/div[2]/div/div/div/div[2]/div/div[2]/div[3]/div/div[1]/span[1]"
    DELETE_BUTTON = "//button[@class='euiButton euiButton--secondary euiButton--fill']//span[@class='euiButtonContent euiButton__content']"
    CONFIRM_DELETE = "//button[contains(@class, '_deleteApproveBtn_') and contains(@class, 'euiButton--warning') and contains(@class, 'euiButton--small')]"
    DONE = "//span[@class='euiButton__text' and text()='Start New']"

    try:
        # Mở tab mới và truy cập URL
        selenium.execute_javascript("window.open('');")
        selenium.switch_to_new_window()
        selenium.open_url(url)
        time.sleep(5)  # Chờ trang tải

        logging.info(f"Xử lý topic: {topic} trong tab mới")
        search_keyword = f"*/{topic}"
        
        # Kiểm tra và reload nếu INPUT_SEARCH không hiển thị
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            input_element = selenium.wait_for_element_to_appear(By.XPATH, INPUT_SEARCH, timeout=10)
            if input_element:
                break
            logging.info(f"Không tìm thấy INPUT_SEARCH, reload trang (lần {retry_count + 1}/{max_retries})")
            selenium.driver.refresh()
            time.sleep(5)
            retry_count += 1
        if not input_element:
            logging.error(f"Không thể tìm thấy INPUT_SEARCH sau {max_retries} lần thử")
            return

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
        selenium.wait_for_element_to_appear(By.XPATH, COUNT_TOTAL, timeout=10)
        
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
                # Trích xuất số key từ count_text
                match = re.search(r'Expected amount: ~(\d+)', count_text)
                keys_deleted = int(match.group(1)) if match else 0
                logging.info(f"Số key sẽ xóa cho topic {topic}: {keys_deleted}")
                
                # Click nút Delete
                selenium.click_element(By.XPATH, DELETE_BUTTON)
                
                # Click nút Confirm Delete
                selenium.click_element(By.XPATH, CONFIRM_DELETE)
                
                done_element = selenium.wait_for_element_to_appear(By.XPATH, DONE, timeout=10)
                if done_element:
                    logging.info(f"Đã xóa key cho topic {topic} và xác nhận hoàn tất")
                    # Lưu số key đã xóa
                    if keys_deleted > 0:
                        save_key_count(keys_deleted)
                else:
                    logging.warning(f"Không tìm thấy nút DONE sau khi xóa topic {topic}, nhưng topic đã được lưu")
                    # Lưu số key đã xóa ngay cả khi không tìm thấy nút DONE
                    if keys_deleted > 0:
                        save_key_count(keys_deleted)
                
                # Lưu topic vào deleted_topic.json
                save_deleted_topic(topic)
        
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
        time.sleep(5)  # Chờ trang tải

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

        # Kiểm tra và reload nếu LIST không hiển thị
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            list_element = selenium.wait_for_element_to_appear(By.XPATH, LIST, timeout=10)
            if list_element:
                break
            logging.info(f"Không tìm thấy LIST, reload trang (lần {retry_count + 1}/{max_retries})")
            selenium.driver.refresh()
            time.sleep(5)
            retry_count += 1
        if not list_element:
            logging.error(f"Không thể tìm thấy LIST sau {max_retries} lần thử")
            return

        index = 1
        while True:
            try:
                item_xpath = ITEMS.format(index=index)
                item_element = selenium.wait_for_element_to_appear(By.XPATH, item_xpath, timeout=5)
                if not item_element:
                    scrolled_to_top = False  # Biến theo dõi trạng thái cuộn lại từ đầu
                    scroll_attempts = 0  # Đếm số lần cuộn
                    # Cuộn trong element LIST một đoạn vừa đủ
                    while scroll_attempts < 10:
                        list_element = selenium.find_element(By.XPATH, LIST)
                        if list_element:
                            # Lưu vị trí cuộn trước đó
                            scroll_position_before = selenium.execute_javascript("return arguments[0].scrollTop;", list_element)
                            logging.info(f"Đang cuộn trong element LIST để tìm item tại index {index} (lần cuộn {scroll_attempts + 1}/10)")
                            # Cuộn một đoạn bằng 50% chiều cao của LIST
                            selenium.execute_javascript("arguments[0].scrollTop += arguments[0].clientHeight * 0.5;", list_element)
                            logging.info("Đã cuộn một đoạn trong element LIST để tải thêm item")
                            time.sleep(2)  # Chờ item tải
                            # Kiểm tra lại item
                            item_element = selenium.wait_for_element_to_appear(By.XPATH, item_xpath, timeout=5)
                            if item_element:
                                break
                            # Kiểm tra vị trí cuộn mới
                            scroll_position_after = selenium.execute_javascript("return arguments[0].scrollTop;", list_element)
                            if scroll_position_before == scroll_position_after:
                                if not scrolled_to_top:
                                    # Cuộn lại từ đầu nếu đã cuộn hết mà không tìm thấy
                                    selenium.execute_javascript("arguments[0].scrollTop = 0;", list_element)
                                    logging.info(f"Đã cuộn lại từ đầu LIST để thử tìm item tại index {index}")
                                    scrolled_to_top = True
                                    time.sleep(2)  # Chờ sau khi cuộn lại
                                    scroll_attempts += 1
                                    continue
                                else:
                                    logging.info("Không thể cuộn thêm trong element LIST và đã thử cuộn lại từ đầu")
                                    break
                            scroll_attempts += 1
                    
                    if not item_element:
                        if scroll_attempts >= 10:
                            # Reload trang và bắt đầu lại từ index 1
                            logging.info(f"Đã cuộn {scroll_attempts} lần mà không tìm thấy item tại index {index}. Reload trang và bắt đầu lại từ index 1.")
                            selenium.driver.refresh()
                            time.sleep(5)  # Chờ trang tải
                            index = 1  # Đặt lại index
                            scrolled_to_top = False  # Đặt lại trạng thái cuộn
                            continue
                        
                        # Thử click nút Scan more nếu không tìm thấy item sau khi cuộn
                        scan_more = selenium.find_element(By.XPATH, SCAN_MORE)
                        if scan_more:
                            selenium.click_element(By.XPATH, SCAN_MORE)
                            logging.info("Đã click nút 'Scan more' để tải thêm item")
                            selenium.wait_for_element_to_appear(By.XPATH, item_xpath, timeout=10)
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
                    # Cuộn nhanh hơn vì topic không thỏa mãn
                    list_element = selenium.find_element(By.XPATH, LIST)
                    if list_element:
                        scroll_position_before = selenium.execute_javascript("return arguments[0].scrollTop;", list_element)
                        selenium.execute_javascript("arguments[0].scrollTop += arguments[0].clientHeight * 1.0;", list_element)
                        logging.info("Đã cuộn nhanh trong element LIST vì topic đã xử lý")
                        time.sleep(1)  # Chờ ngắn hơn
                        scroll_position_after = selenium.execute_javascript("return arguments[0].scrollTop;", list_element)
                        if scroll_position_before == scroll_position_after:
                            logging.info("Không thể cuộn thêm trong element LIST")
                    index += 1
                    continue

                if topic not in topics:
                    logging.info(f"Topic '{topic}' không có trong topic.json. Thực hiện xóa...")
                    delete_key_by_topic(selenium, topic, url)  # Xóa trong tab mới
                    save_processed_topic(topic)  # Lưu topic sau khi xóa
                else:
                    logging.info(f"Topic '{topic}' có trong topic.json. Bỏ qua...")
                    save_processed_topic(topic)  # Lưu topic dù không xóa
                    # Cuộn nhanh hơn vì topic không thỏa mãn
                    list_element = selenium.find_element(By.XPATH, LIST)
                    if list_element:
                        scroll_position_before = selenium.execute_javascript("return arguments[0].scrollTop;", list_element)
                        selenium.execute_javascript("arguments[0].scrollTop += arguments[0].clientHeight * 1.0;", list_element)
                        logging.info("Đã cuộn nhanh trong element LIST vì topic có trong topic.json")
                        time.sleep(1)  # Chờ ngắn hơn
                        scroll_position_after = selenium.execute_javascript("return arguments[0].scrollTop;", list_element)
                        if scroll_position_before == scroll_position_after:
                            logging.info("Không thể cuộn thêm trong element LIST")

                index += 1

            except Exception as e:
                logging.error(f"Lỗi khi kiểm tra item tại index {index}: {e}")
                scrolled_to_top = False  # Biến theo dõi trạng thái cuộn lại từ đầu
                scroll_attempts = 0  # Đếm số lần cuộn
                # Cuộn trong element LIST một đoạn vừa đủ
                while scroll_attempts < 10:
                    list_element = selenium.find_element(By.XPATH, LIST)
                    if list_element:
                        # Lưu vị trí cuộn trước đó
                        scroll_position_before = selenium.execute_javascript("return arguments[0].scrollTop;", list_element)
                        # Cuộn một đoạn bằng 50% chiều cao của LIST
                        selenium.execute_javascript("arguments[0].scrollTop += arguments[0].clientHeight * 0.5;", list_element)
                        logging.info(f"Đã cuộn một đoạn trong element LIST để tải thêm item sau lỗi (lần cuộn {scroll_attempts + 1}/10)")
                        time.sleep(2)  # Chờ item tải
                        # Kiểm tra lại item
                        item_element = selenium.wait_for_element_to_appear(By.XPATH, item_xpath, timeout=5)
                        if item_element:
                            break
                        # Kiểm tra vị trí cuộn mới
                        scroll_position_after = selenium.execute_javascript("return arguments[0].scrollTop;", list_element)
                        if scroll_position_before == scroll_position_after:
                            if not scrolled_to_top:
                                # Cuộn lại từ đầu nếu đã cuộn hết mà không tìm thấy
                                selenium.execute_javascript("arguments[0].scrollTop = 0;", list_element)
                                logging.info(f"Đã cuộn lại từ đầu LIST để thử tìm item tại index {index} sau lỗi")
                                scrolled_to_top = True
                                time.sleep(2)  # Chờ sau khi cuộn lại
                                scroll_attempts += 1
                                continue
                            else:
                                logging.info("Không thể cuộn thêm trong element LIST và đã thử cuộn lại từ đầu")
                                break
                        scroll_attempts += 1
                
                if not item_element:
                    if scroll_attempts >= 10:
                        # Reload trang và bắt đầu lại từ index 1
                        logging.info(f"Đã cuộn {scroll_attempts} lần mà không tìm thấy item tại index {index} sau lỗi. Reload trang và bắt đầu lại từ index 1.")
                        selenium.driver.refresh()
                        time.sleep(5)  # Chờ trang tải
                        index = 1  # Đặt lại index
                        scrolled_to_top = False  # Đặt lại trạng thái cuộn
                        continue
                    
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