from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class EconomicForecast:
    usd_irr: str | None = None
    btc_usd_range: str | None = None
    btc_rise_prob: int | None = None
    usd_rise_prob: int | None = None


def safe(v: object, default: str = "—") -> str:
    return default if v in (None, "", [], {}) else str(v)


def format_channel_post(
    economic: dict | None,
    sports: list[dict] | None,
    trends: list[str] | None,
    header_note: str | None = None,
    sentiment: dict | None = None,
    insight: str | None = None,
) -> str:
    # Fallback-friendly formatter when AI is unavailable
    lines: list[str] = []
    if header_note:
        lines.append(header_note)

    lines.append("")
    lines.append("**📊 اقتصاد و بازارها** 💰")
    lines.append("─" * 20)
    if economic:
        usd_line = economic.get("usd_line")
        btc_line = economic.get("btc_line")
        if usd_line:
            lines.append(f"💵 {usd_line}")
        if btc_line:
            lines.append(f"₿ {btc_line}")
    else:
        lines.append("📈 داده کافی برای بخش اقتصادی موجود نیست.")

    lines.append("")
    lines.append("**⚽ ورزش** ⚽")
    lines.append("─" * 20)
    if sports:
        for m in sports[:3]:
            when = safe(m.get("time"))
            lines.append(f"🏟️ {safe(m.get('home'))} 🆚 {safe(m.get('away'))} ⏰ ({when})")
            pred = m.get("prediction")
            if pred:
                lines.append(f"🔮 {safe(pred)}")
    else:
        lines.append("⚽ فعلاً مسابقه‌ای فهرست نشده است.")

    lines.append("")
    lines.append("**📱 ترند اینترنت** 🔥")
    lines.append("─" * 20)
    if trends:
        tags = [t if t.startswith('#') else f"#{t.replace(' ', '')}" for t in trends[:5]]
        lines.append("🔥 " + " ".join(tags))
    else:
        lines.append("📱 ترندی در دسترس نیست.")

    # Weather section removed per project requirements

    # sentiment + insight
    if sentiment and (sentiment.get("summary") or sentiment.get("score") is not None):
        lines.append("")
        lines.append("**🧭 تحلیل احساسات بازار** 📊")
        lines.append("─" * 20)
        if sentiment.get("summary"):
            lines.append(f"💭 {str(sentiment.get('summary'))}")
    if insight:
        lines.append("")
    lines.append("**💡 Insight روز** ✨")
    lines.append("─" * 20)
    if insight:
        lines.append(f"🎯 {insight}")

    return "\n".join(lines)


def date_label(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


# Topic-specific fallbacks

def format_economy_post(economic: dict | None, sentiment: dict | None = None) -> str:
    lines = ["**📊 اقتصاد و بازارها** 💰"]
    lines.append("─" * 20)
    if economic:
        if economic.get("usd_line"):
            lines.append(f"💵 {economic['usd_line']}")
        if economic.get("btc_line"):
            lines.append(f"₿ {economic['btc_line']}")
    else:
        lines.append("📈 داده کافی برای اقتصاد موجود نیست.")
    if sentiment and sentiment.get("summary"):
        lines.append("")
        lines.append("**🧭 تحلیل احساسات** 📊")
        lines.append("─" * 15)
        lines.append(f"💭 {str(sentiment.get('summary'))}")
    lines.append("\n#اقتصاد #ارز #کریپتو #بازار")
    return "\n".join(lines)


def format_sports_post(sports: list[dict] | None) -> str:
    lines = ["**⚽ مسابقات داغ فردا** ⚽"]
    lines.append("─" * 20)
    if sports:
        for m in sports[:6]:
            when = safe(m.get("time"))
            lines.append(f"🏟️ {safe(m.get('home'))} 🆚 {safe(m.get('away'))} ⏰ ({when})")
            if m.get("prediction"):
                lines.append(f"🔮 {safe(m.get('prediction'))}")
    else:
        lines.append("⚽ فعلاً مسابقه‌ای فهرست نشده است.")
    lines.append("\n#فوتبال #پیشبینی #مسابقات #ورزش")
    return "\n".join(lines)


def format_trends_post(trends: list[str] | None, compare: dict | None) -> str:
    lines = ["**📱 ترندهای داغ اینترنت** 🔥"]
    lines.append("─" * 20)
    if trends:
        tags = [t if t.startswith('#') else f"#{t.replace(' ', '')}" for t in trends[:10]]
        lines.append("🔥 " + " ".join(tags))
    else:
        lines.append("📱 ترندی در دسترس نیست.")
    if compare and compare.get("values"):
        lines.append("")
        lines.append("**🌍 مقایسه جهانی** 🌐")
        lines.append("─" * 15)
        lines.append(f"🌍 مقایسه با {compare.get('region')}: ")
        ct = [t if t.startswith('#') else f"#{t.replace(' ', '')}" for t in (compare.get('values') or [])[:5]]
        lines.append("🔥 " + " ".join(ct))
    lines.append("\n#ترند #هشتگ #اینترنت #داغ")
    return "\n".join(lines)


# Weather-specific formatter removed


def format_insight_post(insight: str | None) -> str:
    lines = ["**💡 نکته طلایی روز** ✨"]
    lines.append("─" * 20)
    lines.append(f"🎯 {insight or 'امروز باهوش‌تر از دیروز! 🧠'}")
    lines.append("\n#دانستنی #نکته #طلایی #تحلیل")
    return "\n".join(lines)


def is_generic_social_media_advice(text: str) -> bool:
    """Check if text contains generic social media advice that should be filtered out."""
    if not text:
        return False
    
    # Keywords that indicate generic social media advice
    generic_keywords = [
        "تعامل اولیه", "الگوریتم", "مخاطب", "واکنش", "CTA", "میکرواینفلوئنسر",
        "نرخ تعامل", "بازپخش", "قلاب", "کامنت", "اشتراک", "ویدیو", "کلیپ",
        "زیرنویس", "تماشای بدون صدا", "تبلیغ", "ارگانیک", "هزینه تبلیغ",
        "بازاریابی محتوا", "زندگی دیجیتال", "رسانه اجتماعی", "شبکه‌های اجتماعی"
    ]
    
    # Check for multiple generic keywords
    text_lower = text.lower()
    generic_count = sum(1 for keyword in generic_keywords if keyword in text_lower)
    
    # If more than 3 generic keywords are found, it's likely generic advice
    if generic_count >= 3:
        return True
    
    # Check for specific patterns
    generic_patterns = [
        "داده‌های جدید مستقیم امروز در دسترس نیست",
        "نکته عملی و زمان‌مند از زاویه تحلیل رفتار",
        "برای زندگی دیجیتال و بازاریابی محتوا",
        "در محیط فعلیِ الگوریتمی",
        "تعیین‌کنندهٔ شانس پخش گسترده",
        "اولین واکنش‌ها و مدت تماشای",
        "الگوریتم محتوای شما را به مخاطب‌های بیشتری نشان می‌دهد"
    ]
    
    for pattern in generic_patterns:
        if pattern in text:
            return True
    
    return False


def clip_telegram_text(text: str, limit: int = 4096) -> str:
    """Ensure message fits Telegram's hard limit.
    Keeps as much as possible and appends an ellipsis when clipping.
    """
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    # Reserve one char for ellipsis
    keep = max(0, limit - 1)
    return text[:keep].rstrip() + "…"


def normalize_persian(text: str) -> str:
    """Normalize digits and common Arabic variants to Persian typography.
    - Western digits 0-9 -> Persian ۰-۹
    - Arabic y,k -> Persian ی,ک
    """
    if not text:
        return ""
    trans = str.maketrans({
        "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
        "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
        "ي": "ی", "ك": "ک",
    })
    return text.translate(trans)


def format_sources(news: list[dict] | None, count: int = 3) -> str:
    if not news:
        return ""
    import re
    def domain(u: str | None) -> str:
        if not u:
            return ""
        try:
            from urllib.parse import urlparse
            d = urlparse(u).netloc
            return d.replace("www.", "")
        except Exception:
            return ""
    items = []
    for it in (news or [])[:count]:
        src = it.get("source") or domain(it.get("url"))
        title = (it.get("title") or "").strip()
        if src and title:
            items.append(f"• {src}: {title}")
        elif src:
            items.append(f"• {src}")
    if not items:
        return ""
    return "\n".join(["\nمنابع:"] + items)
