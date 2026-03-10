"""Telegram command handlers for Manipal Local Loop."""

import json
import logging

from telegram import Update
from telegram.ext import ContextTypes

from manipal_loop.database.db import get_db

logger = logging.getLogger(__name__)

_CATEGORIES = [
    "Power Cut", "Traffic", "Weather", "Academic",
    "Events", "Emergency", "Food", "City News",
    "Campus Chatter", "Official Alert",
]

_HELP_TEXT = """
<b>🔄 Manipal Local Loop — Commands</b>

/start — Register &amp; welcome message
/help — Show this help menu
/powercut — Latest power cut notices
/weather — Current weather &amp; alerts
/events — Upcoming events
/news — Latest city news
/traffic — Traffic updates
/campus — Campus chatter from Reddit
/alerts — High-urgency alerts
/digest — Today's digest
/subscribe [category] — Subscribe to a category
/unsubscribe [category] — Unsubscribe from a category
/mystatus — Your subscription status
/report — Report a local issue

<b>Available categories:</b>
{}
""".format(", ".join(_CATEGORIES))


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — register the user and send a welcome message.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    chat = update.effective_chat
    user = update.effective_user
    if chat is None or user is None:
        return

    db = get_db()
    db.add_user(chat.id, user.username or "")

    await update.message.reply_html(
        f"👋 Welcome to <b>Manipal Local Loop</b>, {user.first_name}!\n\n"
        "I deliver hyperlocal news for Manipal, Udupi &amp; Mangaluru — "
        "power cuts, traffic, weather, events, and more.\n\n"
        "Type /help to see all commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — display the command list.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    if update.message:
        await update.message.reply_html(_HELP_TEXT)


async def powercut_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /powercut — show recent power cut updates.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    await _send_category_updates(update, "Power Cut", "⚡ Power Cut Updates")


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /weather — show recent weather updates.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    await _send_category_updates(update, "Weather", "🌦 Weather Updates")


async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /events — show recent event updates.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    await _send_category_updates(update, "Events", "🎉 Upcoming Events")


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /news — show recent city news.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    await _send_category_updates(update, "City News", "📰 Latest City News")


async def traffic_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /traffic — show recent traffic updates.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    await _send_category_updates(update, "Traffic", "🚗 Traffic Updates")


async def campus_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /campus — show recent campus chatter.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    await _send_category_updates(update, "Campus Chatter", "🎓 Campus Chatter")


async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /alerts — show high-urgency (≥4) updates.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    if update.message is None:
        return

    db = get_db()
    updates = db.get_recent_updates(hours=12)
    high = [u for u in updates if u.get("urgency_score", 1) >= 4]

    if not high:
        await update.message.reply_text("✅ No high-urgency alerts in the last 12 hours.")
        return

    lines = ["🚨 <b>High-Urgency Alerts</b>\n"]
    for u in high[:10]:
        lines.append(
            f"• <b>[{u['category']}]</b> {u['title']}\n"
            f"  <a href='{u.get('url', '')}'>Read more</a>"
        )
    await update.message.reply_html("\n".join(lines))


async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /digest — show today's digest.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    if update.message is None:
        return

    db = get_db()
    updates = db.get_todays_updates()

    if not updates:
        await update.message.reply_text("📭 No updates yet today. Check back later!")
        return

    lines = ["📰 <b>Today's Digest — Manipal Local Loop</b>\n"]
    for u in updates[:15]:
        lines.append(f"• <b>[{u['category']}]</b> {u['title']}")
    await update.message.reply_html("\n".join(lines))


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /subscribe [category] — add a category subscription.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    if update.message is None or update.effective_chat is None:
        return

    if not context.args:
        await update.message.reply_html(
            "Usage: /subscribe <category>\n\n"
            f"<b>Available:</b> {', '.join(_CATEGORIES)}"
        )
        return

    category = " ".join(context.args).strip()
    if category not in _CATEGORIES:
        await update.message.reply_text(
            f"Unknown category: {category}\n"
            f"Available: {', '.join(_CATEGORIES)}"
        )
        return

    db = get_db()
    chat_id = update.effective_chat.id
    db.add_user(chat_id, update.effective_user.username or "")
    cats = db.get_user_subscriptions(chat_id)
    if category not in cats:
        cats.append(category)
    db.update_subscriptions(chat_id, cats)
    await update.message.reply_text(f"✅ Subscribed to: {category}")


async def unsubscribe_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /unsubscribe [category] — remove a category subscription.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    if update.message is None or update.effective_chat is None:
        return

    if not context.args:
        await update.message.reply_html(
            "Usage: /unsubscribe <category>\n\n"
            f"<b>Available:</b> {', '.join(_CATEGORIES)}"
        )
        return

    category = " ".join(context.args).strip()
    db = get_db()
    chat_id = update.effective_chat.id
    cats = db.get_user_subscriptions(chat_id)
    if category in cats:
        cats.remove(category)
    db.update_subscriptions(chat_id, cats)
    await update.message.reply_text(f"🔕 Unsubscribed from: {category}")


async def mystatus_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /mystatus — display the user's subscription status.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    if update.message is None or update.effective_chat is None:
        return

    db = get_db()
    chat_id = update.effective_chat.id
    row = db.get_user_row(chat_id)

    if not row:
        await update.message.reply_text("You are not registered. Use /start first.")
        return

    cats = row.get("subscribed_categories")
    cats = json.loads(cats or "[]")
    cat_text = ", ".join(cats) if cats else "All categories"
    await update.message.reply_html(
        f"👤 <b>Your Status</b>\n\n"
        f"Username: @{row['username'] or 'N/A'}\n"
        f"Active: {'Yes' if row['is_active'] else 'No'}\n"
        f"Subscribed to: {cat_text}"
    )


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /report — prompt user to report a local issue.

    Args:
        update: Incoming Telegram update.
        context: Callback context.
    """
    if update.message is None:
        return

    await update.message.reply_text(
        "📣 To report a local issue, describe it here and we'll note it.\n"
        "(Feature coming soon — stay tuned!)"
    )


# ------------------------------------------------------------------
# Shared helper
# ------------------------------------------------------------------

async def _send_category_updates(
    update: Update, category: str, header: str
) -> None:
    """Fetch recent updates for *category* and send them to the user.

    Args:
        update: Incoming Telegram update.
        category: Category string to filter on.
        header: Display header for the message.
    """
    if update.message is None:
        return

    db = get_db()
    updates = db.get_recent_updates(hours=24)
    filtered = [u for u in updates if u.get("category") == category]

    if not filtered:
        await update.message.reply_text(f"No {category} updates in the last 24 hours.")
        return

    lines = [f"<b>{header}</b>\n"]
    for u in filtered[:10]:
        url = u.get("url", "")
        title = u.get("title", "")
        link_part = f' — <a href="{url}">Link</a>' if url else ""
        lines.append(f"• {title}{link_part}")

    await update.message.reply_html("\n".join(lines))
