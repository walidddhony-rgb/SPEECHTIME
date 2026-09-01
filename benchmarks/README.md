# Benchmarks & Evaluation

Reproducible measurement toolkit for SpeechScribe. It supports two distinct
questions: **how correct is a transcript?** (WER/CER) and **what resources does
the clustering pipeline consume?** (time and memory per stage).

## Install

```powershell
pip install -e ".[bench]"
```

## Arabic WER/CER evaluation

```powershell
python -m benchmarks.evaluate_wer --reference truth.txt --hypothesis out.txt --engine whisper-small
```

The evaluator writes WER, CER, MER and WIL to JSON. It first applies a
conservative Arabic normalization: removes diacritics and tatweel, unifies alef
variants and hamza seats, normalizes ta marbuta/alef maqsura, removes punctuation,
and collapses whitespace. This avoids counting orthographic conventions as ASR
errors.

## Stage-level pipeline benchmark

```powershell
python -m benchmarks.bench_pipeline --seconds 5 30 60
```

The benchmark creates deterministic WAV files and independently measures:

| Stage | What it diagnoses |
|---|---|
| `load_audio` | Audio decoding and base audio-memory cost |
| `extract_segments` | Segment storage/copying cost |
| `cluster_segments` | Clustering algorithm time and allocation cost |

The report includes operating system, Python, installed package versions, CPU
core count and physical memory. Results are saved to
`benchmarks/results/pipeline.json`; generated WAVs go to `benchmarks/tmp/`.
Both locations are intentionally ignored by Git.

> **Important:** Do not upload raw benchmark results through the GitHub browser:
> browser uploads bypass `.gitignore`. Keep the JSON local and later publish a
> reviewed, anonymized results table in `docs/benchmarks.md` with the hardware
> description and command used.

## Reproducibility protocol

- Use identical `--seconds`, `--sr`, `--seed`, segment, hop and threshold values
  when comparing code versions.
- Close resource-heavy software where possible; run each condition three times
  and report the median in published tables.
- Record the full report, command, commit SHA and hardware details.
- For ASR accuracy, score each engine on identical reference transcripts with
  `evaluate_wer.py`; do not compare raw scores produced under different text
  normalization rules.

## Phase 2 protocol

- Datasets: Mozilla Common Voice Arabic, MGB-2, MediaSpeech Arabic, plus a small
  self-recorded set with manually verified ground truth.
- Time-to-verified-transcript (TTVT) = machine runtime + human correction time
  until the transcript is verified against the recording.
- Published final result tables belong in `docs/benchmarks.md`.
