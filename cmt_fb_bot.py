from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import getpass # Thư viện để ẩn mật khẩu khi nhập

# --- CẤU HÌNH ---
webdriver_path = r'C:\python\chromedriver.exe' # Đảm bảo đường dẫn này chính xác

print("--- VUI LÒNG NHẬP THÔNG TIN CẤU HÌNH ---")
FB_EMAIL = input("Nhập email Facebook của bạn: ")
FB_PASSWORD = getpass.getpass("Nhập mật khẩu Facebook của bạn (sẽ không hiển thị): ")
POST_URL = input("Nhập link bài viết cần comment: ")
while not POST_URL.startswith("http"):
    print("Link bài viết không hợp lệ. Vui lòng nhập lại (phải bắt đầu bằng http hoặc https).")
    POST_URL = input("Nhập link bài viết cần comment: ")

# --- KHỞI TẠO WEBDRIVER ---
service = Service(executable_path=webdriver_path)
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-notifications")
# options.add_argument("--headless") # Chạy ẩn trình duyệt (nếu muốn, bỏ comment dòng này)
# options.add_argument("--log-level=3") # Giảm bớt log của trình duyệt trên console

try:
    driver = webdriver.Chrome(service=service, options=options)
    print("\nĐã khởi tạo trình duyệt Chrome.")
except Exception as e:
    print(f"LỖI KHỞI TẠO WEBDRIVER: {e}")
    print("Vui lòng kiểm tra lại đường dẫn chromedriver_path và phiên bản Chrome/ChromeDriver.")
    exit()

driver.get("https://www.facebook.com")
driver.maximize_window()

# --- ĐĂNG NHẬP ---
try:
    print("\n--- BẮT ĐẦU QUÁ TRÌNH ĐĂNG NHẬP ---")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "email"))
    ).send_keys(FB_EMAIL)
    print("Đã nhập email.")
    time.sleep(random.uniform(0.5, 1.5))

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "pass"))
    ).send_keys(FB_PASSWORD)
    print("Đã nhập mật khẩu.")
    time.sleep(random.uniform(0.5, 1.5))

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, "login"))
    ).click()
    print("Đã nhấn nút đăng nhập.")

    # Chờ xác nhận đăng nhập thành công
    # Tìm một element đặc trưng của trang chủ sau khi đăng nhập
    # Ví dụ: Nút "Trang chủ" hoặc avatar người dùng
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Trang chủ' or @aria-label='Home'] | //div[@aria-label='Tài khoản của bạn']"))
    )
    print("Đăng nhập thành công!")

except Exception as e:
    print(f"LỖI TRONG QUÁ TRÌNH ĐĂNG NHẬP: {e}")
    print("Vui lòng kiểm tra lại email, mật khẩu và kết nối mạng.")
    driver.quit()
    exit()

# --- ĐIỀU HƯỚNG ĐẾN BÀI VIẾT VÀ COMMENT ---
try:
    print(f"\n--- BẮT ĐẦU QUÁ TRÌNH COMMENT ---")
    print(f"Đang điều hướng đến bài viết: {POST_URL}")
    driver.get(POST_URL)
    # Chờ form comment xuất hiện
    WebDriverWait(driver, 30).until( # Tăng thời gian chờ nếu mạng chậm
        EC.presence_of_element_located((By.XPATH, "//form[.//div[@aria-label='Viết bình luận' or @aria-label='Write a comment...']]"))
    )
    print("Đã tải xong bài viết và tìm thấy khu vực comment.")
    time.sleep(random.uniform(2, 5)) # Chờ ngẫu nhiên

    # --- NẠP COMMENT TỪ FILE ---
    comments_file_path = "comments.txt"
    loaded_comments = []

    try:
        with open(comments_file_path, "r", encoding="utf-8") as f:
            loaded_comments = [line.strip() for line in f if line.strip()]
        
        if not loaded_comments:
            print(f"CẢNH BÁO: File '{comments_file_path}' trống hoặc không có comment hợp lệ.")
            exit(f"Không có comment để đăng từ file {comments_file_path}. Dừng script.")
        else:
            print(f"Đã nạp thành công {len(loaded_comments)} comment từ file '{comments_file_path}'.")
            random.shuffle(loaded_comments) # Xáo trộn danh sách comment

    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file comment '{comments_file_path}'. Vui lòng tạo file này và điền comment.")
        exit(f"Không thể tiếp tục vì không tìm thấy file {comments_file_path}.")
    except Exception as e:
        print(f"Lỗi khi đọc file comment: {e}")
        exit("Dừng script do lỗi đọc file comment.")

    num_comments_to_post_requested = 150 # Số comment bạn muốn đăng
    # Giới hạn số comment sẽ đăng bằng số comment có sẵn nếu file ít hơn yêu cầu
    num_comments_to_actually_post = min(num_comments_to_post_requested, len(loaded_comments))
    
    if num_comments_to_actually_post == 0:
        print("Không có comment nào để đăng sau khi xử lý. Dừng script.")
        exit()
        
    print(f"Sẽ cố gắng đăng {num_comments_to_actually_post} comment.")
    
    posted_comments_count = 0
    comments_available = list(loaded_comments) # Tạo bản sao để có thể pop

    for i in range(num_comments_to_actually_post):
        if not comments_available:
            print("\nĐã hết comment trong danh sách để đăng.")
            break

        # Lấy comment ngẫu nhiên từ danh sách còn lại và xóa nó đi
        comment_index_to_pop = random.randrange(len(comments_available))
        comment_text = comments_available.pop(comment_index_to_pop)
        
        try:
            print(f"\nĐang chuẩn bị comment lần thứ {posted_comments_count + 1}/{num_comments_to_actually_post}...")
            print(f"Còn lại: {len(comments_available)} comment trong danh sách chờ.")

            comment_box_xpath = "//div[@aria-label='Viết bình luận' or @aria-label='Write a comment...']"
            
            # Cuộn tới ô comment nếu cần (có thể giúp element hiển thị và click được)
            try:
                target_element = driver.find_element(By.XPATH, comment_box_xpath)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", target_element)
                time.sleep(random.uniform(0.5, 1.5))
            except Exception as scroll_err:
                print(f"Lưu ý: Không thể cuộn tới ô comment (có thể không cần thiết): {scroll_err}")

            comment_box = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, comment_box_xpath))
            )
            
            print(f"Sẽ comment: '{comment_text}'")
            comment_box.click()
            time.sleep(random.uniform(0.5, 1.5))
            
            for char_index, char_to_send in enumerate(comment_text):
                comment_box.send_keys(char_to_send)
                # Điều chỉnh tốc độ gõ chữ
                if char_index < len(comment_text) - 1 : # Nếu không phải ký tự cuối
                     time.sleep(random.uniform(0.03, 0.15)) # Nhanh hơn một chút
                else: # Ký tự cuối
                     time.sleep(random.uniform(0.1, 0.3))


            time.sleep(random.uniform(0.8, 2.5)) # Chờ sau khi gõ xong

            comment_box.send_keys(Keys.ENTER)
            print("Đã gửi comment bằng Enter.")
            
            posted_comments_count += 1
            print(f"Đã comment thành công! Tổng số: {posted_comments_count}")

            # Thời gian chờ giữa các comment
            # CÂN NHẮC KỸ THỜI GIAN DELAY NÀY ĐỂ TRÁNH BỊ BLOCK
            # Ví dụ cho 5000 comment trong 4 ngày (96 giờ) => ~69 giây/comment
            # Chạy 10 tiếng/ngày => 500 comment/ngày => ~72 giây/comment
            # Đặt quá thấp sẽ rất rủi ro.
            delay_time = random.uniform(60, 120) # Ví dụ: 1 đến 2 phút
            print(f"Đang chờ {delay_time:.2f} giây trước khi comment tiếp theo...")
            time.sleep(delay_time)

        except Exception as e:
            print(f"LỖI KHI ĐANG COMMENT: {e}")
            print("Bỏ qua comment này và thử comment tiếp theo sau khi chờ.")
            # Không thêm lại comment_text vào danh sách để tránh vòng lặp lỗi nếu comment đó gây lỗi
            time.sleep(random.uniform(15, 45)) # Chờ lâu hơn một chút khi có lỗi
            continue 

except Exception as e:
    print(f"LỖI CHUNG TRONG QUÁ TRÌNH XỬ LÝ BÀI VIẾT: {e}")

finally:
    print(f"\n--- KẾT THÚC SCRIPT ---")
    print(f"Tổng số comment đã cố gắng đăng theo yêu cầu: {posted_comments_count} / {num_comments_to_actually_post}")
    if driver: # Kiểm tra xem driver có tồn tại không trước khi quit
        input("Nhấn Enter để đóng trình duyệt...")
        driver.quit()
        print("Đã đóng trình duyệt.")