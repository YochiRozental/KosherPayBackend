import os
from zoneinfo import ZoneInfo

IL_TZ = ZoneInfo("Asia/Jerusalem")
SESSION_TTL_MIN = int(os.environ.get("IVR_SESSION_TTL_MIN", "60"))
AUDIO_ROOT = "/99"
MAX_TIMEOUT_REPEATS = 3
