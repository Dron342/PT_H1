from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

HACKERONE_BASE_URL = "https://hackerone.com"

DEFAULT_YEAR = 2026
DEFAULT_QUARTERS = (1, 2)
DEFAULT_LIMIT = 30
DEFAULT_USER_TYPE = "individual"
DEFAULT_DELAY_SECONDS = 0.7
DEFAULT_HACKTIVITY_LIMIT = 50
DEFAULT_HACKTIVITY_PAGE_SIZE = 25

DEFAULT_JSON_OUTPUT = DATA_DIR / "hackerone_hunters_sample.json"
DEFAULT_CSV_OUTPUT = DATA_DIR / "hackerone_hunters_sample.csv"
DEFAULT_LEADERBOARD_CSV_OUTPUT = DATA_DIR / "hackerone_leaderboard_entries.csv"
DEFAULT_HACKTIVITY_CSV_OUTPUT = DATA_DIR / "hackerone_hacktivity.csv"
