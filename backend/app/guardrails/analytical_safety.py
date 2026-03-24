"""Analytical claim validation guardrails."""

from __future__ import annotations

import re

CAUSAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bcaused?\s+by\b", re.IGNORECASE),
    re.compile(r"\bresulted?\s+in\b", re.IGNORECASE),
    re.compile(r"\bled\s+to\b", re.IGNORECASE),
    re.compile(r"\bbecause\s+of\b", re.IGNORECASE),
    re.compile(r"\bdriving\b", re.IGNORECASE),
    re.compile(r"\bdue\s+to\b", re.IGNORECASE),
    re.compile(r"\bdirectly\s+impact(?:s|ed|ing)?\b", re.IGNORECASE),
    re.compile(r"\bas\s+a\s+result\s+of\b", re.IGNORECASE),
]

ABSOLUTE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\balways\b", re.IGNORECASE),
    re.compile(r"\bnever\b", re.IGNORECASE),
    re.compile(r"\ball\s+customers?\b", re.IGNORECASE),
    re.compile(r"\bevery\s+\w+", re.IGNORECASE),
    re.compile(r"\bnone\s+of\b", re.IGNORECASE),
    re.compile(r"\bno\s+(?:customer|user|order)s?\b", re.IGNORECASE),
    re.compile(r"\b100\s*%\b", re.IGNORECASE),
    re.compile(r"\b0\s*%\b", re.IGNORECASE),
]

UNCERTAINTY_MARKERS: list[re.Pattern[str]] = [
    re.compile(r"\bapproximately\b", re.IGNORECASE),
    re.compile(r"\broughly\b", re.IGNORECASE),
    re.compile(r"\babout\b", re.IGNORECASE),
    re.compile(r"\bestimated?\b", re.IGNORECASE),
    re.compile(r"\blikely\b", re.IGNORECASE),
    re.compile(r"\bsuggests?\b", re.IGNORECASE),
    re.compile(r"\bmay\b", re.IGNORECASE),
    re.compile(r"\bmight\b", re.IGNORECASE),
    re.compile(r"\btends?\s+to\b", re.IGNORECASE),
    re.compile(r"\bin\s+general\b", re.IGNORECASE),
]

SMALL_SAMPLE_THRESHOLD = 30
COVERAGE_THRESHOLD = 0.9


def check_causal_claims(text: str) -> list[str]:
    """Flag causal language when only correlation data exists.

    Returns a list of flagged phrases found in the text.
    """
    flagged: list[str] = []
    for pattern in CAUSAL_PATTERNS:
        for match in pattern.finditer(text):
            flagged.append(match.group())
    return flagged


def check_absolute_claims(text: str, row_count: int | None = None) -> list[str]:
    """Flag absolute claims when sample may be small.

    Returns a list of flagged phrases. Adds extra context when row_count is
    below the small-sample threshold.
    """
    flagged: list[str] = []
    for pattern in ABSOLUTE_PATTERNS:
        for match in pattern.finditer(text):
            phrase = match.group()
            if row_count is not None and row_count < SMALL_SAMPLE_THRESHOLD:
                flagged.append(
                    f"{phrase} (small sample: n={row_count})"
                )
            else:
                flagged.append(phrase)
    return flagged


def check_uncertainty_markers(
    text: str, data_coverage: float | None = None
) -> list[str]:
    """Suggest uncertainty markers when data coverage is incomplete.

    Returns a list of suggestions. If the text already contains hedging
    language, those are acknowledged in the output.
    """
    suggestions: list[str] = []

    if data_coverage is not None and data_coverage >= COVERAGE_THRESHOLD:
        return suggestions

    existing = [p for p in UNCERTAINTY_MARKERS if p.search(text)]

    if data_coverage is not None and data_coverage < COVERAGE_THRESHOLD:
        coverage_pct = f"{data_coverage * 100:.0f}%"
        if not existing:
            suggestions.append(
                f"Data coverage is {coverage_pct} — consider adding hedging language "
                f"(e.g. 'approximately', 'roughly', 'about')"
            )
        else:
            suggestions.append(
                f"Data coverage is {coverage_pct} — verify hedging language is sufficient"
            )
    elif data_coverage is None and not existing:
        suggestions.append(
            "Consider adding uncertainty markers when data coverage is unknown"
        )

    return suggestions


def run_analytical_safety_checks(
    text: str,
    row_count: int | None = None,
    data_coverage: float | None = None,
) -> dict:
    """Run all analytical safety checks.

    Returns a dict with:
        - ``causal_flags``: phrases implying causation
        - ``absolute_flags``: absolute claims
        - ``uncertainty_suggestions``: hedging suggestions
        - ``issues``: combined list of all flagged items
        - ``suggestions``: combined list of all suggestions
    """
    causal_flags = check_causal_claims(text)
    absolute_flags = check_absolute_claims(text, row_count=row_count)
    uncertainty_suggestions = check_uncertainty_markers(text, data_coverage=data_coverage)

    issues: list[str] = []
    if causal_flags:
        issues.append(
            f"Causal language detected ({', '.join(repr(f) for f in causal_flags)}) "
            f"— ensure causation is supported, not just correlation"
        )
    if absolute_flags:
        issues.append(
            f"Absolute claims detected ({', '.join(repr(f) for f in absolute_flags)}) "
            f"— consider qualifying with sample size or confidence"
        )

    suggestions: list[str] = list(uncertainty_suggestions)

    return {
        "causal_flags": causal_flags,
        "absolute_flags": absolute_flags,
        "uncertainty_suggestions": uncertainty_suggestions,
        "issues": issues,
        "suggestions": suggestions,
    }
