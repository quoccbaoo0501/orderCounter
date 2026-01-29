"""
Telegram Order Counter Bot
Counts orders per product in each group using /done + product name.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update

load_dotenv()
from telegram.ext import Application, CommandHandler, ContextTypes

# ─── Config ─────────────────────────────────────────────────────────────

# Canonical product names (display & storage). Matching is case-insensitive.
PRODUCTS = [
    "GPT RENEW",
    "GPT GO",
    "GPT new",
    "Cur Pro",
    "Cur Pro+",
    "Cur Ultra",
    "Krea Basic",
    "Krea Pro",
    "Krea Max",
    "Runway Stand",
    "Runway Pro",
    "Runway Unlimited",
    "Claude Pro",
    "Claude Max 5",
    "Claude Max 20"
]

DATA_FILE = Path(__file__).parent / "order_counts.json"


# ─── Storage ───────────────────────────────────────────────────────────

def _load_data() -> dict:
    """Load counts: { chat_id: { product: count } }."""
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_data(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _product_key(name: str) -> str | None:
    """Return canonical product name if input matches one of PRODUCTS, else None."""
    name = (name or "").strip()
    if not name:
        return None
    lower = name.lower()
    for p in PRODUCTS:
        if p.lower() == lower:
            return p
    return None


# ─── Handlers ───────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat:
        return
    await update.message.reply_text(
        "📦 *Order Counter Bot*\n\n"
        "• Use `/done <product>` to count an order.\n"
        "• Use `/stats` to see counts per product.\n"
        "• Use `/total` to see total orders in this group.\n"
        "• Use `/clear` to clear all orders and export to TXT.\n"
        "• Use `/products` to list valid product names.\n\n"
        "Example: `/done GPT RENEW`",
        parse_mode="Markdown",
    )


async def cmd_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = ["Valid products (use with /done):\n"]
    for p in PRODUCTS:
        lines.append(f"• {p}")
    await update.message.reply_text("\n".join(lines))


async def cmd_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat:
        return
    # /done product name → args = ["product", "name"] or ["product"]
    product_name = " ".join(context.args).strip() if context.args else ""
    canonical = _product_key(product_name)

    if not canonical:
        await update.message.reply_text(
            "❌ Unknown product. Use `/products` to see valid names.\n"
            "Example: `/done GPT RENEW`",
            parse_mode="Markdown",
        )
        return

    chat_id = str(chat.id)
    data = _load_data()
    if chat_id not in data:
        data[chat_id] = {}
    data[chat_id][canonical] = data[chat_id].get(canonical, 0) + 1
    _save_data(data)

    new_count = data[chat_id][canonical]
    await update.message.reply_text(
        f"✅ Order counted for *{canonical}* (total: {new_count})",
        parse_mode="Markdown",
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat:
        return
    chat_id = str(chat.id)
    data = _load_data()
    counts = data.get(chat_id, {})

    if not counts:
        await update.message.reply_text("No orders recorded yet in this chat.")
        return

    lines = ["📊 *Order counts*\n"]
    total = 0
    for p in PRODUCTS:
        c = counts.get(p, 0)
        total += c
        if c > 0:
            lines.append(f"• {p}: {c}")
    lines.append(f"\n_Total: {total}_")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_total(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all products and quantity of each, plus total orders in this group."""
    chat = update.effective_chat
    if not chat:
        return
    chat_id = str(chat.id)
    data = _load_data()
    counts = data.get(chat_id, {})

    if not counts:
        await update.message.reply_text("No orders recorded yet in this chat.")
        return

    lines = ["📦 *Total orders in this group*\n"]
    total = 0
    for p in PRODUCTS:
        c = counts.get(p, 0)
        total += c
        if c > 0:
            lines.append(f"• {p}: {c}")
    lines.append(f"\n_Total: {total}_")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear all order data for this group and export to a TXT file."""
    chat = update.effective_chat
    if not chat:
        return
    chat_id = str(chat.id)
    data = _load_data()
    counts = data.get(chat_id, {})

    if not counts or sum(counts.values()) == 0:
        await update.message.reply_text("No orders to clear in this group.")
        return

    # Build export text: header then each product (in PRODUCTS order) with count
    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d %H:%M UTC")
    chat_title = getattr(chat, "title", None) or f"Chat {chat_id}"
    lines = [
        "Orders cleared from this group",
        f"Group: {chat_title}",
        f"Date: {date_str}",
        "",
        "Orders (by product):",
        "-" * 40,
    ]
    total = 0
    for p in PRODUCTS:
        c = counts.get(p, 0)
        if c > 0:
            lines.append(f"  {p}: {c}")
            total += c
    lines.append("-" * 40)
    lines.append(f"Total: {total}")
    text = "\n".join(lines)

    # Clear data for this group
    if chat_id in data:
        del data[chat_id]
        _save_data(data)

    # Send TXT file (temp file works on all platforms and PTB versions)
    filename = f"orders_cleared_{now.strftime('%Y-%m-%d_%H%M')}.txt"
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(text)
        path = f.name
    try:
        with open(path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=filename,
                caption="✅ All orders cleared for this group. Export attached.",
            )
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


# ─── Main ──────────────────────────────────────────────────────────────

def main() -> None:
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        print("Set BOT_TOKEN environment variable with your Telegram bot token.")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("products", cmd_products))
    app.add_handler(CommandHandler("done", cmd_done))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("total", cmd_total))
    app.add_handler(CommandHandler("clear", cmd_clear))

    print("Bot running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
