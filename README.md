# ⚡ Auto-Clicker Hub

Ứng dụng tự động click theo tọa độ màn hình. Hỗ trợ nhiều project, mỗi project có nút nổi (FAB) riêng.

---

## 📋 Yêu cầu

- **Python 3.10+** (khuyên dùng 3.12+)
- **Windows 10/11**

---

## 🚀 Cài đặt & Chạy (cho máy mới)

### 1. Cài Python

Tải từ [python.org/downloads](https://www.python.org/downloads/)

> ⚠️ **Tick ☑ "Add Python to PATH"** khi cài!

### 2. Clone & cài thư viện

```bash
git clone https://github.com/BoonnyThien/Jms.git
cd Jms
pip install -r requirements.txt
```

### 3. Chạy

```bash
python main.py
```

---

## 📦 Đóng gói EXE (không cần Python trên máy đích)

### Cài PyInstaller (1 lần)

```bash
pip install pyinstaller
```

### Build EXE

```bash
pyinstaller --noconfirm --onefile --windowed --name "AutoClickerHub" --add-data "venv/Lib/site-packages/customtkinter;customtkinter/" main.py
```

> Nếu cài global (không dùng venv), thay đường dẫn:
> ```bash
> pyinstaller --noconfirm --onefile --windowed --name "AutoClickerHub" --add-data "C:/Users/<USER>/AppData/Local/Programs/Python/Python3xx/Lib/site-packages/customtkinter;customtkinter/" main.py
> ```

File EXE sẽ ở: `dist/AutoClickerHub.exe`

Copy `AutoClickerHub.exe` vào bất kỳ thư mục nào → chạy trực tiếp. File `projects.json` tạo tự động cạnh EXE.

---

## 📖 Hướng dẫn sử dụng

| Thao tác | Cách làm |
|---|---|
| **Tạo project** | Nhấn ＋ Tạo Project Mới |
| **Đổi tên** | Click vào tên project, gõ tên mới |
| **Thêm bước** | 📝 → 🎯 Ghi (click vào màn hình) hoặc ＋ Thêm |
| **Chỉnh bước** | Sửa trực tiếp X, Y, Delay trong bảng |
| **Sắp xếp** | Nút ▲ để di chuyển bước lên |
| **Mở FAB** | 🚀 → nút nổi xuất hiện, kéo đến vị trí mong muốn |
| **Chạy macro** | Nhấn ▶ trên FAB |
| **Menu FAB** | Click phải hoặc ≡ → Đóng FAB / Mở Dashboard |

---

## 📁 Cấu trúc

```
Jms/
├── main.py             ← Ứng dụng chính
├── requirements.txt    ← Thư viện
├── .gitignore
├── README.md
└── projects.json       ← Tạo tự động
```

## ⚠️ Lưu ý

- **Failsafe**: Di chuột đến góc trái-trên màn hình để dừng khẩn cấp
- Nếu `pip` lỗi: `python -m pip install -r requirements.txt`
- FAB nhớ vị trí kéo thả — lưu vào `projects.json`
