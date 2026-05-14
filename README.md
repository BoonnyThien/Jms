# ⚡ Auto-Clicker Hub

Ứng dụng tự động click theo tọa độ màn hình. Hỗ trợ nhiều project, mỗi project có nút nổi (FAB) riêng.

---

## 📋 Yêu cầu

- **Python 3.10+** (khuyên dùng 3.12+)
- **Windows 10/11**

---

## 🚀 Cài đặt (1 lần duy nhất)

### Bước 1: Cài Python

Tải Python từ [python.org/downloads](https://www.python.org/downloads/)

> ⚠️ **Quan trọng:** Khi cài, **tick ☑ "Add Python to PATH"** ở màn hình đầu tiên!

### Bước 2: Clone repo

```bash
git clone https://github.com/<username>/Jms.git
cd Jms
```

### Bước 3: Cài thư viện

```bash
pip install -r requirements.txt
```

Lệnh trên sẽ cài 4 thư viện:
| Thư viện | Chức năng |
|---|---|
| `customtkinter` | Giao diện dark mode hiện đại |
| `pyautogui` | Click chuột ở cấp hệ điều hành |
| `pynput` | Bắt tọa độ chuột khi ghi |
| `Pillow` | Xử lý ảnh (dependency) |

---

## ▶️ Chạy ứng dụng

```bash
python app.py
```

---

## 📖 Hướng dẫn sử dụng

### 1. Tạo Project
- Mở app → nhấn **＋ Tạo Project Mới**
- Đổi tên project bằng cách click vào tên

### 2. Thêm bước click
- Nhấn **📝** để mở trình chỉnh sửa
- **🎯 Ghi**: App thu nhỏ → click vào vị trí cần ghi → tọa độ tự động thêm
- **＋ Thêm**: Thêm bước trống để nhập X, Y thủ công
- **▲**: Di chuyển bước lên (sắp xếp lại thứ tự)
- Chỉnh **Delay (ms)** — thời gian chờ giữa các lần click
- Nhấn **💾 Lưu** khi xong

### 3. Spawn nút nổi (FAB)
- Nhấn **🚀** trên project card → nút nổi xuất hiện
- Kéo nút nổi đến vị trí mong muốn (app nhớ vị trí)
- Nhấn **▶** trên nút nổi để chạy macro
- Nhấn **✕** để đóng nút nổi

### 4. Lưu trữ
- Mọi thay đổi tự động lưu vào `projects.json`
- File này tạo tự động, không cần tạo tay

---

## 📁 Cấu trúc file

```
Jms/
├── app.py              ← Toàn bộ ứng dụng
├── requirements.txt    ← Thư viện cần cài
├── .gitignore          ← Bỏ qua file không cần
├── README.md           ← File này
└── projects.json       ← Tạo tự động khi chạy app
```

---

## ⚠️ Lưu ý

- **Failsafe**: Di chuột đến góc trái-trên màn hình để dừng khẩn cấp
- Nếu gặp lỗi `pip not found`: chạy `python -m pip install -r requirements.txt`
- Nếu gặp lỗi quyền: chạy `pip install --user -r requirements.txt`
