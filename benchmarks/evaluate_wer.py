"""WER/CER evaluation with Arabic normalization (Issue #3).

Install:
    pip install -e ".[bench]"

Usage:
    python -m benchmarks.evaluate_wer --reference truth.txt --hypothesis out.txt --engine whisper-small

Metrics: WER, CER, MER, WIL via jiwer (https://jitsi.github.io/jiwer/).
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import jiwer

from benchmarks.normalize_ar import normalize_ar


@dataclass
class EvalResult:
    engine: str
    audio: str
    WER: float
    CER: float
    MER: float
    WIL: float
    elapsed_s: float


def evaluate_pair(reference: str, hypothesis: str) -> dict:
    """Return WER/CER/MER/WIL between two raw transcripts (normalized)."""
    ref = normalize_ar(reference)
    hyp = normalize_ar(hypothesis)
    if not ref or not hyp:
        raise ValueError("reference or hypothesis is empty after normalization")
    return {
        "WER": round(jiwer.wer(ref, hyp), 4),
        "CER": round(jiwer.cer(ref, hyp), 4),
        "MER": round(jiwer.mer(ref, hyp), 4),
        "WIL": round(jiwer.wil(ref, hyp), 4),
    }


def evaluate_files(
    reference_path: str,
    hypothesis_path: str,
    engine: str = "unknown",
    audio: str = "",
    out: str | None = None,
) -> EvalResult:
    ref = Path(reference_path).read_text(encoding="utf-8")
    hyp = Path(hypothesis_path).read_text(encoding="utf-8")
    t0 = time.perf_counter()
    scores = evaluate_pair(ref, hyp)
    result = EvalResult(
        engine=engine,
        audio=str(audio),
        elapsed_s=round(time.perf_counter() - t0, 4),
        **scores,
    )
    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(asdict(result), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SpeechScribe WER/CER evaluation with Arabic normalization"
    )
    parser.add_argument("--reference", required=True, help="ground-truth transcript file")
    parser.add_argument("--hypothesis", required=True, help="engine output file")
    parser.add_argument("--engine", default="unknown", help="engine name, e.g. whisper-small")
    parser.add_argument("--audio", default="", help="audio file path (recorded in results)")
    parser.add_argument("--out", default="benchmarks/results/eval.json")
    args = parser.parse_args()

    result = evaluate_files(
        args.reference,
        args.hypothesis,
        engine=args.engine,
        audio=args.audio,
        out=args.out,
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
