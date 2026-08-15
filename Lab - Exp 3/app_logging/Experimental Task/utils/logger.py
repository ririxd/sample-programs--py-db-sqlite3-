import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "app_logging"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "lab3_project.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("lab3_project")
