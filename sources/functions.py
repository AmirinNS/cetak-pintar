# Shared helper functions. Pure, stateless, imported wherever needed.
from datetime import UTC, datetime


def utcnow():
    """Timezone-aware current UTC timestamp."""
    return datetime.now(UTC)
