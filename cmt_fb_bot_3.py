import time
import os
import pickle
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidCookieDomainException
from webdriver_manager.chrome import ChromeDriverManager

# ====== Cấu hình ======
EMAIL = 'quanquan25122005@gmail.com' # Thay bằng email thật
PASSWORD = 'letriviet2005' # Thay bằng password thật
POST_URL = 'https://www.facebook.com/l.t.viet.695531/posts/pfbid0xBeLw6rz5wTkADBi7dNw9uCXAm9Xvy8bMotKqzUo9fTPCsk9BgqmfJjeZ8qszkPPl?rdid=vdDlpAKxwZI9Yl5O#' # Thay URL bài viết

COOKIES_FILE = 'cookies.pkl'
COMMENTS_FILE = 'comments.txt'
USE_LIKE = True
MAX_WAIT_TIME = 15 # Thời gian chờ tối đa cho element

# ====== Hàm khởi tạo Chrome ======
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-notifications')
    options.add_argument("--start-maximized")
    # options.add_argument("--headless") # Chạy ẩn danh (có thể dễ bị phát hiện hơn)
    # options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# ====== Đọc bình luận từ file ======
def load_comments():
    if os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE, 'r', encoding='utf-8') as f:
            comments = [line.strip() for line in f if line.strip()]
            if not comments:
                print("File comments.txt rỗng.")
                return []
            return comments
    else:
        print(f"Không tìm thấy file {COMMENTS_FILE}.")
        return []

# ====== Đăng nhập bằng email/pass ======
def facebook_login(driver, wait, email, password):
    driver.get("https://www.facebook.com/login")
    try:
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = wait.until(EC.presence_of_element_located((By.ID, "pass")))

        email_input.send_keys(email)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)

        # Chờ trang chuyển hướng sau khi đăng nhập, ví dụ chờ 1 element trên trang chủ
        wait.until(EC.url_contains("facebook.com")) # Hoặc chờ một element cụ thể trên trang chủ
        # Ví dụ: wait.until(EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Home']")))
        time.sleep(random.uniform(3,5)) # Chờ thêm một chút cho trang ổn định

        save_cookies(driver)
        print("Đã đăng nhập bằng email/password và lưu cookies.")
        return True
    except TimeoutException:
        print("Lỗi: Không tìm thấy ô email/password hoặc trang không tải kịp.")
        return False
    except Exception as e:
        print(f"Lỗi không xác định khi đăng nhập: {e}")
        return False

# ====== Lưu và nạp cookie ======
def save_cookies(driver):
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)
    print("Cookies đã được lưu.")

def load_cookies(driver, wait):
    if not os.path.exists(COOKIES_FILE):
        print("Không tìm thấy file cookies.")
        return False
    
    driver.get("https://www.facebook.com/") # Phải vào domain trước khi add cookie
    time.sleep(random.uniform(1,2))

    with open(COOKIES_FILE, 'rb') as f:
        cookies = pickle.load(f)
    
    if not cookies:
        print("File cookies rỗng.")
        return False

    for cookie in cookies:
        # Đảm bảo cookie có thuộc tính 'domain' và 'name'
        if 'domain' in cookie and 'name' in cookie:
            # Xóa domain nếu nó không khớp hoàn toàn, FB sẽ tự đặt
            if cookie['domain'].startswith('.'):
                 cookie['domain'] = cookie['domain'][1:] # Bỏ dấu chấm ở đầu
            try:
                driver.add_cookie(cookie)
            except InvalidCookieDomainException:
                print(f"Bỏ qua cookie không hợp lệ cho domain: {cookie.get('name')}")
            except Exception as e:
                print(f"Lỗi khi thêm cookie {cookie.get('name')}: {e}")
        else:
            print(f"Cookie không hợp lệ, thiếu 'domain' hoặc 'name': {cookie}")


    driver.get("https://www.facebook.com/") # Tải lại trang để cookie có hiệu lực
    
    # Kiểm tra đăng nhập thành công bằng cách tìm một element chỉ có khi đã login
    try:
        # Tìm một element đặc trưng của trang đã đăng nhập, ví dụ nút "Trang chủ" hoặc avatar
        # Selector này cần được kiểm tra và cập nhật thường xuyên
        wait.until(EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Trang chủ' or @aria-label='Home']")))
        print("Đăng nhập thành công bằng cookies.")
        return True
    except TimeoutException:
        print("Không thể xác nhận đăng nhập bằng cookies (có thể cookies đã hết hạn).")
        return False


def go_to_post(driver, wait, post_url):
    driver.get(post_url)
    time.sleep(3)

    # Scroll để load DOM đầy đủ
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    try:
        # Click vào ô để hiện hộp nhập bình luận
        comment_trigger = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//div[@aria-label='Viết bình luận công khai...' or @aria-label='Write a public comment...']"
        )))
        comment_trigger.click()
    except TimeoutException:
        print("❌ Không tìm thấy nút kích hoạt comment.")
        return

    try:
        # Tìm ô nhập và comment
        comment_box = wait.until(EC.presence_of_element_located((
            By.XPATH, "//div[@role='textbox']"
        )))
        comment_box.send_keys("Test comment từ script", Keys.ENTER)
        print("✅ Bình luận thành công.")
    except TimeoutException:
        print("❌ Không tìm thấy ô nhập bình luận.")

# ====== Like bài viết ======
def like_post(driver, wait):
    # Selector cho nút Like có thể rất phức tạp và thay đổi thường xuyên
    # Đây là một ví dụ, bạn cần kiểm tra và cập nhật nó
    # Có thể tìm theo data-testid nếu có, hoặc cấu trúc HTML
    # Ưu tiên tìm nút chưa được nhấn (chưa có "Bỏ thích")
    like_button_xpath = "//div[@aria-label='Thích' or @aria-label='Like']" # Hoặc "//div[contains(@aria-label,'Thích') and not(contains(@aria-label,'Bỏ thích'))]"
    
    try:
        like_button = wait.until(EC.element_to_be_clickable((By.XPATH, like_button_xpath)))
        # Kiểm tra xem đã like chưa bằng cách xem text của nó hoặc aria-label của nút cha
        # Cách đơn giản là cứ click, nếu nó đã like rồi thì Facebook xử lý, hoặc nó sẽ thành unlike
        # Để chắc chắn, có thể tìm nút "Bỏ thích" (Unlike)
        # unlike_button_xpath = "//div[@aria-label='Bỏ thích' or @aria-label='Unlike']"
        # if not driver.find_elements(By.XPATH, unlike_button_xpath): # Nếu không tìm thấy nút Bỏ thích
        #     like_button.click()
        #     print("Đã like bài viết.")
        # else:
        #     print("Bài viết đã được like trước đó.")
        like_button.click() # Click trực tiếp
        print("Đã thực hiện hành động Like/Unlike.") # FB sẽ tự toggle
        time.sleep(random.uniform(1,3))
    except TimeoutException:
        print("Không tìm thấy nút like hoặc không thể click.")
    except Exception as e:
        print(f"Lỗi khi like bài viết: {e}")

# ====== Đăng bình luận ======
def post_comment(driver, wait, comment_text):
    try:
        # Selector này cần rất cẩn thận, Facebook thay đổi thường xuyên
        comment_area_xpath = "//form//div[@aria-label='Viết bình luận công khai...' or @aria-label='Write a public comment...']"
        comment_area = wait.until(EC.element_to_be_clickable((By.XPATH, comment_area_xpath)))
        
        # Click để focus, sau đó gõ
        comment_area.click() 
        time.sleep(random.uniform(0.5, 1.5)) # Chờ một chút sau khi click

        # Gõ từng ký tự để giống người hơn (tùy chọn, làm script chậm hơn)
        # for char in comment_text:
        #     comment_area.send_keys(char)
        #     time.sleep(random.uniform(0.05, 0.15))
        comment_area.send_keys(comment_text)
        time.sleep(random.uniform(0.5, 1.5)) # Chờ một chút sau khi gõ

        # Tìm nút gửi bình luận (Post/Đăng)
        # Selector này cũng rất dễ thay đổi
        submit_button_xpath = "//form//button[@type='submit' and (contains(@aria-label, 'Đăng') or contains(@aria-label, 'Post') or contains(@aria-label, 'Comment'))]"
        # Hoặc có thể là một button không có text nhưng có icon mũi tên gửi
        # submit_button_xpath = "//div[@aria-label='Viết bình luận công khai...']/ancestor::form//div[@aria-label='Đăng' or @aria-label='Post']"
        
        # Thử tìm nút gửi trong ngữ cảnh form của comment_area
        # form_element = comment_area.find_element(By.XPATH, "./ancestor::form")
        # submit_button = form_element.find_element(By.XPATH, ".//button[@type='submit']") # Tìm button submit trong form đó

        # Cách an toàn hơn là dựa vào Keys.ENTER nếu không có nút submit rõ ràng và ô comment là dạng input chuẩn
        # comment_area.send_keys(Keys.ENTER) # Hoặc Keys.RETURN
        # Tuy nhiên, Facebook thường có nút submit
        
        # Tìm submit button dựa trên XPATH
        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, submit_button_xpath)))
        submit_button.click()
        print(f"Đã gửi bình luận: {comment_text}")
        return True

    except TimeoutException:
        print(f"Lỗi: Không tìm thấy ô bình luận hoặc nút gửi cho: {comment_text}")
        return False
    except Exception as e:
        print(f"Lỗi không xác định khi gửi bình luận '{comment_text}': {e}")
        # Chụp ảnh màn hình khi có lỗi để debug
        # driver.save_screenshot(f"error_commenting_{time.time()}.png")
        return False


# ====== Workflow chính ======
def run_comment_workflow():
    driver = None # Khởi tạo driver là None
    try:
        driver = init_driver()
        wait = WebDriverWait(driver, MAX_WAIT_TIME)

        # Đăng nhập (ưu tiên cookie)
        if not load_cookies(driver, wait):
            print("Thử đăng nhập bằng email/password...")
            if not facebook_login(driver, wait, EMAIL, PASSWORD):
                print("Đăng nhập thất bại. Thoát.")
                return # Không return ở đây nếu muốn driver.quit() ở finally
        
        # Kiểm tra lại xem có thực sự đăng nhập thành công không
        # Bằng cách truy cập trang cá nhân hoặc một trang yêu cầu login
        driver.get("https://www.facebook.com/me")
        time.sleep(random.uniform(2,4))
        if "login" in driver.current_url.lower():
            print("Đăng nhập không thành công hoặc session hết hạn. Vui lòng kiểm tra lại.")
            return

        # Chuyển tới bài viết
        go_to_post(driver, wait, POST_URL)

        # Like nếu cần
        if USE_LIKE:
            like_post(driver, wait)

        # Đọc comment
        comments = load_comments()
        if not comments:
            print("Không có bình luận nào để đăng.")
            return # Không return ở đây nếu muốn driver.quit() ở finally

        # Đăng bình luận
        for idx, comment in enumerate(comments):
            print(f"Chuẩn bị đăng bình luận [{idx+1}/{len(comments)}]: {comment}")
            success = post_comment(driver, wait, comment)
            if success:
                print(f"[{idx+1}] Bình luận thành công.")
            else:
                print(f"[{idx+1}] Bình luận thất bại.")
                # Có thể thêm logic thử lại hoặc bỏ qua

            # Thời gian chờ giữa các bình luận
            # Nên có khoảng nghỉ dài hơn sau một số lượng comment nhất định
            if (idx + 1) % 5 == 0: # Sau mỗi 5 comments, nghỉ dài hơn
                 delay = random.uniform(60, 180)
                 print(f"Đã đăng {idx+1} bình luận. Nghỉ dài {delay:.0f} giây...")
            else:
                delay = random.uniform(15, 45) # Thời gian chờ giữa các comment (giây)
            
            print(f"Đợi {delay:.0f} giây trước khi đăng bình luận tiếp theo...")
            time.sleep(delay)
            
            # Tùy chọn: Làm mới trang sau một số bình luận để tránh lỗi giao diện
            if (idx + 1) % 10 == 0:
                print("Làm mới trang...")
                driver.refresh()
                time.sleep(random.uniform(5,10))
                # Sau khi refresh, cần chờ trang tải lại và có thể phải tìm lại ô comment
                go_to_post(driver, wait, POST_URL) # Quay lại bài post và chờ element

        print("Hoàn tất quá trình đăng bình luận.")

    except Exception as e:
        print(f"Lỗi nghiêm trọng trong workflow: {e}")
        if driver:
            driver.save_screenshot(f"critical_error_{time.time()}.png")
    finally:
        if driver:
            print("Đóng trình duyệt...")
            driver.quit()


# ====== Chạy script ======
if __name__ == '__main__':
    if not EMAIL or EMAIL == 'your_email_here' or not PASSWORD or PASSWORD == 'your_password_here':
        print("Vui lòng cấu hình EMAIL và PASSWORD trong script.")
    elif not POST_URL or 'xxx' in POST_URL:
        print("Vui lòng cấu hình POST_URL cho bài viết cụ thể.")
    else:
        run_comment_workflow()