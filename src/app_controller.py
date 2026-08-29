"""Application services shared by the SpeechScribe desktop interface."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import contextlib
import wave


SUPPORTED_AUDIO_SUFFIXES = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}


@dataclass(frozen=True)
class AudioMetadata:
    """Basic metadata returned after validating an audio selection."""

    path: Path
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None
    sample_width_bits: int | None
    file_size_bytes: int
    format_name: str
    warning: str | None = None

    @property
    def file_name(self) -> str:
        return self.path.name

    @property
    def is_wav(self) -> bool:
        return self.path.suffix.lower() == ".wav"


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "Unknown duration"
    whole_seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(whole_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def inspect_audio_file(path: str | Path) -> AudioMetadata:
    """Validate the selected path and inspect WAV metadata without decoding audio.

    Non-WAV formats are accepted by the interface but receive a clear message:
    full decoding will be added when the real processing engine is connected.
    """
    audio_path = Path(path).expanduser().resolve()
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file was not found: {audio_path}")

    suffix = audio_path.suffix.lower()
    if suffix not in SUPPORTED_AUDIO_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_AUDIO_SUFFIXES))
        raise ValueError(f"Unsupported audio format ({suffix or 'no extension'}). Supported: {supported}")

    size_bytes = audio_path.stat().st_size
    format_name = suffix.lstrip(".").upper()

    if suffix != ".wav":
        return AudioMetadata(
            path=audio_path,
            duration_seconds=None,
            sample_rate=None,
            channels=None,
            sample_width_bits=None,
            file_size_bytes=size_bytes,
            format_name=format_name,
            warning=(
                f"{format_name} was selected successfully. Detailed metadata and processing "
                "are currently available for WAV files; conversion/decoder support comes next."
            ),
        )

    try:
        with contextlib.closing(wave.open(str(audio_path), "rb")) as audio:
            sample_rate = audio.getframerate()
            channels = audio.getnchannels()
            sample_width_bits = audio.getsampwidth() * 8
            frames = audio.getnframes()
    except wave.Error as exc:
        raise ValueError(f"The WAV file could not be read: {exc}") from exc

    duration = frames / sample_rate if sample_rate else None
    return AudioMetadata(
        path=audio_path,
        duration_seconds=duration,
        sample_rate=sample_rate,
        channels=channels,
        sample_width_bits=sample_width_bits,
        file_size_bytes=size_bytes,
        format_name=format_name,
    )
