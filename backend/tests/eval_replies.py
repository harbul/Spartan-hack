"""AI eval: runs Job 2 (and the Job 1/4 privacy check) against data/test_replies.json.

Run by hand, not by pytest: `python tests/eval_replies.py` from backend/.
Pass at 18/20 or better on need type and priority band. Rerun after every
prompt change. Any device or diagnosis word in a resident message fails the run.

Implements: PLAN.md §17 (AI eval, privacy check).
Owner: P3 (AI).
"""

import re
import unicodedata
from pathlib import Path

TEST_REPLIES = Path(__file__).resolve().parents[2] / "data" / "test_replies.json"
PASS_THRESHOLD = 18

# Device and diagnosis words, EN/ES/VI, written without accents (matching ignores them).
PRIVACY_WORDS: list[str] = [
    # English
    "oxygen", "concentrator", "dialysis", "kidney", "insulin", "diabetes", "diabetic",
    "wheelchair", "ventilator", "cpap",
    # Spanish
    "oxigeno", "concentrador", "dialisis", "rinon", "insulina", "diabetico", "diabetica",
    "silla de ruedas", "respirador",
    # Vietnamese
    "oxy", "may tho", "loc than", "chay than", "than nhan tao", "tieu duong", "xe lan",
]


def _plain(text: str) -> str:
    """Lowercase, accents removed (Vietnamese đ -> d), so 'Oxígeno' and 'lọc thận' match."""
    text = text.lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def privacy_violations(text: str) -> list[str]:
    """Return the privacy words found in a resident-facing message."""
    plain = _plain(text)
    return [w for w in PRIVACY_WORDS if re.search(rf"\b{re.escape(w)}\b", plain)]


def run_eval(path: Path = TEST_REPLIES) -> int:
    """Assess every labeled reply, compare need type and band, print a table, return the pass count."""
    ...


if __name__ == "__main__":
    run_eval()
