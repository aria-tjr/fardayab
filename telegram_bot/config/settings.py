import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHANNEL_ID: str = ""
    ADMIN_USER_ID: int = 0

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5-mini-2025-08-07"  # Latest GPT-5-mini model

    # APIs
    NEWSAPI_KEY: str = ""
    NEWSDATA_KEY: str = ""
    MEDIASTACK_KEY: str = ""
    OPENWEATHER_KEY: str = ""
    THESPORTSDB_KEY: str = "1"  # '1' public test key
    API_FOOTBALL_KEY: str = ""
    API_SPORTS_KEY: str = ""
    
    # Binance API
    BINANCE_API_KEY: str = "UPchixR6CyXXthOG3vSpAaZOXJikWDxD4q7Uu8kkW0qbs1LKCPdXhRIiEg4SBwHv"
    BINANCE_SECRET_KEY: str = "EIxLfnfANrnin3r8EyDQ6eWmwbWxFbQiDzl3TbXKqG7nWCarBXyXE9EQLlnyr3k7"
    BINANCE_BASE_URL: str = "https://api.binance.com"
    BINANCE_WS_URL: str = "wss://stream.binance.com:9443/ws"

    # Scheduling
    TIMEZONE: str = "Asia/Tehran"
    DAILY_RUN_AT: str = "22:00"
    DAILY_RUN_TIMES: str = ""

    # General
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    HTTP_TIMEOUT: float = 30.0  # Increased timeout for better connectivity
    DB_PATH: str = "data/bot.db"
    
    # Internet Connectivity
    ENABLE_REAL_TIME_DATA: bool = True
    DATA_REFRESH_INTERVAL: int = 300  # 5 minutes
    CONNECTION_RETRY_ATTEMPTS: int = 3
    CONNECTION_RETRY_DELAY: float = 5.0

    # Content
    DEFAULT_CITIES: str = "Tehran, Munich"
    NEWS_LANGUAGE: str = "fa"
    
    # Persian APIs
    WORLD_NEWS_API_KEY: str = ""
    LINGVANEX_API_KEY: str = ""
    TASNIM_API_KEY: str = ""
    ISNA_API_KEY: str = ""
    MEHR_API_KEY: str = ""
    FARS_API_KEY: str = ""
    
    # Content APIs
    TMDB_API_KEY: str = ""
    LASTFM_API_KEY: str = ""
    GOODREADS_API_KEY: str = ""
    WIKIPEDIA_API_KEY: str = ""

    # A/B testing
    AB_SEED: str = "tg-content-factory"

    # Feeds/Leagues
    THESPORTSDB_LEAGUE_IDS: str = "4328,4335"  # EPL, LaLiga
    API_SPORTS_LEAGUE_IDS: str = "39,140"  # EPL, LaLiga (API-Sports)

    # Features
    ENABLE_CHARTS: bool = True
    ENABLE_POLL: bool = True
    TRENDS_COMPARE_REGION: str = "united_states"
    # Posting mode
    POST_MODE: str = "split"  # 'split' or 'combined'
    TOPIC_SEQUENCE: str = "crypto,forex,defi,trading,regulatory,sentiment,economic,insight"
    DETAIL_LEVEL: str = "high"  # 'high'|'medium'|'low'
    ENABLE_IMAGES: bool = True
    IMAGE_SIZE: str = "1024x1024"
    # AI controls
    STRUCTURED_GENERATION: bool = True
    OPENAI_MODEL_LIGHT: str = "gpt-5-mini-2025-08-07"  # Latest GPT-5-mini model
    ENABLE_MODERATION: bool = False
    # Content footers
    INCLUDE_DISCLAIMER: bool = True
    DISCLAIMER_TEXT: str = "⚠️ این مطلب صرفاً اطلاع‌رسانی است و توصیه مالی نیست."
    # Content sources footer
    INCLUDE_SOURCES: bool = True
    SOURCES_COUNT: int = 3
    # Persona and tone
    TONE: str = "engaging"
    PERSONA: str = "Persian social media analyst"
    # Channel control
    PIN_POSTS: bool = True
    # Intelligent scheduling
    DYNAMIC_SCHEDULING: bool = True
    # Auto scheduling
    AUTO_SCHEDULE: bool = True
    AUTO_BOOTSTRAP_DAYS: int = 7
    AUTO_BOOTSTRAP_TIMES: str = "10:00,13:00,16:00,21:00"
    AUTO_REGULAR_TIMES: str = "11:00,16:00,21:00"

    def __post_init__(self):
        # Re-read from environment at instantiation time
        object.__setattr__(self, "TELEGRAM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN", self.TELEGRAM_BOT_TOKEN))
        object.__setattr__(self, "TELEGRAM_CHANNEL_ID", os.getenv("TELEGRAM_CHANNEL_ID", self.TELEGRAM_CHANNEL_ID))
        object.__setattr__(self, "ADMIN_USER_ID", int(os.getenv("ADMIN_USER_ID", str(self.ADMIN_USER_ID or 0)) or 0))

        object.__setattr__(self, "OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", self.OPENAI_API_KEY))
        object.__setattr__(self, "OPENAI_MODEL", os.getenv("OPENAI_MODEL", self.OPENAI_MODEL))

        object.__setattr__(self, "NEWSAPI_KEY", os.getenv("NEWSAPI_KEY", self.NEWSAPI_KEY))
        object.__setattr__(self, "NEWSDATA_KEY", os.getenv("NEWSDATA_KEY", self.NEWSDATA_KEY))
        object.__setattr__(self, "MEDIASTACK_KEY", os.getenv("MEDIASTACK_KEY", self.MEDIASTACK_KEY))
        object.__setattr__(self, "OPENWEATHER_KEY", os.getenv("OPENWEATHER_KEY", self.OPENWEATHER_KEY))
        object.__setattr__(self, "THESPORTSDB_KEY", os.getenv("THESPORTSDB_KEY", self.THESPORTSDB_KEY))
        object.__setattr__(self, "API_FOOTBALL_KEY", os.getenv("API_FOOTBALL_KEY", self.API_FOOTBALL_KEY))
        object.__setattr__(self, "API_SPORTS_KEY", os.getenv("API_SPORTS_KEY", self.API_SPORTS_KEY))
        
        # Persian APIs
        object.__setattr__(self, "WORLD_NEWS_API_KEY", os.getenv("WORLD_NEWS_API_KEY", self.WORLD_NEWS_API_KEY))
        object.__setattr__(self, "LINGVANEX_API_KEY", os.getenv("LINGVANEX_API_KEY", self.LINGVANEX_API_KEY))
        object.__setattr__(self, "TASNIM_API_KEY", os.getenv("TASNIM_API_KEY", self.TASNIM_API_KEY))
        object.__setattr__(self, "ISNA_API_KEY", os.getenv("ISNA_API_KEY", self.ISNA_API_KEY))
        object.__setattr__(self, "MEHR_API_KEY", os.getenv("MEHR_API_KEY", self.MEHR_API_KEY))
        object.__setattr__(self, "FARS_API_KEY", os.getenv("FARS_API_KEY", self.FARS_API_KEY))

        object.__setattr__(self, "TIMEZONE", os.getenv("TIMEZONE", self.TIMEZONE))
        object.__setattr__(self, "DAILY_RUN_AT", os.getenv("DAILY_RUN_AT", self.DAILY_RUN_AT))
        object.__setattr__(self, "DAILY_RUN_TIMES", os.getenv("DAILY_RUN_TIMES", self.DAILY_RUN_TIMES))

        object.__setattr__(self, "ENV", os.getenv("ENV", self.ENV))
        object.__setattr__(self, "LOG_LEVEL", os.getenv("LOG_LEVEL", self.LOG_LEVEL))
        object.__setattr__(self, "HTTP_TIMEOUT", float(os.getenv("HTTP_TIMEOUT", str(self.HTTP_TIMEOUT))))
        object.__setattr__(self, "DB_PATH", os.getenv("DB_PATH", self.DB_PATH))
        
        # Internet Connectivity settings
        object.__setattr__(self, "ENABLE_REAL_TIME_DATA", os.getenv("ENABLE_REAL_TIME_DATA", "1" if self.ENABLE_REAL_TIME_DATA else "0") == "1")
        object.__setattr__(self, "DATA_REFRESH_INTERVAL", int(os.getenv("DATA_REFRESH_INTERVAL", str(self.DATA_REFRESH_INTERVAL))))
        object.__setattr__(self, "CONNECTION_RETRY_ATTEMPTS", int(os.getenv("CONNECTION_RETRY_ATTEMPTS", str(self.CONNECTION_RETRY_ATTEMPTS))))
        object.__setattr__(self, "CONNECTION_RETRY_DELAY", float(os.getenv("CONNECTION_RETRY_DELAY", str(self.CONNECTION_RETRY_DELAY))))

        object.__setattr__(self, "DEFAULT_CITIES", os.getenv("DEFAULT_CITIES", self.DEFAULT_CITIES))
        object.__setattr__(self, "NEWS_LANGUAGE", os.getenv("NEWS_LANGUAGE", self.NEWS_LANGUAGE))

        object.__setattr__(self, "AB_SEED", os.getenv("AB_SEED", self.AB_SEED))

        object.__setattr__(self, "THESPORTSDB_LEAGUE_IDS", os.getenv("THESPORTSDB_LEAGUE_IDS", self.THESPORTSDB_LEAGUE_IDS))
        object.__setattr__(self, "API_SPORTS_LEAGUE_IDS", os.getenv("API_SPORTS_LEAGUE_IDS", self.API_SPORTS_LEAGUE_IDS))

        object.__setattr__(self, "ENABLE_CHARTS", os.getenv("ENABLE_CHARTS", "1" if self.ENABLE_CHARTS else "0") == "1")
        object.__setattr__(self, "ENABLE_POLL", os.getenv("ENABLE_POLL", "1" if self.ENABLE_POLL else "0") == "1")
        object.__setattr__(self, "TRENDS_COMPARE_REGION", os.getenv("TRENDS_COMPARE_REGION", self.TRENDS_COMPARE_REGION))
        object.__setattr__(self, "POST_MODE", os.getenv("POST_MODE", self.POST_MODE))
        object.__setattr__(self, "TOPIC_SEQUENCE", os.getenv("TOPIC_SEQUENCE", self.TOPIC_SEQUENCE))
        object.__setattr__(self, "DETAIL_LEVEL", os.getenv("DETAIL_LEVEL", self.DETAIL_LEVEL))
        object.__setattr__(self, "ENABLE_IMAGES", os.getenv("ENABLE_IMAGES", "1" if self.ENABLE_IMAGES else "0") == "1")
        object.__setattr__(self, "IMAGE_SIZE", os.getenv("IMAGE_SIZE", self.IMAGE_SIZE))
        object.__setattr__(self, "STRUCTURED_GENERATION", os.getenv("STRUCTURED_GENERATION", "1" if self.STRUCTURED_GENERATION else "0") == "1")
        object.__setattr__(self, "OPENAI_MODEL_LIGHT", os.getenv("OPENAI_MODEL_LIGHT", self.OPENAI_MODEL_LIGHT))
        object.__setattr__(self, "ENABLE_MODERATION", os.getenv("ENABLE_MODERATION", "1" if self.ENABLE_MODERATION else "0") == "1")
        object.__setattr__(self, "INCLUDE_DISCLAIMER", os.getenv("INCLUDE_DISCLAIMER", "1" if self.INCLUDE_DISCLAIMER else "0") == "1")
        object.__setattr__(self, "DISCLAIMER_TEXT", os.getenv("DISCLAIMER_TEXT", self.DISCLAIMER_TEXT))
        object.__setattr__(self, "INCLUDE_SOURCES", os.getenv("INCLUDE_SOURCES", "1" if self.INCLUDE_SOURCES else "0") == "1")
        object.__setattr__(self, "SOURCES_COUNT", int(os.getenv("SOURCES_COUNT", str(self.SOURCES_COUNT))))
        object.__setattr__(self, "TONE", os.getenv("TONE", self.TONE))
        object.__setattr__(self, "PERSONA", os.getenv("PERSONA", self.PERSONA))
        object.__setattr__(self, "PIN_POSTS", os.getenv("PIN_POSTS", "1" if self.PIN_POSTS else "0") == "1")
        object.__setattr__(self, "DYNAMIC_SCHEDULING", os.getenv("DYNAMIC_SCHEDULING", "1" if self.DYNAMIC_SCHEDULING else "0") == "1")
        object.__setattr__(self, "AUTO_SCHEDULE", os.getenv("AUTO_SCHEDULE", "1" if self.AUTO_SCHEDULE else "0") == "1")
        object.__setattr__(self, "AUTO_BOOTSTRAP_DAYS", int(os.getenv("AUTO_BOOTSTRAP_DAYS", str(self.AUTO_BOOTSTRAP_DAYS))))
        object.__setattr__(self, "AUTO_BOOTSTRAP_TIMES", os.getenv("AUTO_BOOTSTRAP_TIMES", self.AUTO_BOOTSTRAP_TIMES))
        object.__setattr__(self, "AUTO_REGULAR_TIMES", os.getenv("AUTO_REGULAR_TIMES", self.AUTO_REGULAR_TIMES))

    def cities(self) -> list[str]:
        return [c.strip() for c in self.DEFAULT_CITIES.split(",") if c.strip()]

    def leagues(self) -> list[str]:
        return [x.strip() for x in self.THESPORTSDB_LEAGUE_IDS.split(",") if x.strip()]

    def leagues_api_sports(self) -> list[str]:
        return [x.strip() for x in self.API_SPORTS_LEAGUE_IDS.split(",") if x.strip()]

    def run_times(self) -> list[str]:
        # If DAILY_RUN_TIMES defined, use those; else fallback to single DAILY_RUN_AT
        src = self.DAILY_RUN_TIMES.strip()
        if src:
            return [t.strip() for t in src.split(",") if t.strip()]
        return [self.DAILY_RUN_AT]

    def topics(self) -> list[str]:
        allowed = {"economy", "sports", "trends", "insight"}
        seq = [t.strip().lower() for t in self.TOPIC_SEQUENCE.split(",") if t.strip()]
        return [t for t in seq if t in allowed] or ["economy", "sports", "trends", "insight"]
