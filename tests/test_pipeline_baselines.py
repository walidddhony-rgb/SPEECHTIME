"""Correctness baselines required before optimizing the audio pipeline."""
from __future__ import annotations

import numpy as np

from src.audio_processor import AudioProcessor
from src.clusterer import SegmentClusterer


def _membership(clusters: list[dict]) -> list[tuple[int, ...]]:
    """Return order-independent cluster memberships for stable comparison."""
    return sorted(
        tuple(sorted(segment["index"] for segment in cluster["segments"]))
        for cluster in clusters
    )


def test_segment_count_and_sample_timing_are_stable():
    audio = np.arange(100, dtype=np.float64)
    segments = AudioProcessor().extract_segments(
        audio,
        sample_rate=1000,
        segment_ms=10.0,
        hop_ms=5.0,
    )

    assert len(segments) == 19
    assert segments[0]["start"] == 0
    assert segments[0]["end"] == 9
    assert segments[-1]["start"] == 90
    assert segments[-1]["end"] == 99
    assert [segment["index"] for segment in segments] == list(range(19))


def test_segment_times_are_monotonic_and_match_sample_rate():
    audio = np.arange(100, dtype=np.float64)
    segments = AudioProcessor().extract_segments(
        audio,
        sample_rate=1000,
        segment_ms=10.0,
        hop_ms=5.0,
    )

    assert all(
        left["start_seconds"] < right["start_seconds"]
        for left, right in zip(segments, segments[1:])
    )
    assert segments[0]["start_seconds"] == 0.0
    assert segments[0]["end_seconds"] == 0.009
    assert segments[-1]["start_seconds"] == 0.09
    assert segments[-1]["end_seconds"] == 0.099


def test_segments_are_views_of_source_audio():
    audio = np.arange(100, dtype=np.float64)
    segments = AudioProcessor().extract_segments(
        audio,
        sample_rate=1000,
        segment_ms=10.0,
        hop_ms=5.0,
    )

    assert all(np.shares_memory(segment["data"], audio) for segment in segments)


def test_float32_and_float64_produce_same_cluster_membership():
    processor = AudioProcessor()
    signal32 = np.tile(np.array([0.0, 1.0, 0.0, -1.0], dtype=np.float32), 25)
    signal64 = signal32.astype(np.float64)
    segments32 = processor.extract_segments(signal32, 1000, 10.0, 10.0)
    segments64 = processor.extract_segments(signal64, 1000, 10.0, 10.0)

    clusters32 = SegmentClusterer(similarity_threshold=0.99).cluster(segments32)
    clusters64 = SegmentClusterer(similarity_threshold=0.99).cluster(segments64)

    assert _membership(clusters32) == _membership(clusters64)
    assert len(clusters32) == len(clusters64)
