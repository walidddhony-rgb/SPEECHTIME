"""Pipeline performance benchmark: wall time + peak memory (Issues #1, #3).

Runs the clustering pipeline through the proven public API (the same
sequence used by the GUI worker: ``src.transcriber.SpeechTranscriber``
with load_audio -> extract_segments -> cluster_segments) on
deterministic synthetic audio and records, per duration:

- elapsed wall-clock seconds
- peak allocated memory (tracemalloc, MB)
- process RSS before/after (psutil, MB, optional)

Not part of CI. Run locally from the repository root:

    python -m benchmarks.bench_pipeline --seconds 5 30 60
    python -m benchmarks.bench_pipeline --seconds 600 --json benchmarks/results/pipeline.json

Notes:
- Synthesized WAVs go to ``benchmarks/tmp/`` (git-ignored).
- Only in-memory stages are measured; no review files are written.
"""
from __future__ import annotations

import argparse
import json
import time
import tracemalloc
from pathlib import Path

import numpy as np


def _rss_mb():
    try:
        import psutil

        return round(psutil.Process().memory_info().rss / (1024 * 1024), 2)
    except Exception:
        return None


def synth_audio(path: Path, seconds: float, sr: int = 16000, seed: int = 42) -> Path:
    """Deterministic mixture of tones + noise -> non-trivial clustering input."""
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


def run_once(audio_path: str) -> dict:
    try:
        from src.transcriber import SpeechTranscriber
    except Exception as exc:
        raise SystemExit(
            f"Cannot import SpeechTranscriber from 'src.transcriber' ({exc}). "
            "Run this script from the repository root."
        )

    rss_before = _rss_mb()
    tracemalloc.start()
    t0 = time.perf_counter()
    transcriber = SpeechTranscriber(
        audio_path=audio_path,
        segment_ms=25.0,
        hop_ms=12.5,
        similarity_threshold=0.85,
    )
    transcriber.load_audio()
    transcriber.extract_segments()
    transcriber.cluster_segments()
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "elapsed_s": round(elapsed, 3),
        "peak_alloc_mb": round(peak / (1024 * 1024), 2),
        "rss_before_mb": rss_before,
        "rss_after_mb": _rss_mb(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="SpeechScribe pipeline benchmark")
    parser.add_argument("--seconds", nargs="+", type=float, default=[5, 30, 60])
    parser.add_argument("--sr", type=int, default=16000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json", default="benchmarks/results/pipeline.json")
    args = parser.parse_args()

    tmp_dir = Path("benchmarks/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for seconds in args.seconds:
        wav = synth_audio(
            tmp_dir / f"bench_{int(seconds)}s.wav", seconds, sr=args.sr, seed=args.seed
        )
        print(f"[bench] {int(seconds)}s audio -> {wav}")
        stats = run_once(str(wav))
        stats["seconds"] = seconds
        rows.append(stats)
        print(f"        {stats}")

    out = Path(args.json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[bench] wrote {out}")
    print("\n| duration_s | elapsed_s | peak_alloc_mb |")
    print("|---:|---:|---:|")
    for r in rows:
        print(f"| {int(r['seconds'])} | {r['elapsed_s']} | {r['peak_alloc_mb']} |")


if __name__ == "__main__":
    main()
