"""Stage-level performance benchmark for the clustering pipeline (Issues #1, #3).

Run locally from the repository root after ``pip install -e '.[bench]'``:

    python -m benchmarks.bench_pipeline --seconds 5 30 60

The report records reproducible system metadata plus independent measurements
for ``load_audio``, ``extract_segments``, and ``cluster_segments``. It does
not write review/transcript files and is deliberately excluded from CI.
"""
from __future__ import annotations

import argparse
import gc
import json
import time
import tracemalloc
from pathlib import Path
from typing import Any, Callable

import numpy as np

from benchmarks.system_info import collect_system_info


def _rss_mb() -> float | None:
    try:
        import psutil

        return round(psutil.Process().memory_info().rss / (1024 * 1024), 2)
    except Exception:
        return None


def _mb(value: int) -> float:
    return round(value / (1024 * 1024), 3)


def measure_stage(label: str, action: Callable[[], Any]) -> tuple[Any, dict]:
    """Run one stage and return its result plus time/allocation/RSS deltas."""
    gc.collect()
    current_before, _ = tracemalloc.get_traced_memory()
    rss_before = _rss_mb()
    tracemalloc.reset_peak()
    started = time.perf_counter()
    result = action()
    elapsed = time.perf_counter() - started
    current_after, peak_after = tracemalloc.get_traced_memory()
    rss_after = _rss_mb()
    return result, {
        "stage": label,
        "elapsed_s": round(elapsed, 4),
        "python_alloc_delta_mb": _mb(current_after - current_before),
        "python_peak_increment_mb": _mb(max(0, peak_after - current_before)),
        "rss_before_mb": rss_before,
        "rss_after_mb": rss_after,
        "rss_delta_mb": None
        if rss_before is None or rss_after is None
        else round(rss_after - rss_before, 2),
    }


def synth_audio(path: Path, seconds: float, sr: int = 16000, seed: int = 42) -> Path:
    """Create deterministic tones plus noise: stable, non-trivial cluster input."""
    from scipy.io import wavfile

    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * sr)) / sr
    signal = (
        0.4 * np.sin(2 * np.pi * 440 * t)
        + 0.3 * np.sin(2 * np.pi * 880 * t)
        + 0.2 * np.sin(2 * np.pi * 1320 * t)
        + 0.05 * rng.standard_normal(t.size)
    )
    wavfile.write(str(path), sr, (signal * 16383).astype(np.int16))
    return path


def _count_items(value: Any) -> int | None:
    try:
        return len(value)
    except TypeError:
        return None


def run_once(audio_path: str) -> dict:
    """Profile the three proven in-memory pipeline stages separately."""
    try:
        from src.transcriber import SpeechTranscriber
    except Exception as exc:
        raise SystemExit(
            f"Cannot import SpeechTranscriber from 'src.transcriber' ({exc}). "
            "Run this script from the repository root."
        )

    transcriber = SpeechTranscriber(
        audio_path=audio_path,
        segment_ms=25.0,
        hop_ms=12.5,
        similarity_threshold=0.85,
    )
    tracemalloc.start()
    total_started = time.perf_counter()
    try:
        _, load = measure_stage("load_audio", transcriber.load_audio)
        _, extract = measure_stage("extract_segments", transcriber.extract_segments)
        clusters, cluster = measure_stage("cluster_segments", transcriber.cluster_segments)
        _, total_peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    return {
        "stages": {
            "load_audio": load,
            "extract_segments": extract,
            "cluster_segments": cluster,
        },
        "segments_extracted": _count_items(getattr(transcriber, "segments", None)),
        "clusters_created": _count_items(clusters),
        "total": {
            "elapsed_s": round(time.perf_counter() - total_started, 4),
            "peak_alloc_mb": _mb(total_peak),
            "rss_after_mb": _rss_mb(),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="SpeechScribe stage-level pipeline benchmark")
    parser.add_argument("--seconds", nargs="+", type=float, default=[5, 30, 60])
    parser.add_argument("--sr", type=int, default=16000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json", default="benchmarks/results/pipeline.json")
    args = parser.parse_args()
    if any(seconds <= 0 for seconds in args.seconds):
        parser.error("--seconds values must be positive")

    tmp_dir = Path("benchmarks/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for seconds in args.seconds:
        wav = synth_audio(
            tmp_dir / f"bench_{int(seconds)}s.wav", seconds, sr=args.sr, seed=args.seed
        )
        print(f"[bench] {int(seconds)}s audio -> {wav}")
        row = run_once(str(wav))
        row["audio_seconds"] = seconds
        row["sample_rate_hz"] = args.sr
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False, indent=2))

    report = {
        "schema_version": "1.0",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "system": collect_system_info(),
        "config": {"segment_ms": 25.0, "hop_ms": 12.5, "similarity_threshold": 0.85},
        "rows": rows,
    }
    out = Path(args.json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[bench] wrote {out}")
    print("\n| duration_s | load_s | extract_s | cluster_s | peak_alloc_mb |")
    print("|---:|---:|---:|---:|---:|")
    for row in rows:
        stages = row["stages"]
        print(
            f"| {int(row['audio_seconds'])} | {stages['load_audio']['elapsed_s']} "
            f"| {stages['extract_segments']['elapsed_s']} "
            f"| {stages['cluster_segments']['elapsed_s']} "
            f"| {row['total']['peak_alloc_mb']} |"
        )


if __name__ == "__main__":
    main()
