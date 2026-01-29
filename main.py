"""
Telegram Order Counter Bot
Counts orders per product in each group using /done + product name.
"""

import json
import os
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
        "• Use `/done <product>` to count an order — you must *reply* to the order message.\n"
        "• Use `/stats` to see counts per product.\n"
        "• Use `/total` to see total orders in this group.\n"
        "• Use `/products` to list valid product names.\n\n"
        "Example: Reply to a message, then send: `/done GPT RENEW`",
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
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ You must *reply* to order message when using /done.\n"
            "Reply to the order/customer message, then send: `/done <product>`",
            parse_mode="Markdown",
        )
        return
    # /done product name → args = ["product", "name"] or ["product"]
    product_name = " ".join(context.args).strip() if context.args else ""
    canonical = _product_key(product_name)

    if not canonical:
        await update.message.reply_text(
            "❌ Unknown product. Use `/products` to see valid names.\n"
            "Example: Reply to a message, then send: `/done GPT RENEW`",
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

    print("Bot running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
