# Deploy lên Render

**Lưu ý:** Render **không còn free tier**. Nếu cần deploy miễn phí, xem file **DEPLOY-FREE.md** (Oracle Cloud, Fly.io, Koyeb, Railway).

---

## Chọn gì khi tạo service?

- **Language / Environment:** chọn **Python 3**
- **Service type:** **Background Worker** (nếu có) — vì bot không chạy web server

## Các bước

1. Vào [render.com](https://render.com) → **New** → **Background Worker**
2. Kết nối repo GitHub (repo chứa code bot)
3. Cấu hình:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
4. **Environment Variables** → Add:
   - Key: `BOT_TOKEN`
   - Value: token bot Telegram (lấy từ @BotFather)
5. **Create Background Worker** / **Deploy**

## Lưu ý

- Nếu không thấy **Background Worker**, dùng **Web Service** và đặt **Start Command** là `python main.py`.
- Render free tier có thể tắt worker sau ~15 phút không hoạt động; plan trả phí thì chạy 24/7.
