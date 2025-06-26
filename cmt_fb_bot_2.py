# --- KHAI BÁO THƯ VIỆN ---
from selenium import webdriver  # Thư viện chính để tự động hóa trình duyệt
from selenium.webdriver.common.by import By  # Cách để tìm element (theo ID, XPATH, NAME,...)
from selenium.webdriver.common.keys import Keys  # Cho phép gửi các phím đặc biệt (Enter, Tab,...)
from selenium.webdriver.chrome.service import Service  # Dịch vụ để chạy ChromeDriver
from selenium.webdriver.support.ui import WebDriverWait  # Cơ chế chờ đợi thông minh
from selenium.webdriver.support import expected_conditions as EC  # Các điều kiện cụ thể để chờ (element xuất hiện, click được,...)
import time  # Thư viện để quản lý thời gian (delay, sleep)
import random  # Thư viện để tạo số ngẫu nhiên (cho delay, chọn comment)
import getpass  # Thư viện để ẩn mật khẩu khi người dùng nhập từ terminal
from urllib.parse import urlparse, parse_qs # Thư viện để phân tích và xử lý URL

# --- HÀM XỬ LÝ LINK FACEBOOK ---
def get_actual_post_url(driver_instance, initial_url):
    """
    Mục đích: Cố gắng lấy URL bài viết gốc từ một link Facebook (có thể là link chia sẻ, link rút gọn).
    Cách hoạt động:
    1. Kiểm tra nếu là link dạng sharer.php, trích xuất URL gốc từ tham số 'u'.
    2. Truy cập URL đã trích xuất hoặc URL ban đầu.
    3. Chờ trang tải và có thể chuyển hướng.
    4. Lấy URL hiện tại của trình duyệt (driver.current_url) - đây là URL cuối cùng sau mọi chuyển hướng.
    5. Cố gắng "làm sạch" URL cuối cùng bằng cách loại bỏ các tham số theo dõi không cần thiết.
    Input:
        - driver_instance: Đối tượng WebDriver đã được khởi tạo và đăng nhập.
        - initial_url: Link Facebook ban đầu do người dùng nhập.
    Output:
        - URL bài viết đã được xử lý (hy vọng là link trực tiếp đến bài viết).
    """
    print(f"Đang xử lý URL đầu vào: {initial_url}")
    parsed_url = urlparse(initial_url) # Phân tích URL thành các thành phần (scheme, netloc, path, query,...)

    # Trường hợp 1: Link chia sẻ dạng sharer.php (ví dụ: facebook.com/sharer/sharer.php?u=URL_GOC)
    if "facebook.com/sharer/sharer.php" in initial_url:
        query_params = parse_qs(parsed_url.query) # Lấy các tham số query (ví dụ: {'u': ['URL_GOC']})
        if 'u' in query_params and query_params['u']: # Kiểm tra xem có tham số 'u' không
            actual_url_from_sharer = query_params['u'][0] # Lấy giá trị của 'u'
            print(f"Link chia sẻ dạng sharer.php, URL gốc tiềm năng: {actual_url_from_sharer}")
            try:
                # Thử truy cập URL gốc này để xem nó có chuyển hướng tiếp không
                driver_instance.get(actual_url_from_sharer)
                time.sleep(random.uniform(2, 4)) # Chờ trang tải và có thể chuyển hướng
                final_url_after_sharer_redirect = driver_instance.current_url # Lấy URL cuối cùng
                print(f"URL cuối cùng sau khi truy cập link gốc từ sharer: {final_url_after_sharer_redirect}")
                # Sau khi lấy được URL từ sharer, tiếp tục xử lý "làm sạch" nó ở phần dưới
                initial_url = final_url_after_sharer_redirect # Cập nhật initial_url để xử lý tiếp
            except Exception as e:
                print(f"Lỗi khi thử truy cập URL từ sharer ('{actual_url_from_sharer}'): {e}. Sẽ thử dùng URL sharer ban đầu.")
                # Nếu lỗi, initial_url vẫn là link sharer ban đầu, sẽ được xử lý ở khối try-except dưới
                pass

    # Trường hợp 2 (hoặc sau khi xử lý sharer): Truy cập URL (có thể đã được cập nhật) và lấy URL cuối cùng
    try:
        print(f"Thử truy cập URL để lấy link cuối cùng: {initial_url}")
        driver_instance.get(initial_url)
        # Chờ một chút để Facebook có thể thực hiện chuyển hướng hoàn tất (nếu có)
        # Thời gian này quan trọng, đặc biệt nếu link ban đầu cần nhiều bước chuyển hướng.
        time.sleep(random.uniform(3, 6)) # Có thể cần tăng nếu mạng chậm hoặc trang phức tạp
        
        final_url = driver_instance.current_url # Lấy URL hiện tại của trình duyệt
        print(f"URL cuối cùng sau khi truy cập và chờ chuyển hướng: {final_url}")
        
        # Đôi khi, sau khi truy cập link gốc từ sharer, nó lại redirect về một link sharer khác.
        # Nếu final_url vẫn là link sharer và initial_url ban đầu không phải, thì có thể có vấn đề.
        if "facebook.com/sharer/sharer.php" in final_url and "facebook.com/sharer/sharer.php" not in parsed_url.geturl(): # So sánh với initial_url trước khi nó có thể bị thay đổi
            print("Cảnh báo: URL cuối cùng vẫn là link sharer, có thể có lỗi chuyển hướng. Sử dụng URL đã qua xử lý sharer (nếu có) hoặc URL gốc ban đầu.")
            # Trong trường hợp này, initial_url có thể đã là URL từ tham số 'u' của sharer, nên ta dùng nó.
            # Hoặc nếu không qua bước sharer, thì initial_url là link người dùng nhập.
            return initial_url 

        # Cố gắng "làm sạch" URL bằng cách loại bỏ các tham số theo dõi không cần thiết
        parsed_final_url = urlparse(final_url)
        clean_query_parts = []
        # Danh sách các tham số query quan trọng cần giữ lại (có thể cần bổ sung)
        important_params = ['story_fbid', 'id', 'v', 'set', 'fbid', 'viewtype', 'post_id', 'photo_id'] 
        
        final_query_params = parse_qs(parsed_final_url.query)
        for key, value in final_query_params.items():
            # Giữ lại các tham số quan trọng hoặc các tham số liên quan đến comment/reply
            if key in important_params or "comment_id" in key or "reply_comment_id" in key:
                clean_query_parts.append(f"{key}={value[0]}") # Lấy giá trị đầu tiên của tham số
        
        clean_query_string = "&".join(clean_query_parts) # Ghép lại thành chuỗi query
        
        # Tạo lại URL đã làm sạch
        if clean_query_string:
            clean_url = f"{parsed_final_url.scheme}://{parsed_final_url.netloc}{parsed_final_url.path}?{clean_query_string}"
        else:
            clean_url = f"{parsed_final_url.scheme}://{parsed_final_url.netloc}{parsed_final_url.path}"
        
        # Loại bỏ dấu / ở cuối nếu có (trừ khi là trang chủ facebook.com/)
        if clean_url.endswith('/') and clean_url.lower().replace("https://","").replace("http://","") != "www.facebook.com":
             clean_url = clean_url.rstrip('/')

        print(f"URL đã được 'làm sạch' (nếu có thể): {clean_url}")
        return clean_url # Trả về URL đã được xử lý
        
    except Exception as e:
        print(f"Lỗi khi truy cập hoặc xử lý URL '{initial_url}': {e}. Sẽ sử dụng URL này trực tiếp.")
        return initial_url # Nếu có lỗi nghiêm trọng, trả về link ban đầu để thử

# --- CẤU HÌNH BAN ĐẦU ---
# Đường dẫn đến file chromedriver.exe trên máy của bạn.
# QUAN TRỌNG: Đảm bảo đường dẫn này chính xác và file chromedriver.exe tồn tại ở đó.
# Phiên bản ChromeDriver phải tương thích với phiên bản trình duyệt Chrome bạn đang cài.
webdriver_path = r'C:\python\chromedriver.exe'

print("--- VUI LÒNG NHẬP THÔNG TIN CẤU HÌNH ---")
# Yêu cầu người dùng nhập thông tin đăng nhập và link bài viết
FB_EMAIL = input("Nhập email Facebook của bạn: ")
FB_PASSWORD = getpass.getpass("Nhập mật khẩu Facebook của bạn (sẽ không hiển thị khi gõ): ") # getpass giúp ẩn mật khẩu
INPUT_POST_URL = input("Nhập link bài viết Facebook (có thể là link chia sẻ): ")
# Kiểm tra cơ bản xem link có bắt đầu bằng http không
while not INPUT_POST_URL.lower().startswith("http"):
    print("Link bài viết không hợp lệ. Vui lòng nhập lại (phải bắt đầu bằng http hoặc https).")
    INPUT_POST_URL = input("Nhập link bài viết Facebook (có thể là link chia sẻ): ")

# --- KHỞI TẠO WEBDRIVER ---
# Khai báo biến `actual_driver` ở phạm vi này để có thể truy cập trong khối `finally`
actual_driver = None 
try:
    # Thiết lập dịch vụ cho ChromeDriver
    service = Service(executable_path=webdriver_path)
    # Các tùy chọn cho trình duyệt Chrome
    options = webdriver.ChromeOptions()
    # Cố gắng giảm thiểu khả năng bị Facebook phát hiện là bot (không đảm bảo 100%)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # Tắt các thông báo pop-up của Chrome (ví dụ: "Chrome is being controlled by automated test software")
    options.add_argument("--disable-notifications") # Tắt thông báo của trang web
    # options.add_argument("--headless") # Bỏ comment dòng này nếu muốn chạy trình duyệt ở chế độ ẩn (không hiện giao diện)
    # options.add_argument("--log-level=3") # Giảm bớt các thông báo log của trình duyệt trên console

    # Khởi tạo đối tượng WebDriver (điều khiển trình duyệt Chrome)
    actual_driver = webdriver.Chrome(service=service, options=options)
    print("\nĐã khởi tạo trình duyệt Chrome.")
except Exception as e:
    print(f"LỖI KHỞI TẠO WEBDRIVER: {e}")
    print("Vui lòng kiểm tra lại đường dẫn webdriver_path và phiên bản Chrome/ChromeDriver.")
    exit() # Thoát script nếu không khởi tạo được driver

# --- ĐĂNG NHẬP FACEBOOK ---
try:
    print("\n--- BẮT ĐẦU QUÁ TRÌNH ĐĂNG NHẬP ---")
    # Mở trang chủ Facebook
    actual_driver.get("https://www.facebook.com")
    actual_driver.maximize_window() # Mở toàn màn hình để dễ thao tác và giống người dùng hơn

    # Tìm ô nhập email bằng ID, chờ tối đa 10 giây cho đến khi nó xuất hiện
    email_field = WebDriverWait(actual_driver, 10).until(
        EC.presence_of_element_located((By.ID, "email"))
    )
    email_field.send_keys(FB_EMAIL) # Gửi email đã nhập vào ô
    print("Đã nhập email.")
    time.sleep(random.uniform(0.5, 1.5)) # Chờ ngẫu nhiên một chút

    # Tìm ô nhập mật khẩu bằng ID
    password_field = WebDriverWait(actual_driver, 10).until(
        EC.presence_of_element_located((By.ID, "pass"))
    )
    password_field.send_keys(FB_PASSWORD) # Gửi mật khẩu đã nhập
    print("Đã nhập mật khẩu.")
    time.sleep(random.uniform(0.5, 1.5))

    # Tìm nút đăng nhập bằng NAME (selector này có thể thay đổi, cần kiểm tra lại nếu lỗi)
    login_button = WebDriverWait(actual_driver, 10).until(
        EC.element_to_be_clickable((By.NAME, "login")) # Chờ cho đến khi nút có thể click được
    )
    login_button.click() # Nhấn nút đăng nhập
    print("Đã nhấn nút đăng nhập.")

    # Chờ xác nhận đăng nhập thành công bằng cách tìm một element đặc trưng của trang chủ sau khi đăng nhập
    # Ví dụ: Nút "Trang chủ" hoặc avatar/tên người dùng. XPATH này có thể cần cập nhật.
    # Dùng `|` trong XPATH để tìm một trong hai element (nếu giao diện có thể khác nhau)
    WebDriverWait(actual_driver, 20).until( # Tăng thời gian chờ lên 20s
        EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Trang chủ' or @aria-label='Home'] | //div[contains(@aria-label,'Tài khoản của bạn')] | //span[contains(text(),'Chào mừng bạn đến với Facebook')]"))
    )
    print("Đăng nhập thành công!")

except Exception as e:
    print(f"LỖI TRONG QUÁ TRÌNH ĐĂNG NHẬP: {e}")
    print("Vui lòng kiểm tra lại email, mật khẩu, kết nối mạng, và các selector (ID, XPATH).")
    if actual_driver: actual_driver.quit() # Đóng trình duyệt nếu có lỗi
    exit() # Thoát script

# --- XỬ LÝ URL VÀ ĐIỀU HƯỚNG ĐẾN BÀI VIẾT ---
# Biến POST_URL sẽ lưu trữ link cuối cùng sau khi được xử lý bởi hàm get_actual_post_url
POST_URL = ""
try:
    print("\n--- BẮT ĐẦU XỬ LÝ LINK BÀI VIẾT VÀ COMMENT ---")
    # Gọi hàm để lấy URL bài viết thực tế, truyền driver đã đăng nhập vào
    POST_URL = get_actual_post_url(actual_driver, INPUT_POST_URL) 
    
    # Sau khi hàm get_actual_post_url chạy, driver đã ở trang cuối cùng (hy vọng là bài viết)
    # Tuy nhiên, để chắc chắn và code rõ ràng hơn, ta có thể get lại URL này
    # (Mặc dù driver.get(POST_URL) đã được gọi bên trong get_actual_post_url)
    # print(f"Đang xác nhận điều hướng đến URL bài viết đã xử lý: {POST_URL}")
     actual_driver.get(POST_URL) # Dòng này có thể không cần thiết nếu hàm trên đã điều hướng đúng

    # Chờ khu vực comment của bài viết xuất hiện để xác nhận đã tải đúng trang
    # XPATH này tìm một form chứa một div có aria-label là "Viết bình luận" hoặc "Write a comment..."
    # Đây là một cách khá phổ biến để xác định ô comment, nhưng có thể thay đổi.
    WebDriverWait(actual_driver, 30).until( 
        EC.presence_of_element_located((By.XPATH, "//form[.//div[@aria-label='Viết bình luận' or @aria-label='Write a comment...']]"))
    )
    print(f"Đã tải xong bài viết tại URL '{POST_URL}' và tìm thấy khu vực comment.")
    time.sleep(random.uniform(2, 5)) # Chờ ngẫu nhiên một chút để trang ổn định

    # --- NẠP COMMENT TỪ FILE ---
    comments_file_path = "comments.txt" # Tên file chứa danh sách comment
    loaded_comments = [] # Danh sách để lưu các comment đọc từ file

    try:
        with open(comments_file_path, "r", encoding="utf-8") as f: # Mở file ở chế độ đọc ("r") với encoding utf-8
            # Đọc từng dòng, loại bỏ khoảng trắng thừa ở đầu/cuối (strip)
            # và chỉ lấy các dòng có nội dung (không phải dòng trống)
            loaded_comments = [line.strip() for line in f if line.strip()]
        
        if not loaded_comments: # Nếu không có comment nào được nạp
            print(f"CẢNH BÁO: File '{comments_file_path}' trống hoặc không có comment hợp lệ.")
            if actual_driver: actual_driver.quit()
            exit(f"Không có comment để đăng từ file {comments_file_path}. Dừng script.")
        else:
            print(f"Đã nạp thành công {len(loaded_comments)} comment từ file '{comments_file_path}'.")
            random.shuffle(loaded_comments) # Xáo trộn thứ tự các comment để việc đăng ngẫu nhiên hơn

    except FileNotFoundError: # Xử lý lỗi nếu không tìm thấy file comments.txt
        print(f"LỖI: Không tìm thấy file comment '{comments_file_path}'. Vui lòng tạo file này trong cùng thư mục với script và điền comment vào.")
        if actual_driver: actual_driver.quit()
        exit(f"Không thể tiếp tục vì không tìm thấy file {comments_file_path}.")
    except Exception as e: # Xử lý các lỗi khác có thể xảy ra khi đọc file
        print(f"Lỗi không xác định khi đọc file comment: {e}")
        if actual_driver: actual_driver.quit()
        exit("Dừng script do lỗi đọc file comment.")

    # --- THIẾT LẬP SỐ LƯỢNG COMMENT SẼ ĐĂNG ---
    num_comments_to_post_requested = 153 # Số lượng comment bạn muốn đăng (Mục tiêu)
    
    # Số comment thực tế sẽ đăng là số nhỏ hơn giữa số yêu cầu và số comment có sẵn trong file
    num_comments_to_actually_post = min(num_comments_to_post_requested, len(loaded_comments))
    
    if num_comments_to_actually_post == 0: # Nếu không có comment nào để đăng
        print("Không có comment nào để đăng sau khi xử lý. Dừng script.")
        if actual_driver: actual_driver.quit()
        exit()
        
    print(f"Sẽ cố gắng đăng {num_comments_to_actually_post} comment.")
    
    posted_comments_count = 0 # Biến đếm số comment đã đăng thành công
    comments_available = list(loaded_comments) # Tạo một bản sao của danh sách comment để có thể xóa (pop) mà không ảnh hưởng đến `loaded_comments` gốc

    # --- VÒNG LẶP ĐĂNG COMMENT ---
    for i in range(num_comments_to_actually_post):
        if not comments_available: # Kiểm tra xem còn comment trong danh sách không
            print("\nĐã hết comment trong danh sách để đăng.")
            break # Thoát khỏi vòng lặp nếu không còn comment

        # Lấy một comment ngẫu nhiên từ danh sách còn lại và xóa nó đi khỏi danh sách
        # Điều này đảm bảo mỗi comment chỉ được dùng một lần (cho đến khi danh sách hết)
        comment_index_to_pop = random.randrange(len(comments_available))
        comment_text = comments_available.pop(comment_index_to_pop)
        
        try: # Bắt đầu khối try cho một lượt comment
            print(f"\nĐang chuẩn bị comment lần thứ {posted_comments_count + 1}/{num_comments_to_actually_post}...")
            print(f"Còn lại: {len(comments_available)} comment trong danh sách chờ.")

            # XPATH để tìm ô nhập comment. Quan trọng: XPATH này có thể thay đổi theo giao diện Facebook.
            # Nó tìm một div có aria-label là "Viết bình luận" (tiếng Việt) hoặc "Write a comment..." (tiếng Anh)
            comment_box_xpath = "//div[@aria-label='Viết bình luận' or @aria-label='Write a comment...']"
            
            # Cố gắng cuộn tới ô comment để đảm bảo nó hiển thị trên màn hình và có thể tương tác
            # Điều này có thể hữu ích nếu ô comment nằm ngoài tầm nhìn hiện tại của trình duyệt.
            try:
                target_element_for_scroll = actual_driver.find_element(By.XPATH, comment_box_xpath)
                # Thực thi JavaScript để cuộn element vào giữa màn hình
                actual_driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", target_element_for_scroll)
                time.sleep(random.uniform(0.5, 1.5)) # Chờ một chút sau khi cuộn
            except Exception as scroll_err:
                print(f"Lưu ý: Không thể cuộn tới ô comment (có thể không cần thiết hoặc XPATH sai): {scroll_err}")

            # Chờ cho đến khi ô comment có thể click được
            comment_box = WebDriverWait(actual_driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, comment_box_xpath))
            )
            
            print(f"Sẽ comment: '{comment_text}'")
            comment_box.click() # Click vào ô comment để focus
            time.sleep(random.uniform(0.5, 1.5)) # Chờ một chút sau khi click
            
            # Gửi từng ký tự của comment một để mô phỏng hành vi người dùng gõ phím
            # Điều này có thể giúp tránh bị phát hiện là bot so với việc gửi toàn bộ chuỗi một lúc.
            for char_index, char_to_send in enumerate(comment_text):
                comment_box.send_keys(char_to_send)
                # Điều chỉnh tốc độ gõ chữ: nhanh hơn một chút giữa các ký tự, chậm hơn ở ký tự cuối
                if char_index < len(comment_text) - 1 : # Nếu không phải ký tự cuối
                     time.sleep(random.uniform(0.03, 0.15)) 
                else: # Ký tự cuối
                     time.sleep(random.uniform(0.1, 0.3))

            time.sleep(random.uniform(0.8, 2.5)) # Chờ một chút sau khi gõ xong toàn bộ comment

            # Gửi comment bằng cách nhấn phím ENTER
            comment_box.send_keys(Keys.ENTER)
            print("Đã gửi comment bằng Enter.")
            
            posted_comments_count += 1 # Tăng biến đếm
            print(f"Đã comment thành công! Tổng số đã đăng: {posted_comments_count}")

            # --- THỜI GIAN CHỜ GIỮA CÁC COMMENT ---
            # CỰC KỲ QUAN TRỌNG: Thời gian chờ đủ lớn và ngẫu nhiên giúp giảm rủi ro bị block.
            # Tính toán thời gian dựa trên mục tiêu của bạn.
            # Ví dụ: 5000 comment trong 4 ngày (96 giờ) => ~69 giây/comment (nếu chạy 24/24)
            # Nếu chỉ chạy 10 tiếng/ngày => 500 comment/ngày => ~72 giây/comment
            # Đặt thời gian chờ quá thấp sẽ rất rủi ro.
            delay_time = random.uniform(60, 120) # Ví dụ: chờ từ 1 đến 2 phút
            print(f"Đang chờ {delay_time:.2f} giây trước khi comment tiếp theo...")
            time.sleep(delay_time)

        except Exception as e: # Xử lý lỗi nếu có vấn đề trong một lượt comment
            print(f"LỖI KHI ĐANG COMMENT (lần {posted_comments_count + 1}): {e}")
            print("Bỏ qua comment này và thử comment tiếp theo sau khi chờ.")
            # Comment gây lỗi (comment_text) đã được pop khỏi danh sách comments_available,
            # nên nó sẽ không được thử lại trong lần lặp tiếp theo của vòng lặp này.
            # Chờ lâu hơn một chút khi có lỗi để hệ thống có thời gian "nghỉ"
            time.sleep(random.uniform(15, 45)) 
            continue # Tiếp tục với lần lặp tiếp theo của vòng lặp for (comment tiếp theo)

except Exception as e: # Bắt các lỗi chung không lường trước được trong toàn bộ quá trình xử lý bài viết
    print(f"LỖI CHUNG NGOÀI DỰ KIẾN TRONG QUÁ TRÌNH XỬ LÝ BÀI VIẾT: {e}")

finally: # Khối lệnh này sẽ luôn được thực thi, dù có lỗi hay không
    print(f"\n--- KẾT THÚC SCRIPT ---")
    # Kiểm tra xem các biến đếm có tồn tại không trước khi in ra (để tránh lỗi nếu script dừng sớm)
    if 'posted_comments_count' in locals() and 'num_comments_to_actually_post' in locals():
        print(f"Tổng số comment đã cố gắng đăng theo yêu cầu: {posted_comments_count} / {num_comments_to_actually_post}")
    
    if actual_driver: # Kiểm tra xem đối tượng driver có được khởi tạo không
        input("Nhấn Enter để đóng trình duyệt...") # Chờ người dùng nhấn Enter trước khi đóng
        actual_driver.quit() # Đóng tất cả các cửa sổ trình duyệt và kết thúc session WebDriver
        print("Đã đóng trình duyệt.")