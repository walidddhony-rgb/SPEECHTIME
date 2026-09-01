"""Focused correctness tests for TextGenerator (Issue #1 baseline)."""
from __future__ import annotations

from src.text_generator import TextGenerator


def _clusters() -> list[dict]:
    return [
        {
            "id": 0,
            "segments": [
                {
                    "index": 0,
                    "start": 0,
                    "end": 9,
                    "start_seconds": 0.0,
                    "end_seconds": 0.009,
                    "score": 1.0,
                },
                {
                    "index": 2,
                    "start": 20,
                    "end": 29,
                    "start_seconds": 0.02,
                    "end_seconds": 0.029,
                    "score": 1.0,
                },
            ],
        },
        {
            "id": 1,
            "segments": [
                {
                    "index": 1,
                    "start": 10,
                    "end": 19,
                    "start_seconds": 0.01,
                    "end_seconds": 0.019,
                    "score": 1.0,
                }
            ],
        },
    ]


def test_generate_orders_labeled_segments_by_time():
    result = TextGenerator().generate(_clusters(), {0: "ا", 1: "ب"}, 30, 1000)

    assert [item["character"] for item in result] == ["ا", "ب", "ا"]
    assert [item["start"] for item in result] == [0, 10, 20]
    assert [item["end"] for item in result] == [9, 19, 29]


def test_generate_ignores_unlabeled_clusters():
    result = TextGenerator().generate(_clusters(), {1: "ب"}, 30, 1000)

    assert len(result) == 1
    assert result[0]["character"] == "ب"
    assert result[0]["start"] == 10


def test_generate_empty_labels_returns_empty_result():
    assert TextGenerator().generate(_clusters(), {}, 30, 1000) == []
