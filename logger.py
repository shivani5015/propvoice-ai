import logging
from pathlib import Path

LOGS = Path(__file__).with_name("logs")     
LOGS.mkdir(exist_ok=True)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOGS / "voice_agent.log", encoding="utf-8"),  # file me save
        logging.StreamHandler()                                         # terminal me bhi dikhe
    ]
)

# saari libraries chup (httpx, faiss, huggingface wagairah)
logging.getLogger().setLevel(logging.WARNING)

log = logging.getLogger("voice")
log.setLevel(logging.INFO)