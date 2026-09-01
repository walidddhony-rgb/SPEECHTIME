"""Segment clustering utilities."""
from __future__ import annotations

import csv
import json

import numpy as np


class SegmentClusterer:
    """Cluster similar audio segments."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    def _normalize_signal(self, signal: np.ndarray) -> np.ndarray:
        """Normalize one signal without promoting float32 input to float64."""
        signal = np.asarray(signal)
        if signal.dtype.kind not in "fc":
            signal = signal.astype(np.float32)
        signal = signal - np.mean(signal, dtype=signal.dtype)
        norm = np.linalg.norm(signal)
        if norm == 0:
            return np.zeros_like(signal)
        return signal / norm

    def _compare_segments(self, seg1: dict, seg2: dict) -> float:
        """Compare two segments with a normalized dot product."""
        a = self._normalize_signal(seg1["data"])
        b = self._normalize_signal(seg2["data"])

        if len(a) != len(b):
            return 0.0

        return float(np.dot(a, b))

    def cluster(self, segments: list[dict]) -> list[dict]:
        """Greedily group segments that meet the configured similarity threshold."""
        if not segments:
            return []

        clusters = []
        used = [False] * len(segments)

        for i, seg in enumerate(segments):
            if used[i]:
                continue

            cluster = {
                "id": len(clusters),
                "segments": [],
                "representative": seg,
            }

            for j, other in enumerate(segments):
                if used[j]:
                    continue

                score = self._compare_segments(seg, other)
                if score >= self.similarity_threshold:
                    cluster["segments"].append(
                        {
                            "index": j,
                            "start": other["start"],
                            "end": other["end"],
                            "start_seconds": other["start_seconds"],
                            "end_seconds": other["end_seconds"],
                            "score": score,
                        }
                    )
                    used[j] = True

            if cluster["segments"]:
                clusters.append(cluster)

        for idx, cluster in enumerate(clusters):
            cluster["id"] = idx

        return clusters

    def save_clusters(self, clusters: list[dict], output_path: str) -> None:
        """Save a lightweight, JSON-serializable representation of clusters."""
        clusters_lite = []

        for cluster in clusters:
            cluster_lite = {
                "id": cluster["id"],
                "count": len(cluster["segments"]),
                "representative": {
                    "start_seconds": cluster["representative"]["start_seconds"],
                    "end_seconds": cluster["representative"]["end_seconds"],
                },
                "segments": [
                    {
                        "start_seconds": seg["start_seconds"],
                        "end_seconds": seg["end_seconds"],
                        "score": seg["score"],
                    }
                    for seg in cluster["segments"]
                ],
            }
            clusters_lite.append(cluster_lite)

        with open(output_path, "w", encoding="utf-8-sig") as f:
            json.dump(clusters_lite, f, indent=2, ensure_ascii=False)

    def create_labels_template(self, clusters: list[dict], output_path: str) -> None:
        """Create a CSV template for manual cluster labeling."""
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["cluster_id", "character", "count", "first_occurrence_seconds", "notes"]
            )

            for cluster in clusters:
                writer.writerow(
                    [
                        cluster["id"],
                        "",
                        len(cluster["segments"]),
                        f"{cluster['segments'][0]['start_seconds']:.2f}",
                        "",
                    ]
                )

    def load_labels(self, input_path: str) -> dict[int, str]:
        """Load non-empty manual labels from a CSV file."""
        labels = {}

        with open(input_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                character = row["character"].strip()
                if character:
                    labels[int(row["cluster_id"])] = character

        return labels
