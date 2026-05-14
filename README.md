# ⚡ Auto-Clicker Hub

Ứng dụng tự động click theo tọa độ màn hình — hỗ trợ nhiều project, mỗi project có nút nổi (FAB) riêng.

---

## 🖥️ Dùng trên máy công ty (Người dùng cuối)

### Chỉ cần 1 bước duy nhất:

1. Vào trang GitHub: **[Releases](https://github.com/BoonnyThien/Jms/releases)**
2. Tải file **`AutoClickerHub.exe`**
3. Bỏ ra Desktop → **nhấp đúp** → chạy luôn ✅

> Không cần cài Python. Không cần cài thêm gì. Tải 1 file, click đúp, xong.

---

## 🔧 Dành cho Developer (máy cá nhân)

### Cài đặt môi trường

```bash
git clone https://github.com/BoonnyThien/Jms.git
cd Jms
pip install -r requirements.txt
python main.py
```

### Tự build EXE trên máy nhà

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "AutoClickerHub" --add-data "<đường dẫn customtkinter>;customtkinter/" main.py
```

Tìm đường dẫn customtkinter:
```bash
python -c "import customtkinter; print(customtkinter.__path__[0])"
```

File EXE xuất ra: `dist/AutoClickerHub.exe` → copy lên Drive/USB/Zalo gửi cho máy công ty.

### Auto-build qua GitHub (đã cài sẵn)

Mỗi khi bạn push tag mới, GitHub tự động build EXE và đăng lên Releases:

```bash
git add -A
git commit -m "v1.0"
git tag v1.0
git push origin Py --tags
```

→ Vào GitHub → Releases → tải `AutoClickerHub.exe` 🎉

---

## 📖 Hướng dẫn sử dụng

| Thao tác | Cách làm |
|---|---|
| Tạo project | ＋ Tạo Project Mới |
| Đổi tên | Click vào tên project, gõ tên mới |
| Thêm bước | 📝 → 🎯 Ghi (click vào màn hình) hoặc ＋ Thêm |
| Chỉnh bước | Sửa X, Y, Delay trực tiếp |
| Sắp xếp | ▲ di chuyển bước lên |
| Mở FAB | 🚀 → nút nổi xuất hiện, kéo đến vị trí muốn |
| Chạy macro | ▶ trên FAB |
| Menu FAB | Chuột phải hoặc ≡ → Đóng / Dashboard |

## ⚠️ Lưu ý

- **Dừng khẩn cấp**: Di chuột đến góc trái-trên màn hình
- FAB nhớ vị trí kéo thả — tự lưu vào `projects.json`
- `projects.json` tạo tự động cạnh file EXE
