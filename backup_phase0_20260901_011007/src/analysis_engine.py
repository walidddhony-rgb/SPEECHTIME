"""Real audio analysis engine for SpeechScribe.

Loads audio files, extracts segments, computes MFCC features, and clusters them
in a background-friendly way. Designed for Tkinter integration without freezing
the UI.
"""
from __future__ import annotations

import contextlib
import queue
import threading
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
from scipy.io import wavfile
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist

try:
    import soundfile as sf  # type: ignore
except ImportError:
    sf = None


@dataclass
class AnalysisProgress:
    """Progress update sent from background thread to UI."""
    stage: str
    percent: int
    message: str


@dataclass
class AnalysisResult:
    """Final analysis result containing segments, clusters, and timeline."""
    audio_path: Path
    sample_rate: int
    total_duration: float
    segment_count: int
    cluster_count: int
    cluster_assignments: np.ndarray
    segments_start_times: np.ndarray
    segments_end_times: np.ndarray
    features: np.ndarray
    cluster_labels: dict[int, int] = field(default_factory=dict)
    error: str | None = None


class AnalysisEngine:
    """Runs segmentation and clustering in a background thread."""

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._cancel = threading.Event()
        self._result: AnalysisResult | None = None

    @property
    def result(self) -> AnalysisResult | None:
        return self._result

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start_analysis(self, audio_path: str | Path, segment_ms: float = 25.0, overlap_ms: float = 12.5, max_clusters: int = 100):
        """Start background analysis. Returns immediately."""
        if self.is_running:
            raise RuntimeError("Analysis is already running.")
        self._cancel.clear()
        self._result = None
        self._thread = threading.Thread(
            target=self._run,
            args=(Path(audio_path), segment_ms, overlap_ms, max_clusters),
            daemon=True,
        )
        self._thread.start()

    def cancel(self):
        self._cancel.set()

    def get_progress(self) -> AnalysisProgress | None:
        """Non-blocking progress poll. Returns None if no update."""
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def _emit(self, stage: str, percent: int, message: str):
        self._queue.put(AnalysisProgress(stage, percent, message))

    def _run(self, audio_path: Path, segment_ms: float, overlap_ms: float, max_clusters: int):
        try:
            self._emit("loading", 5, "Loading audio file...")
            audio, sample_rate = self._load_audio(audio_path)
            self._emit("loading", 15, f"Loaded {audio_path.name} ({sample_rate} Hz)")

            if self._cancel.is_set():
                self._emit("cancelled", 0, "Cancelled by user.")
                return

            self._emit("segmenting", 25, "Extracting segments...")
            segments, start_times, end_times = self._extract_segments(audio, sample_rate, segment_ms, overlap_ms)
            self._emit("segmenting", 40, f"Extracted {len(segments)} segments")

            if self._cancel.is_set():
                self._emit("cancelled", 0, "Cancelled by user.")
                return

            self._emit("features", 55, "Computing MFCC features...")
            features = self._compute_mfcc_features(segments, sample_rate)
            self._emit("features", 65, f"Computed {features.shape[1]}-dimensional features")

            if self._cancel.is_set():
                self._emit("cancelled", 0, "Cancelled by user.")
                return

            self._emit("clustering", 80, "Clustering segments...")
            cluster_labels = self._cluster_features(features, max_clusters)
            cluster_count = len(np.unique(cluster_labels))
            self._emit("clustering", 95, f"Found {cluster_count} clusters")

            duration = len(audio) / sample_rate
            self._result = AnalysisResult(
                audio_path=audio_path,
                sample_rate=sample_rate,
                total_duration=duration,
                segment_count=len(segments),
                cluster_count=cluster_count,
                cluster_assignments=cluster_labels,
                segments_start_times=start_times,
                segments_end_times=end_times,
                features=features,
            )
            self._emit("complete", 100, f"Analysis complete: {cluster_count} clusters from {len(segments)} segments")
        except Exception as exc:
            self._emit("error", 0, f"Analysis failed: {exc}")

    def _load_audio(self, path: Path) -> tuple[np.ndarray, int]:
        """Load audio as mono float32 array. Supports WAV via stdlib, others via soundfile."""
        suffix = path.suffix.lower()
        if suffix == ".wav":
            sample_rate, audio = wavfile.read(str(path))
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            elif audio.dtype == np.int32:
                audio = audio.astype(np.float32) / 2147483648.0
            elif audio.dtype == np.uint8:
                audio = (audio.astype(np.float32) - 128) / 128.0
            else:
                audio = audio.astype(np.float32)
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            return audio, sample_rate

        if sf is None:
            raise RuntimeError("soundfile is required for non-WAV formats. Run: py -m pip install soundfile")

        audio, sample_rate = sf.read(str(path), dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        return audio, sample_rate

    def _extract_segments(self, audio: np.ndarray, sample_rate: int, segment_ms: float, overlap_ms: float):
        """Extract overlapping segments with a Hann window."""
        segment_samples = int(sample_rate * segment_ms / 1000)
        hop_samples = int(sample_rate * (segment_ms - overlap_ms) / 1000)
        if hop_samples <= 0:
            raise ValueError("Overlap must be smaller than segment length")

        segments = []
        start_times = []
        end_times = []
        window = np.hanning(segment_samples)

        for start in range(0, len(audio) - segment_samples + 1, hop_samples):
            end = start + segment_samples
            segment = audio[start:end] * window
            segments.append(segment)
            start_times.append(start / sample_rate)
            end_times.append(end / sample_rate)

        return np.array(segments), np.array(start_times), np.array(end_times)

    def _compute_mfcc_features(self, segments: np.ndarray, sample_rate: int, n_mfcc: int = 13):
        """Compute lightweight MFCC features from segment windows."""
        # FFT magnitude
        fft = np.fft.rfft(segments, axis=1)
        magnitude = np.abs(fft)
        power = magnitude ** 2

        # Mel filterbank
        n_fft = segments.shape[1]
        n_filters = 26
        mel_filters = self._mel_filterbank(sample_rate, n_fft, n_filters)
        mel_energy = power @ mel_filters.T
        mel_energy = np.where(mel_energy == 0, np.finfo(float).eps, mel_energy)

        # Log mel spectrogram
        log_mel = np.log(mel_energy)

        # DCT-II to get MFCC
        from scipy.fftpack import dct
        mfcc = dct(log_mel, type=2, axis=1, norm="ortho")[:, :n_mfcc]

        # Add deltas
        delta = np.zeros_like(mfcc)
        for t in range(1, len(mfcc) - 1):
            delta[t] = (mfcc[t + 1] - mfcc[t - 1]) / 2.0
        delta[0] = mfcc[1] - mfcc[0]
        delta[-1] = mfcc[-1] - mfcc[-2]

        return np.hstack([mfcc, delta])

    def _mel_filterbank(self, sample_rate: int, n_fft: int, n_filters: int):
        """Create a simple mel filterbank matrix."""
        def hz_to_mel(hz):
            return 2595 * np.log10(1 + hz / 700)

        def mel_to_hz(mel):
            return 700 * (10 ** (mel / 2595) - 1)

        low_mel = 0
        high_mel = hz_to_mel(sample_rate / 2)
        mel_points = np.linspace(low_mel, high_mel, n_filters + 2)
        hz_points = mel_to_hz(mel_points)
        bin_points = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

        filters = np.zeros((n_filters, n_fft // 2 + 1))
        for i in range(1, n_filters + 1):
            left, center, right = bin_points[i - 1], bin_points[i], bin_points[i + 1]
            for j in range(left, center):
                filters[i - 1, j] = (j - left) / (center - left + 1e-8)
            for j in range(center, right):
                filters[i - 1, j] = (right - j) / (right - center + 1e-8)
        return filters

    def _cluster_features(self, features: np.ndarray, max_clusters: int):
        """Hierarchical clustering with Ward linkage and cosine distance."""
        if len(features) < 2:
            return np.zeros(len(features), dtype=int)

        # Normalize features
        features = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-8)

        # Ward linkage requires Euclidean distance; use cosine for better audio separation
        distances = pdist(features, metric="cosine")
        linkage_matrix = linkage(distances, method="ward")
        labels = fcluster(linkage_matrix, t=max_clusters, criterion="maxclust")
        return labels - 1  # 0-based

    def get_cluster_summary(self) -> list[dict]:
        """Return a summary of clusters for the UI table."""
        if self._result is None:
            return []
        labels = self._result.cluster_assignments
        unique, counts = np.unique(labels, return_counts=True)
        summary = []
        for cluster_id, count in zip(unique, counts):
            summary.append({
                "id": f"C-{cluster_id:03d}",
                "samples": int(count),
                "label": "—",
                "state": "Pending",
            })
        return summary
