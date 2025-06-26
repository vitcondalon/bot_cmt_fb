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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidCookieDomainException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# ====== Cấu hình ======
EMAIL = 'vietledepchoai@gmail.com'
PASSWORD = 'kandethuong2005'
POST_URL = 'https://www.facebook.com/l.t.viet.695531/posts/pfbid0xBeLw6rz5wTkADBi7dNw9uCXAm9Xvy8bMotKqzUo9fTPCsk9BgqmfJjeZ8qszkPPl?rdid=vdDlpAKxwZI9Yl5O#'

COOKIES_FILE = 'cookies.pkl'
COMMENTS_FILE = 'comments.txt' # QUAN TRỌNG: KHÔNG CHỨA EMOJI
USE_LIKE = True
MAX_WAIT_TIME = 20
SHORT_WAIT_TIME = 10

# ====== Hàm khởi tạo Chrome ======
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-notifications')
    options.add_argument("--start-maximized")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option("useAutomationExtension", False)
    try:
        print("Đang khởi tạo ChromeDriver...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("ChromeDriver đã khởi tạo thành công.")
        return driver
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi khởi tạo ChromeDriver: {e}")
        return None

# ====== Đọc bình luận từ file ======
def load_comments():
    if not os.path.exists(COMMENTS_FILE):
        print(f"Lỗi: Không tìm thấy file {COMMENTS_FILE}.")
        return []
    with open(COMMENTS_FILE, 'r', encoding='utf-8') as f:
        comments = [line.strip() for line in f if line.strip()]
    if not comments:
        print(f"File {COMMENTS_FILE} rỗng hoặc không có bình luận hợp lệ.")
    return comments

# ====== Đăng nhập bằng email/pass ======
def facebook_login(driver, wait, email, password):
    print("Đang thử đăng nhập bằng Email/Password...")
    driver.get("https://www.facebook.com/login")
    try:
        email_input = wait.until(EC.visibility_of_element_located((By.ID, "email")))
        password_input = wait.until(EC.visibility_of_element_located((By.ID, "pass")))
        email_input.send_keys(email)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
        WebDriverWait(driver, MAX_WAIT_TIME).until(
            lambda d: "facebook.com" in d.current_url and "login" not in d.current_url and "checkpoint" not in d.current_url
        )
        time.sleep(random.uniform(2, 4))
        save_cookies(driver)
        print("Đã đăng nhập bằng Email/Password và lưu cookies.")
        return True
    except TimeoutException:
        print("Lỗi Timeout: Không tìm thấy ô email/password hoặc trang không tải/chuyển hướng kịp sau khi đăng nhập.")
        driver.save_screenshot(f"error_login_timeout_{time.time()}.png")
        return False
    except Exception as e:
        print(f"Lỗi không xác định khi đăng nhập bằng Email/Password: {e}")
        driver.save_screenshot(f"error_login_unknown_{time.time()}.png")
        return False

# ====== Lưu và nạp cookie ======
def save_cookies(driver):
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)
    print(f"Cookies đã được lưu vào file: {COOKIES_FILE}")

def load_cookies(driver, wait):
    if not os.path.exists(COOKIES_FILE):
        print(f"Không tìm thấy file cookies: {COOKIES_FILE}")
        return False
    print(f"Đang tải cookies từ file: {COOKIES_FILE}...")
    driver.get("https://www.facebook.com/")
    time.sleep(random.uniform(0.5, 1.5))
    with open(COOKIES_FILE, 'rb') as f:
        cookies = pickle.load(f)
    if not cookies:
        print("File cookies rỗng.")
        return False
    for cookie in cookies:
        if 'domain' in cookie and cookie['domain'].startswith('.'):
            cookie['domain'] = cookie['domain'][1:]
        try:
            driver.add_cookie(cookie)
        except InvalidCookieDomainException: pass
        except Exception as e: print(f"  Lỗi khi thêm cookie '{cookie.get('name')}': {e}")
    print("Đã thêm cookies vào trình duyệt. Đang tải lại trang Facebook...")
    driver.get("https://www.facebook.com/me")
    try:
        WebDriverWait(driver, SHORT_WAIT_TIME).until_not(
            lambda d: "login" in d.current_url.lower() or "checkpoint" in d.current_url.lower()
        )
        if "login" in driver.current_url.lower() or "checkpoint" in driver.current_url.lower():
             print("Cookie không hợp lệ hoặc đã hết hạn (bị chuyển hướng đến trang login/checkpoint).")
             driver.save_screenshot(f"error_cookie_login_redirect_{time.time()}.png")
             return False
        print("Đăng nhập thành công bằng cookies (đã kiểm tra /me).")
        return True
    except TimeoutException:
        print("Không thể xác nhận đăng nhập bằng cookies (trang /me không tải kịp hoặc vẫn ở trang login/checkpoint).")
        driver.save_screenshot(f"error_cookie_login_timeout_or_redirected_{time.time()}.png")
        return False

# ====== Truy cập bài viết ======
def go_to_post(driver, wait, post_url):
    print(f"Đang truy cập bài viết: {post_url}")
    driver.get(post_url)
    try:
        post_indicator_xpaths = [
            "//div[@role='textbox' and (contains(@aria-label, 'comment') or contains(@aria-label, 'bình luận'))]",
            "//div[@role='article']",
            "//form[.//div[contains(@aria-label, 'Viết bình luận') or contains(@aria-label, 'Write a comment')]]"
        ]
        loaded_indicator = None
        print("  Đang chờ nội dung bài viết tải...")
        for idx, xpath in enumerate(post_indicator_xpaths):
            try:
                loaded_indicator = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                if loaded_indicator:
                    print(f"  ==> Đã tìm thấy chỉ báo tải bài viết với XPath: {xpath}")
                    break
            except TimeoutException: pass
        if not loaded_indicator:
            raise TimeoutException("Không tìm thấy chỉ báo tải bài viết sau khi thử các XPath.")
        print("  Đã tải xong nội dung bài viết (hoặc ít nhất là một phần quan trọng).")
        time.sleep(random.uniform(1,2))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
        time.sleep(0.5)
    except TimeoutException as e:
        print(f"Lỗi Timeout: Không thể tải hoặc tìm thấy nội dung chính của bài viết tại {post_url}.")
        driver.save_screenshot(f"error_goto_post_timeout_{time.time()}.png")
        raise
    except Exception as e:
        print(f"Lỗi không xác định khi truy cập bài viết: {e}")
        driver.save_screenshot(f"error_goto_post_unknown_{time.time()}.png")
        raise

# ====== Like bài viết ======
def like_post(driver, wait):
    like_button_xpaths = [
        "//div[@role='button' and (@aria-label='Thích' or @aria-label='Like') and not(contains(@aria-label, 'Bỏ thích') or contains(@aria-label, 'Unlike'))]",
        "//div[@role='button' and @aria-label='Thích']",
        "//div[@role='button' and @aria-label='Like']",
        "//div[@data-testid='UFI2ReactionLink']"
    ]
    like_button = None
    print("  Đang tìm nút Like...")
    for idx, xpath in enumerate(like_button_xpaths):
        try:
            potential_button = WebDriverWait(driver, SHORT_WAIT_TIME).until(EC.presence_of_element_located((By.XPATH, xpath)))
            current_label = potential_button.get_attribute("aria-label")
            if current_label and ("Bỏ thích" in current_label or "Unlike" in current_label):
                print("  Bài viết đã được thích trước đó.")
                return
            like_button = WebDriverWait(driver, SHORT_WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            if like_button:
                print(f"  ==> Tìm thấy nút Like với XPath: {xpath}")
                break
        except TimeoutException: pass
        except Exception: pass
    if not like_button:
        print("  Không tìm thấy nút Like nào phù hợp sau khi thử các XPath.")
        driver.save_screenshot(f"error_like_not_found_{time.time()}.png")
        return
    try:
        print("  Đang thực hiện hành động Like...")
        driver.execute_script("arguments[0].click();", like_button)
        print("  Đã thực hiện hành động Like.")
        time.sleep(random.uniform(1,2))
    except ElementClickInterceptedException as eci:
        print(f"  Lỗi ElementClickInterceptedException khi like: {eci}")
        driver.save_screenshot(f"error_like_intercepted_{time.time()}.png")
    except Exception as e:
        print(f"  Lỗi không xác định khi like bài viết: {e}")
        driver.save_screenshot(f"error_like_unknown_{time.time()}.png")

# ====== Đăng bình luận ======
def post_comment(driver, wait, comment_text):
    try:
        comment_area_xpaths = [
            "//div[@role='textbox' and @aria-label='Viết bình luận…']",
            "//div[@role='textbox' and @aria-label='Write a comment…']",
            "//div[@role='textbox' and (contains(@aria-label, 'bình luận') or contains(@aria-label, 'comment'))]",
            "//div[@role='textbox' and @data-lexical-editor='true']",
        ]
        comment_area = None
        print("  Đang tìm ô bình luận (placeholder)...")
        for idx, xpath in enumerate(comment_area_xpaths):
            try:
                comment_area = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                if comment_area:
                    print(f"  ==> Tìm thấy ô bình luận (placeholder) với XPath: {xpath}")
                    break
            except TimeoutException: pass
        
        if not comment_area:
            print(f"  Lỗi: Không tìm thấy ô bình luận (placeholder) nào phù hợp cho: '{comment_text[:30]}...'")
            driver.save_screenshot(f"error_comment_area_placeholder_not_found_{time.time()}.png")
            return False

        actions = ActionChains(driver)
        actions.move_to_element(comment_area).click().perform()
        time.sleep(random.uniform(0.3, 0.7))

        focused_element = driver.switch_to.active_element
        
        print(f"  Đang gõ bình luận vào element đang focus: '{comment_text[:30]}...'")
        focused_element.send_keys(Keys.CONTROL + "a")
        focused_element.send_keys(Keys.DELETE)
        time.sleep(0.1)

        for char_idx, char_code in enumerate(comment_text):
            focused_element.send_keys(char_code)
            if char_idx < 5: time.sleep(random.uniform(0.01, 0.05))
        time.sleep(random.uniform(0.2, 0.4))

        # === CẬP NHẬT XPATH CHO NÚT GỬI DỰA TRÊN THÔNG TIN MỚI NHẤT ===
        # Giả định: Nút gửi thực sự có thể có aria-label="Bình luận" HOẶC "Comment",
        # và có thể có tabindex="0" (dựa trên HTML bạn gửi gần nhất cho nút gửi)
        # hoặc tabindex="-1" (dựa trên HTML bạn gửi trước đó cho nút gửi).
        # Class icon có thể là 'xi3auck' (từ HTML gần nhất) hoặc 'xmgbrsx' (từ HTML trước đó).
        submit_button_xpaths = [
            # Ưu tiên 1: Tìm div[role="button"] với label "Bình luận" hoặc "Comment",
            # không disabled, trong form, và có icon với class chứa 'xi3auck' (từ HTML mới nhất bạn gửi)
            "//div[@role='textbox' and (contains(@aria-label, 'Viết bình luận') or contains(@aria-label, 'Write a comment'))]/ancestor::form[1]//div[@role='button' and (@aria-label='Bình luận' or @aria-label='Comment') and (not(@aria-disabled='true') or @aria-disabled='false') and .//i[contains(@class, 'xi3auck')]]",

            # Ưu tiên 2: Tương tự Ưu tiên 1, nhưng với class icon 'xmgbrsx' (từ HTML trước đó của nút gửi)
            "//div[@role='textbox' and (contains(@aria-label, 'Viết bình luận') or contains(@aria-label, 'Write a comment'))]/ancestor::form[1]//div[@role='button' and (@aria-label='Bình luận' or @aria-label='Comment') and (not(@aria-disabled='true') or @aria-disabled='false') and .//i[contains(@class, 'xmgbrsx')]]",
            
            # Ưu tiên 3: Dựa vào tabindex="-1" và label "Comment" (nếu thông tin cũ về tabindex="-1" cho nút gửi là đúng)
            "//div[@role='button' and @aria-label='Comment' and @tabindex='-1' and (not(@aria-disabled='true') or @aria-disabled='false')]",

            # Ưu tiên 4: Dựa vào tabindex="-1" và label "Bình luận"
            "//div[@role='button' and @aria-label='Bình luận' and @tabindex='-1' and (not(@aria-disabled='true') or @aria-disabled='false')]",

            # Ưu tiên 5: Chỉ dựa vào tabindex="-1" và có icon <i> (ít cụ thể hơn)
            "//div[@role='button' and @tabindex='-1' and (not(@aria-disabled='true') or @aria-disabled='false') and .//i]",
        ]
        submit_button = None
        print("  Đang tìm nút gửi bình luận...")
        for idx, xpath in enumerate(submit_button_xpaths):
            try:
                print(f"    Thử tìm nút gửi với XPath [{idx+1}]: {xpath}")
                submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                if submit_button:
                    print(f"    ==> Tìm thấy nút gửi với XPath: {xpath}")
                    break
            except TimeoutException:
                print(f"        Không tìm thấy nút gửi với XPath (hoặc không clickable): {xpath}")
        
        if not submit_button:
            print(f"  Lỗi: Không tìm thấy nút gửi bình luận (hoặc nút không clickable sau khi thử các XPath).")
            driver.save_screenshot(f"error_comment_submit_not_found_{time.time()}.png")
            return False

        print("  Đang click nút gửi...")
        try:
            driver.execute_script("arguments[0].click();", submit_button)
            print(f"  Đã gửi bình luận: '{comment_text[:30]}...'")
            time.sleep(random.uniform(1.5, 2.5))
            return True
        except Exception as e_click:
            print(f"  Lỗi khi click nút gửi: {e_click}")
            driver.save_screenshot(f"error_comment_submit_click_failed_{time.time()}.png")
            return False

    except TimeoutException as e:
        print(f"Lỗi Timeout trong hàm post_comment: {e}")
        driver.save_screenshot(f"error_comment_timeout_func_{time.time()}.png")
        return False
    except ElementClickInterceptedException as eci:
        print(f"Lỗi ElementClickInterceptedException trong post_comment: {eci}")
        driver.save_screenshot(f"error_comment_intercepted_func_{time.time()}.png")
        return False
    except Exception as e:
        if "ChromeDriver only supports characters in the BMP" in str(e):
            print(f"LỖI GỬI BÌNH LUẬN (CÓ THỂ DO EMOJI): '{comment_text[:30]}...'. Lỗi: {e}")
            print("    VUI LÒNG LOẠI BỎ EMOJI KHỎI FILE comments.txt")
        else:
            print(f"Lỗi không xác định khi gửi bình luận '{comment_text[:30]}...': {e}")
        driver.save_screenshot(f"error_comment_unknown_func_{time.time()}.png")
        return False

# ====== Workflow chính ======
def run_comment_workflow():
    driver = None
    try:
        driver = init_driver()
        if not driver:
            print("Không thể khởi tạo trình duyệt. Thoát.")
            return

        wait = WebDriverWait(driver, MAX_WAIT_TIME)

        if not load_cookies(driver, wait):
            print("Không thể đăng nhập bằng cookies. Thử đăng nhập bằng Email/Password...")
            if not facebook_login(driver, wait, EMAIL, PASSWORD):
                print("Đăng nhập bằng Email/Password thất bại. Thoát.")
                return
        
        driver.get("https://www.facebook.com/me")
        time.sleep(random.uniform(1,2))
        if "login" in driver.current_url.lower() or "checkpoint" in driver.current_url.lower():
            print("Xác nhận đăng nhập cuối cùng không thành công (bị chuyển hướng). Vui lòng kiểm tra lại tài khoản hoặc cookies.")
            driver.save_screenshot(f"error_final_login_check_failed_{time.time()}.png")
            return
        print("Xác nhận đã đăng nhập thành công vào Facebook.")

        go_to_post(driver, wait, POST_URL)

        if USE_LIKE:
            print("\nTiến hành like bài viết...")
            like_post(driver, wait)

        comments = load_comments()
        if not comments:
            print("Không có bình luận nào để đăng từ file comments.txt.")
            return

        print(f"\nBắt đầu đăng {len(comments)} bình luận...")
        successful_comments = 0
        failed_comments = 0

        for idx, comment in enumerate(comments):
            print(f"\n--- Chuẩn bị đăng bình luận [{idx+1}/{len(comments)}]: '{comment[:40].strip()}...' ---")
            try:
                success = post_comment(driver, wait, comment)
                if success:
                    print(f"    ==> [{idx+1}] Bình luận THÀNH CÔNG.")
                    successful_comments += 1
                else:
                    print(f"    ==> [{idx+1}] Bình luận THẤT BẠI.")
                    failed_comments += 1
            except Exception as e_main_loop_comment:
                print(f"    Lỗi không mong muốn khi gọi post_comment cho bình luận [{idx+1}]: {e_main_loop_comment}")
                failed_comments += 1
                driver.save_screenshot(f"error_main_loop_post_comment_call_{idx+1}_{time.time()}.png")

            if (idx + 1) < len(comments):
                base_delay = random.uniform(15, 35)
                if (idx + 1) % 5 == 0 :
                     long_delay_multiplier = random.uniform(2.0, 3.5)
                     delay = base_delay * long_delay_multiplier
                     print(f"    Đã đăng {idx+1} bình luận. Nghỉ dài {delay:.0f} giây...")
                else:
                    delay = base_delay
                    print(f"    Đợi {delay:.0f} giây trước khi đăng bình luận tiếp theo...")
                time.sleep(delay)
            
                if (idx + 1) % 10 == 0:
                    print("    Làm mới trang và quay lại bài viết...")
                    current_url_before_refresh = driver.current_url
                    try:
                        driver.refresh()
                        WebDriverWait(driver, MAX_WAIT_TIME).until(EC.staleness_of(driver.find_element(By.TAG_NAME, "body")))
                        time.sleep(random.uniform(3,6))
                        target_url_after_refresh = current_url_before_refresh if "facebook.com/posts/" in current_url_before_refresh else POST_URL
                        go_to_post(driver, wait, target_url_after_refresh)
                    except Exception as e_refresh:
                        print(f"    Lỗi khi tải lại bài viết sau khi refresh: {e_refresh}")
                        print("    Thử tiếp tục mà không đảm bảo đã quay lại đúng bài viết...")
                        driver.get(POST_URL)
                        time.sleep(3)

        print("\n===== HOÀN TẤT QUÁ TRÌNH ĐĂNG BÌNH LUẬN =====")
        print(f"Tổng số bình luận đã xử lý: {len(comments)}")
        print(f"Thành công: {successful_comments}")
        print(f"Thất bại: {failed_comments}")

    except Exception as e:
        print(f"Lỗi nghiêm trọng không mong muốn trong workflow chính: {e}")
        if driver: driver.save_screenshot(f"critical_error_main_workflow_{time.time()}.png")
    finally:
        if driver:
            print("\nĐang chờ để đóng trình duyệt...")
            input("Nhấn Enter để đóng trình duyệt...") 
            driver.quit()
            print("Trình duyệt đã đóng.")

# ====== Chạy script ======
if __name__ == '__main__':
    if not EMAIL or 'your_email_here' in EMAIL or not PASSWORD or 'your_password_here' in PASSWORD:
        print("!!! CẤU HÌNH LỖI: Vui lòng đặt EMAIL và PASSWORD của bạn trong script.")
    elif not POST_URL or 'xxx' in POST_URL or not POST_URL.startswith("https://www.facebook.com/"):
        print("!!! CẤU HÌNH LỖI: Vui lòng đặt POST_URL hợp lệ cho bài viết Facebook.")
    else:
        if not os.path.exists(COMMENTS_FILE):
            print(f"File {COMMENTS_FILE} không tồn tại. Đang tạo file mẫu...")
            with open(COMMENTS_FILE, 'w', encoding='utf-8') as f:
                f.write("Binh luan mau 1 (khong dung emoji).\n")
                f.write("Binh luan mau 2.\n")
            print(f"Đã tạo file {COMMENTS_FILE} với bình luận mẫu. Hãy chỉnh sửa file này.")
        
        run_comment_workflow()