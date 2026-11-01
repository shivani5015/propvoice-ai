import logging
from pathlib import Path

LOGS = Path(__file__).with_name("logs")      # project folder me hi bane
LOGS.mkdir(exist_ok=True)

logging.basicConfig(
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOGS / "voice_agent.log", encoding="utf-8"),  # file me save
        logging.StreamHandler()                                         # terminal me bhi dikhe
    ]
)

# saari libraries chup (httpx, faiss, huggingface wagairah)
logging.getLogger().setLevel(logging.WARNING)

# sirf hamari apni lines dikhengi
log = logging.getLogger("voice")
log.setLevel(logging.INFO)
