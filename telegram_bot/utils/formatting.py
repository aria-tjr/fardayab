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
    weather: list[dict] | None,
    header_note: str | None = None,
    sentiment: dict | None = None,
    insight: str | None = None,
) -> str:
    # Fallback-friendly formatter when AI is unavailable
    lines: list[str] = []
    if header_note:
        lines.append(header_note)

    lines.append("📊 اقتصاد:")
    if economic:
        usd_line = economic.get("usd_line")
        btc_line = economic.get("btc_line")
        if usd_line:
            lines.append(f"💵 {usd_line}")
        if btc_line:
            lines.append(f"₿ {btc_line}")
    else:
        lines.append("داده کافی برای بخش اقتصادی موجود نیست.")

    lines.append("")
    lines.append("⚽ مسابقات داغ فردا:")
    if sports:
        for m in sports[:3]:
            when = safe(m.get("time"))
            lines.append(f"{safe(m.get('home'))} 🆚 {safe(m.get('away'))} ({when})")
            pred = m.get("prediction")
            if pred:
                lines.append(safe(pred))
    else:
        lines.append("فعلاً مسابقه‌ای فهرست نشده است.")

    lines.append("")
    lines.append("📱 ترند احتمالی اینترنت فردا:")
    if trends:
        tags = [t if t.startswith('#') else f"#{t.replace(' ', '')}" for t in trends[:5]]
        lines.append(" ".join(tags))
    else:
        lines.append("ترندی در دسترس نیست.")

    lines.append("")
    lines.append("🌦️ وضعیت آب‌وهوا:")
    if weather:
        for w in weather:
            lines.append(f"{safe(w.get('city'))} {safe(w.get('desc'))} {safe(w.get('temp'))}°C")
    else:
        lines.append("اطلاعات آب‌وهوا موجود نیست.")

    # sentiment + insight
    if sentiment and (sentiment.get("summary") or sentiment.get("score") is not None):
        lines.append("")
        lines.append("🧭 جمع‌بندی احساسات:")
        if sentiment.get("summary"):
            lines.append(str(sentiment.get("summary")))
    if insight:
        lines.append("")
        lines.append("💡 Insight روز:")
        lines.append(insight)

    return "\n".join(lines)


def date_label(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


# Topic-specific fallbacks

def format_economy_post(economic: dict | None, sentiment: dict | None = None) -> str:
    lines = ["📊 اقتصاد — مرور و چشم‌انداز:"]
    if economic:
        if economic.get("usd_line"):
            lines.append(f"💵 {economic['usd_line']}")
        if economic.get("btc_line"):
            lines.append(f"₿ {economic['btc_line']}")
    else:
        lines.append("داده کافی برای اقتصاد موجود نیست.")
    if sentiment and sentiment.get("summary"):
        lines.append("")
        lines.append("🧭 احساسات بازار:")
        lines.append(str(sentiment.get("summary")))
    lines.append("\n#اقتصاد #ارز #کریپتو")
    return "\n".join(lines)


def format_sports_post(sports: list[dict] | None) -> str:
    lines = ["⚽ مسابقات داغ — تحلیل کوتاه:"]
    if sports:
        for m in sports[:6]:
            when = safe(m.get("time"))
            lines.append(f"{safe(m.get('home'))} 🆚 {safe(m.get('away'))} ({when})")
            if m.get("prediction"):
                lines.append(safe(m.get("prediction")))
    else:
        lines.append("فعلاً مسابقه‌ای فهرست نشده است.")
    lines.append("\n#فوتبال #پیشبینی")
    return "\n".join(lines)


def format_trends_post(trends: list[str] | None, compare: dict | None) -> str:
    lines = ["📱 ترندهای امروز:"]
    if trends:
        tags = [t if t.startswith('#') else f"#{t.replace(' ', '')}" for t in trends[:10]]
        lines.append(" ".join(tags))
    else:
        lines.append("ترندی در دسترس نیست.")
    if compare and compare.get("values"):
        lines.append("")
        lines.append(f"🌍 مقایسه با {compare.get('region')}: ")
        ct = [t if t.startswith('#') else f"#{t.replace(' ', '')}" for t in (compare.get('values') or [])[:5]]
        lines.append(" ".join(ct))
    lines.append("\n#ترند #هشتگ")
    return "\n".join(lines)


def format_weather_post(weather: list[dict] | None) -> str:
    lines = ["🌦️ وضعیت آب‌وهوا:"]
    if weather:
        for w in weather:
            lines.append(f"{safe(w.get('city'))} — {safe(w.get('desc'))} — {safe(w.get('temp'))}°C")
    else:
        lines.append("اطلاعات آب‌وهوا موجود نیست.")
    lines.append("\n#آبوهوا #هواشناسی")
    return "\n".join(lines)


def format_insight_post(insight: str | None) -> str:
    lines = ["💡 Insight روز:"]
    lines.append(insight or "امروز باهوش‌تر از دیروز! 🧠")
    lines.append("\n#دانستنی #نکته")
    return "\n".join(lines)
