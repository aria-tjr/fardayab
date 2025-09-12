from __future__ import annotations


def combined_schema() -> dict:
    return {
        "name": "DailyCombinedPost",
        "schema": {
            "type": "object",
            "properties": {
                "economy": {
                    "type": "object",
                    "properties": {
                        "usd_range": {"type": "string"},
                        "btc_range": {"type": "string"},
                        "reason": {"type": "string"},
                        "scenario_optimistic": {"type": "string"},
                        "scenario_pessimistic": {"type": "string"},
                        "compare_yesterday": {"type": "string"},
                    },
                    "required": ["reason"],
                },
                "sports": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "home": {"type": "string"},
                            "away": {"type": "string"},
                            "time": {"type": "string"},
                            "prediction": {"type": "string"},
                        },
                        "required": ["home", "away"],
                    },
                },
                "trends": {
                    "type": "object",
                    "properties": {
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "compare_region": {"type": "string"},
                        "compare_tags": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "weather": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                            "desc": {"type": "string"},
                            "temp": {"type": "number"},
                        },
                        "required": ["city"],
                    },
                },
                "insight": {"type": "string"},
                "hashtags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["economy", "insight"],
            "additionalProperties": True,
        },
        "strict": False,
    }


def topic_schema(topic: str) -> dict:
    base = {
        "name": f"Topic_{topic}",
        "schema": {
            "type": "object",
            "properties": {
                "body": {"type": "string"},
                "hashtags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["body"],
            "additionalProperties": True,
        },
        "strict": False,
    }
    return base

