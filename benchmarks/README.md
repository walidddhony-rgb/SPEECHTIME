# Benchmarks & Evaluation

Reproducible measurement toolkit for SpeechScribe — the groundwork for the
scientific validation phase (WER/CER benchmarking and time studies).

## Why normalization?

Raw WER on unnormalized Arabic punishes orthographic variants that do not
change meaning (diacritics, hamza seats, ta marbuta, alef maqsura).
`benchmarks/normalize_ar.py` applies a conservative normalization before
scoring so that engine errors are counted, not spelling conventions.

## Install

    pip install -e ".[bench]"

## WER/CER evaluation

    python -m benchmarks.evaluate_wer --reference truth.txt --hypothesis out.txt --engine whisper-small

Writes JSON to `benchmarks/results/eval.json` (git-ignored) and prints
WER / CER / MER / WIL.

## Pipeline performance (Issues #1, #3)

    python -m benchmarks.bench_pipeline --seconds 5 30 60

Synthesizes deterministic audio, runs the clustering pipeline through the
public API (`src.SpeechTranscriber`), and reports wall time plus peak
allocated memory (tracemalloc) per duration. Results land in
`benchmarks/results/pipeline.json`.

## Evaluation protocol (Phase 2)

- Datasets: Mozilla Common Voice (Arabic, CC-0), MGB-2, MediaSpeech
  (Arabic), plus a small self-recorded set with manual ground truth.
- Every engine must be scored on identical segments with identical
  normalization; hardware and library versions are recorded with results.
- Time-to-verified-transcript (TTVT) = machine runtime + human correction
  time until a zero-error transcript; measured per condition.

Published result tables will live in `docs/benchmarks.md`.
