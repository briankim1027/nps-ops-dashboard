from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORT_DIR = DATA_DIR / "exports"
DEFAULT_TEAM = "전북"
DEFAULT_TARGET_SCORE = 87.0
MAPPING_FILE = PROJECT_ROOT / "팀소속_대리점명_매장명_매칭.xlsx"
EXPORT_TOP_N_STORES = 64
EXPORT_TOP_N_TYPES = 30
EXPORT_TOP_N_AUDIT = 100
MAPPING_UNMATCHED_WARN_RATE = 0.05

# Care Priority sample-confidence multipliers.
# Keyed on the (non-sales) response count and applied as a *multiplier* on the base
# risk score — not as an additive term — so low-sample stores stop surfacing at the
# top of the care ranking by noise. Tiers are ordered high→low min_n.
CARE_PRIORITY_SAMPLE_CONFIDENCE = [
    {"min_n": 20, "multiplier": 1.00},
    {"min_n": 10, "multiplier": 0.85},
    {"min_n": 5, "multiplier": 0.70},
]
# n < 5 stores are already split out as 샘플 착시형 in diagnose_store and excluded from
# the Risk Map; this strong discount keeps them low anywhere the raw score is still used.
CARE_PRIORITY_LOW_SAMPLE_MULTIPLIER = 0.50
