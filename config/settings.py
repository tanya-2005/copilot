"""
settings.py — centralized env/config loading. Every other module imports
from here rather than reading os.environ directly, so there's one place
to see what configuration the system depends on.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
    OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY", "")
    TAVILY_API_KEY: str = os.environ.get("TAVILY_API_KEY", "")

    SMTP_HOST: str = os.environ.get("SMTP_HOST", "")
    SMTP_PORT: str = os.environ.get("SMTP_PORT", "")
    SMTP_USER: str = os.environ.get("SMTP_USER", "")
    SMTP_PASS: str = os.environ.get("SMTP_PASS", "")
    DIGEST_TO: str = os.environ.get("DIGEST_TO", "")

    def validate_for(self, required: list[str]):
        """Call this at the top of each entry-point script with the vars it
        actually needs, so missing config fails fast with a clear message
        instead of a confusing error three layers down."""
        missing = [name for name in required if not getattr(self, name, None)]
        if missing:
            raise RuntimeError(
                f"Missing required settings: {', '.join(missing)}. "
                f"Check your .env file or GitHub Actions secrets."
            )


settings = Settings()

_CONFIG_DIR = os.path.dirname(__file__)


def load_sources_config() -> dict:
    import yaml
    with open(os.path.join(_CONFIG_DIR, "sources.yaml")) as f:
        return yaml.safe_load(f)


def load_matching_config() -> dict:
    import yaml
    with open(os.path.join(_CONFIG_DIR, "matching.yaml")) as f:
        return yaml.safe_load(f)

