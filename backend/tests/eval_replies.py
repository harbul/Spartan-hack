"""AI eval: runs Job 2 (and the Job 1/4 privacy check) against data/test_replies.json.

Run by hand, not by pytest: `python tests/eval_replies.py` from backend/.
Pass at 18/20 or better on need type and priority band. Rerun after every
prompt change. Any device or diagnosis word in a resident message fails the run.

Implements: PLAN.md §17 (AI eval, privacy check).
Owner: P3 (AI).
"""

from pathlib import Path

TEST_REPLIES = Path(__file__).resolve().parents[2] / "data" / "test_replies.json"
PASS_THRESHOLD = 18

# TODO(P3, §17): device/diagnosis words (oxygen, dialysis, insulin, wheelchair) and their ES/VI forms.
PRIVACY_WORDS: list[str] = []


def privacy_violations(text: str) -> list[str]:
    """Return the privacy words found in a resident-facing message."""
    ...


def run_eval(path: Path = TEST_REPLIES) -> int:
    """Assess every labeled reply, compare need type and band, print a table, return the pass count."""
    ...


if __name__ == "__main__":
    run_eval()
