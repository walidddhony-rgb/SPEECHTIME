"""Tests for Step 4 audio-file metadata inspection."""
from __future__ import annotations

import wave
from pathlib import Path

import pytest

from src.app_controller import format_duration, inspect_audio_file


def make_test_wav(path: Path, *, frames: int = 8000, sample_rate: int = 8000) -> None:
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(b"\x00\x00" * frames)


def test_inspect_wav_reads_real_metadata(tmp_path: Path):
    sample = tmp_path / "sample.wav"
    make_test_wav(sample)

    metadata = inspect_audio_file(sample)

    assert metadata.is_wav
    assert metadata.duration_seconds == pytest.approx(1.0)
    assert metadata.sample_rate == 8000
    assert metadata.channels == 1
    assert metadata.sample_width_bits == 16
    assert format_duration(metadata.duration_seconds) == "00:00:01"


def test_non_wav_is_accepted_with_decoder_warning(tmp_path: Path):
    sample = tmp_path / "sample.mp3"
    sample.write_bytes(b"not an actual mp3")

    metadata = inspect_audio_file(sample)

    assert metadata.format_name == "MP3"
    assert metadata.duration_seconds is None
    assert metadata.warning is not None


def test_missing_file_raises_clear_error(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        inspect_audio_file(tmp_path / "missing.wav")
