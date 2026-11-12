from __future__ import annotations

import math
from collections.abc import Sequence

from modules.spec import Spec

NO_ANSWER_TOPICS = frozenset({"sifir_ref", "trace"})
MATCH_PAIRS = 6


def sifir_ref_sheets(tables_or_count: int | Sequence[int]) -> int:
    """Calculate the number of sheets required for multiplication reference tables (6 per sheet)."""
    count = tables_or_count if isinstance(tables_or_count, int) else len(tables_or_count)
    return math.ceil(count / 6)


def cards_per_sheet(spec: Spec, topic: str) -> int:
    """Return the number of problem cards for a practice sheet of the given topic."""
    if topic == "grid":
        return 1
    if topic == "count":
        return 12
    if topic == "add":
        return 16 if spec.add_digits == 3 else 20
    if topic == "sub":
        return 16 if spec.sub_digits == 3 else 20
    if topic == "sifir":
        return spec.sifir_n
    if topic == "div":
        return 8 if spec.div_digits == 3 else 12
    if topic == "sifir_ref":
        return len(spec.sifir_tables)
    if topic == "trace":
        return 4
    if topic == "missing":
        return 12
    if topic == "match":
        return 3
    raise ValueError(f"Unknown topic: {topic}")


def plan_sheets(spec: Spec) -> list[tuple[str, str, int]]:
    """Return ordered list of (kind, topic, sheet_index) for content and answer sheets.

    kind: 'content' or 'answer'
    topic: a selected worksheet topic
    sheet_index: 0-based per-topic index

    Accounting rules:
    - pages counts content sheets in total.
    - sifir_ref needs ceil(len(sifir_tables) / 6) sheets.
    - Remaining sheets go round-robin to practice topics in canonical order.
    - Answer sheets follow all content sheets in the same order.
    - Topics in NO_ANSWER_TOPICS have no answer sheet.
    - Maximum PDF length is 40 pages.
    """
    if spec.pages < 1 or spec.pages > 20:
        raise ValueError(f"pages must be between 1 and 20, got {spec.pages}")

    has_ref = "sifir_ref" in spec.t
    ref_count = sifir_ref_sheets(spec.sifir_tables) if has_ref else 0
    practice_topics = [t for t in spec.t if t != "sifir_ref"]
    min_pages = ref_count + len(practice_topics)

    if spec.pages < min_pages:
        raise ValueError(
            f"pages ({spec.pages}) is less than minimum required ({min_pages})"
        )
    if not practice_topics and spec.pages != ref_count:
        raise ValueError(
            f"pages ({spec.pages}) must match ref count ({ref_count}) when only ref selected"
        )

    # Distribute practice sheets
    practice_pages_needed = spec.pages - ref_count
    practice_seq: list[tuple[str, int]] = []
    if practice_topics:
        topic_counts: dict[str, int] = {t: 0 for t in practice_topics}
        idx = 0
        while len(practice_seq) < practice_pages_needed:
            topic = practice_topics[idx % len(practice_topics)]
            sheet_idx = topic_counts[topic]
            topic_counts[topic] += 1
            practice_seq.append((topic, sheet_idx))
            idx += 1

    # First pass: canonical order of selected topics
    content_sheets: list[tuple[str, str, int]] = []
    for topic in spec.t:
        if topic == "sifir_ref":
            for r in range(ref_count):
                content_sheets.append(("content", "sifir_ref", r))
        else:
            content_sheets.append(("content", topic, 0))

    # Remaining practice sheets (after sheet 0 of each practice topic)
    if practice_topics:
        for topic, sheet_idx in practice_seq[len(practice_topics):]:
            content_sheets.append(("content", topic, sheet_idx))

    # Answer sheets (if ans=1) follow content sheets that need answers
    answer_sheets: list[tuple[str, str, int]] = []
    if spec.ans == 1:
        for _kind, topic, sheet_idx in content_sheets:
            if topic not in NO_ANSWER_TOPICS:
                answer_sheets.append(("answer", topic, sheet_idx))

    total_sheets = content_sheets + answer_sheets
    if len(total_sheets) > 40:
        raise ValueError(f"Total PDF sheets ({len(total_sheets)}) exceeds maximum 40")

    return total_sheets
