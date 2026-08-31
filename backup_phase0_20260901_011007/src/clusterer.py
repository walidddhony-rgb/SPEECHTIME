"""
Segment clustering utilities.
"""

import csv
import json

import numpy as np


class SegmentClusterer:
    """Cluster similar audio segments."""
    
    def __init__(self, similarity_threshold=0.85):
        self.similarity_threshold = similarity_threshold
    
    def _normalize_signal(self, signal):
        """Normalize signal for comparison."""
        signal = np.asarray(signal, dtype=np.float64)
        signal = signal - np.mean(signal)
        norm = np.linalg.norm(signal)
        if norm == 0:
            return np.zeros_like(signal)
        return signal / norm
    
    def _compare_segments(self, seg1, seg2):
        """Compare two segments using dot product."""
        a = self._normalize_signal(seg1["data"])
        b = self._normalize_signal(seg2["data"])
        
        if len(a) != len(b):
            return 0.0
        
        return float(np.sum(a * b))
    
    def cluster(self, segments):
        """
        Cluster similar segments.
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            list: List of cluster dictionaries
        """
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
                    cluster["segments"].append({
                        "index": j,
                        "start": other["start"],
                        "end": other["end"],
                        "start_seconds": other["start_seconds"],
                        "end_seconds": other["end_seconds"],
                        "score": score,
                    })
                    used[j] = True
            
            if cluster["segments"]:
                clusters.append(cluster)
        
        # Sort by frequency
        #clusters.sort(
         #   key=lambda c: len(c["segments"]),
          #  reverse=True,
        #)
        
        # Renumber
        for idx, cluster in enumerate(clusters):
            cluster["id"] = idx
        
        return clusters
    
    def save_clusters(self, clusters, output_path):
        """Save clusters to JSON file."""
        # Create lightweight version
        clusters_lite = []
        
        for cluster in clusters:
            cluster_lite = {
                "id": cluster["id"],
                "count": len(cluster["segments"]),
                "representative": {
                    "start_seconds": (
                        cluster["representative"]["start_seconds"]
                    ),
                    "end_seconds": (
                        cluster["representative"]["end_seconds"]
                    ),
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
            json.dump(
                clusters_lite,
                f,
                indent=2,
                ensure_ascii=False,
            )
    
    def create_labels_template(self, clusters, output_path):
        """Create CSV template for manual labeling."""
        with open(
            output_path,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as f:
            writer = csv.writer(f)
            
            writer.writerow([
                "cluster_id",
                "character",
                "count",
                "first_occurrence_seconds",
                "notes",
            ])
            
            for cluster in clusters:
                writer.writerow([
                    cluster["id"],
                    "",
                    len(cluster["segments"]),
                    f"{cluster['segments'][0]['start_seconds']:.2f}",
                    "",
                ])
    
    def load_labels(self, input_path):
        """Load manual labels from CSV."""
        labels = {}
        
        with open(input_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                cluster_id = int(row["cluster_id"])
                character = row["character"].strip()
                
                if character:
                    labels[cluster_id] = character
        
        return labels