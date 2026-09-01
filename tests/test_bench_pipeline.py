"""Fast unit tests for stage-level benchmark utilities (Issue #3)."""
from __future__ import annotations

import tracemalloc

from benchmarks.bench_pipeline import measure_stage, synth_audio
from benchmarks.system_info import collect_system_info


def test_measure_stage_reports_expected_schema():
    tracemalloc.start()
    try:
        value, stats = measure_stage("unit_stage", lambda: sum(range(1000)))
    finally:
        tracemalloc.stop()

    assert value == 499500
    assert stats["stage"] == "unit_stage"
    assert stats["elapsed_s"] >= 0
    assert stats["python_peak_increment_mb"] >= 0
    assert "rss_delta_mb" in stats


def test_synth_audio_is_created_with_expected_size(tmp_path):
    audio = synth_audio(tmp_path / "test.wav", seconds=0.1, sr=1000, seed=7)
    assert audio.exists()
    assert audio.stat().st_size > 44  # WAV header plus samples


def test_system_info_has_reproducibility_basics():
    info = collect_system_info()
    assert info["os"]
    assert info["python"]
    assert "numpy" in info["packages"]
    assert "scipy" in info["packages"]
