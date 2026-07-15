"""
settings.py — centralized env/config loading. Every other module imports
from here rather than reading os.environ directly, so there's one place
to see what configuration the system depends on.
"""
import os
from dotenv import load_dotenv

load_dotenv()


_ENV_VARS = [
    "DATABASE_URL", "OPENROUTER_API_KEY", "TAVILY_API_KEY",
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "DIGEST_TO",
]


class Settings:
    """Reads os.environ fresh on every attribute access (via __getattr__)
    rather than caching values at import time. Needed for platforms like
    Streamlit Community Cloud, which keep one Python process alive across
    script re-runs — if a value were baked in as a class attribute at
    import time, adding/editing a secret later in the same process would
    silently keep using the old (often empty) value."""

    def __getattr__(self, name: str):
        if name in _ENV_VARS:
            return os.environ.get(name, "")
        raise AttributeError(name)

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

