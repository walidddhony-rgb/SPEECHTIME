"""Tests for the benchmarks package (Issue #3 groundwork)."""
from __future__ import annotations

import pytest

from benchmarks.normalize_ar import normalize_ar


class TestNormalizeAr:
    def test_diacritics_removed(self):
        assert normalize_ar("مُحَمَّد") == normalize_ar("محمد")

    def test_alef_hamza_unified(self):
        assert normalize_ar("إسلام") == normalize_ar("اسلام")
        assert normalize_ar("أحمد") == normalize_ar("احمد")
        assert normalize_ar("آمنة") == normalize_ar("امنه")

    def test_ta_marbuta_and_alef_maqsura(self):
        assert normalize_ar("مدرسة") == normalize_ar("مدرسه")
        assert normalize_ar("على") == normalize_ar("علي")

    def test_hamza_seats(self):
        assert normalize_ar("سؤال") == normalize_ar("سوال")
        assert normalize_ar("شئ") == normalize_ar("شي")

    def test_tatweel_removed(self):
        assert normalize_ar("الـــله") == normalize_ar("الله")

    def test_punctuation_and_case(self):
        assert normalize_ar("Hello, World!") == "hello world"

    def test_whitespace_collapsed(self):
        assert normalize_ar("  نصٌ   ما   ") == "نص ما"

    def test_empty(self):
        assert normalize_ar("") == ""


jiwer = pytest.importorskip("jiwer", reason="jiwer required for WER tests")

from benchmarks.evaluate_wer import evaluate_pair  # noqa: E402


class TestEvaluatePair:
    def test_identical_zero_errors(self):
        scores = evaluate_pair("مرحبا بالعالم", "مرحبا بالعالم")
        assert scores["WER"] == 0.0
        assert scores["CER"] == 0.0

    def test_one_substitution_of_three(self):
        scores = evaluate_pair("واحد اثنين ثلاثة", "واحد اثنين أربعة")
        assert scores["WER"] == pytest.approx(1 / 3, abs=1e-3)

    def test_normalization_not_penalized(self):
        scores = evaluate_pair("الْقُرْآنُ كِتَابٌ", "القران كتاب")
        assert scores["WER"] == 0.0

    def test_insertion_counts(self):
        scores = evaluate_pair("كلمة", "كلمة زائدة")
        assert scores["WER"] == pytest.approx(1.0, abs=1e-3)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            evaluate_pair("", "نص")
