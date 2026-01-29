# Deploy bot miễn phí (Render không còn free)

Các nền tảng **miễn phí** hoặc **rất rẻ** để chạy bot 24/7:

---

## 1. Oracle Cloud Free Tier (miễn phí mãi mãi)

**Ưu điểm:** VPS miễn phí vĩnh viễn, full quyền, data lưu trên máy của bạn.

1. Đăng ký [Oracle Cloud](https://www.oracle.com/cloud/free/) (cần thẻ tín dụng để xác minh, không bị trừ tiền nếu dùng đúng free tier).
2. Tạo **Compute Instance** → chọn **Always Free** (AMD hoặc ARM).
3. SSH vào máy, cài Python 3 và clone/copy code bot.
4. Chạy bot bằng **systemd** (chạy nền, tự chạy lại khi tắt):

```bash
# Trên VPS (Ubuntu)
sudo apt update && sudo apt install -y python3 python3-pip git
cd ~ && git clone <your-repo-url> ordercounter && cd ordercounter
pip3 install -r requirements.txt

# Tạo file .env với BOT_TOKEN
echo 'BOT_TOKEN=your_token_here' > .env

# Tạo service
sudo nano /etc/systemd/system/ordercounter.service
```

Nội dung file service (sửa `youruser` và đường dẫn nếu cần):

```ini
[Unit]
Description=Order Counter Telegram Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/ordercounter
EnvironmentFile=/home/youruser/ordercounter/.env
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ordercounter
sudo systemctl start ordercounter
sudo systemctl status ordercounter
```

---

## 2. Fly.io (free tier)

**Ưu điểm:** Deploy từ máy tính, không cần VPS. Free tier có giới hạn nhưng đủ cho 1 bot nhỏ.

1. Cài [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) và đăng nhập: `fly auth login`
2. Trong thư mục project:

```bash
fly launch
# App name: để trống hoặc đặt tên unique (vd: ordercounter-tênbạn)
# PostgreSQL/Redis: No
fly secrets set BOT_TOKEN=your_telegram_bot_token
fly deploy
```

---

## 3. Koyeb (free tier)

**Ưu điểm:** Có free tier, deploy từ GitHub.

1. Vào [koyeb.com](https://www.koyeb.com) → Sign up → **Create App**.
2. Deploy từ **GitHub** (chọn repo).
3. **Runtime:** Docker (dùng Dockerfile trong repo) hoặc Native → Python.
4. **Build:** `pip install -r requirements.txt`
5. **Run:** `python main.py`
6. **Environment variables:** thêm `BOT_TOKEN`.
7. Deploy. Free tier có giới hạn giờ chạy/tháng.

---

## 4. Railway (khoảng $5 credit/tháng)

**Ưu điểm:** Rất dễ, kết nối GitHub là chạy. Không còn free unlimited nhưng có credit mỗi tháng.

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub.
2. Thêm biến môi trường `BOT_TOKEN`.
3. Settings → Start Command: `python main.py`

---

## So sánh nhanh

| Nền tảng      | Chi phí        | Độ khó   | Ghi chú                    |
|---------------|----------------|----------|----------------------------|
| Oracle Cloud  | Free mãi mãi   | Trung bình | VPS thật, data giữ được   |
| Fly.io        | Free tier      | Dễ       | Deploy bằng lệnh           |
| Koyeb         | Free tier      | Dễ       | Deploy từ GitHub           |
| Railway       | ~$5 credit/tháng | Rất dễ | Có thể hết credit          |

**Gợi ý:** Nếu muốn **free lâu dài** và không ngại setup: dùng **Oracle Cloud**. Nếu muốn **nhanh, ít cấu hình**: thử **Fly.io** hoặc **Koyeb** trước.
