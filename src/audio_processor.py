"""Audio processing utilities."""
from __future__ import annotations

import numpy as np
from scipy.io import wavfile


class AudioProcessor:
    """Handle WAV loading, normalization, and segment extraction."""

    def load(self, path: str) -> tuple[int, np.ndarray]:
        """Load a WAV file, convert it to mono float32, and normalize it.

        Float32 has more than sufficient precision for the segment-comparison
        pipeline and occupies half the memory of the former float64 format.
        Normalization operations are in-place after the required input conversion.
        """
        sample_rate, audio = wavfile.read(path)

        if audio.ndim == 2:
            # Explicit float32 keeps stereo averaging from using NumPy's float64 default.
            audio = audio.mean(axis=1, dtype=np.float32)
        else:
            audio = audio.astype(np.float32, copy=False)

        audio -= np.mean(audio, dtype=np.float32)
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio /= max_val

        return sample_rate, audio

    def extract_segments(
        self,
        audio: np.ndarray,
        sample_rate: int,
        segment_ms: float = 25.0,
        hop_ms: float = 12.5,
    ) -> list[dict]:
        """Extract overlapping segment metadata; each data field is a NumPy view."""
        segment_length = int(round(sample_rate * segment_ms / 1000.0))
        hop_length = int(round(sample_rate * hop_ms / 1000.0))
        if segment_length <= 0 or hop_length <= 0:
            raise ValueError("segment_ms and hop_ms must produce positive lengths")

        segments = []
        for start in range(0, len(audio) - segment_length + 1, hop_length):
            end = start + segment_length
            segments.append(
                {
                    "index": len(segments),
                    "start": start,
                    "end": end - 1,
                    "data": audio[start:end],
                    "start_seconds": start / sample_rate,
                    "end_seconds": (end - 1) / sample_rate,
                    "labeled": False,
                    "cluster_id": -1,
                }
            )

        return segments
