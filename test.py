# Đọc nội dung từ file input.txt
with open("input.txt", "r", encoding="utf-8") as infile:
    text = infile.read()

# Tách từng từ
words = text.split()

# Ghi từng từ ra file output.txt, mỗi từ trên một dòng
with open("output.txt", "w", encoding="utf-8") as outfile:
    for word in words:
        outfile.write(word + "\n")

input("Đã tạo file output.txt với mỗi từ trên một dòng. Nhấn Enter để thoát...")
