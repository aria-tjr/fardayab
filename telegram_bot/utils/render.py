from __future__ import annotations

from typing import Any


def render_combined(d: dict[str, Any]) -> str:
    lines: list[str] = []
    ec = d.get("economy") or {}
    lines.append("📊 اقتصاد:")
    if ec.get("usd_range"):
        lines.append(f"💵 دلار: {ec['usd_range']}")
    if ec.get("btc_range"):
        lines.append(f"₿ بیت‌کوین: {ec['btc_range']}")
    if ec.get("reason"):
        lines.append("علت: " + ec["reason"])
    if ec.get("scenario_optimistic") or ec.get("scenario_pessimistic"):
        lines.append("سناریوها:")
        if ec.get("scenario_optimistic"):
            lines.append("✅ خوش‌بینانه: " + ec["scenario_optimistic"])
        if ec.get("scenario_pessimistic"):
            lines.append("⚠️ بدبینانه: " + ec["scenario_pessimistic"])
    if ec.get("compare_yesterday"):
        lines.append("مقایسه با دیروز: " + ec["compare_yesterday"])

    sp = d.get("sports") or []
    if sp:
        lines.append("")
        lines.append("⚽ مسابقات داغ:")
        for m in sp[:6]:
            home, away = m.get("home"), m.get("away")
            time = m.get("time")
            pred = m.get("prediction")
            if home and away:
                lines.append(f"{home} 🆚 {away} ({time or '—'})")
                if pred:
                    lines.append(pred)

    tr = d.get("trends") or {}
    tags = tr.get("tags") or []
    if tags:
        lines.append("")
        lines.append("📱 ترندهای امروز:")
        lines.append(" ".join([t if t.startswith('#') else f"#{t.replace(' ','')}" for t in tags[:8]]))
        if tr.get("compare_region") and tr.get("compare_tags"):
            lines.append(f"🌍 مقایسه با {tr['compare_region']}:")
            lines.append(" ".join([t if t.startswith('#') else f"#{t.replace(' ','')}" for t in tr['compare_tags'][:5]]))

    # Weather section removed per project requirements

    if d.get("insight"):
        lines.append("")
        lines.append("💡 Insight روز:")
        lines.append(str(d["insight"]))

    if d.get("hashtags"):
        lines.append("")
        lines.append(" ".join([h if h.startswith('#') else f"#{h}" for h in d["hashtags"][:8]]))

    return "\n".join(lines)


def render_topic(d: dict[str, Any]) -> str:
    body = d.get("body") or ""
    tags = d.get("hashtags") or []
    tag_line = ("\n" + " ".join([h if h.startswith('#') else f"#{h}" for h in tags[:8]])) if tags else ""
    return body.strip() + tag_line
