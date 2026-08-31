"""
Main transcriber module for SpeechScribe.
"""

import argparse
import csv
import json
from pathlib import Path
from datetime import timedelta

import numpy as np
from scipy.io import wavfile

from .audio_processor import AudioProcessor
from .clusterer import SegmentClusterer
from .text_generator import TextGenerator
from .utils import format_time, seconds_to_srt_time


class SpeechTranscriber:
    """
    Semi-automatic speech transcription system.
    """
    
    def __init__(
        self,
        audio_path,
        segment_ms=25.0,
        hop_ms=12.5,
        similarity_threshold=0.85,
    ):
        self.audio_path = Path(audio_path)
        self.segment_ms = segment_ms
        self.hop_ms = hop_ms
        self.similarity_threshold = similarity_threshold
        
        self.audio_processor = AudioProcessor()
        self.clusterer = SegmentClusterer(
            similarity_threshold=similarity_threshold
        )
        self.text_generator = TextGenerator()
        
        self.sample_rate = None
        self.audio = None
        self.segments = []
        self.clusters = []
        self.labels = {}
        self.text_result = []
    
    def load_audio(self):
        """Load audio file."""
        print("Loading audio file...")
        self.sample_rate, self.audio = self.audio_processor.load(
            str(self.audio_path)
        )
        duration = len(self.audio) / self.sample_rate
        print(f"Audio loaded - Duration: {format_time(duration)}")
    
    def extract_segments(self):
        """Extract audio segments."""
        print("Extracting audio segments...")
        self.segments = self.audio_processor.extract_segments(
            self.audio,
            self.sample_rate,
            self.segment_ms,
            self.hop_ms,
        )
        print(f"Extracted {len(self.segments)} segments")
    
    def cluster_segments(self):
        """Cluster similar segments."""
        print("Clustering similar segments...")
        self.clusters = self.clusterer.cluster(
            self.segments,
        )
        print(f"Created {len(self.clusters)} clusters")
    
    def save_clusters_for_review(self, output_path="clusters.json"):
        """Save clusters for manual review."""
        print(f"Saving clusters to {output_path}...")
        self.clusterer.save_clusters(
            self.clusters,
            output_path,
        )
        print(f"Saved: {output_path}")
    
    def create_labels_template(self, output_path="manual_labels.csv"):
        """Create template for manual labeling."""
        print(f"Creating {output_path}...")
        self.clusterer.create_labels_template(
            self.clusters,
            output_path,
        )
        print(f"Created: {output_path}")
        print(f"Clusters to label: {len(self.clusters)}")
    
    def load_manual_labels(self, input_path="manual_labels.csv"):
        """Load manual labels."""
        print(f"Loading labels from {input_path}...")
        self.labels = self.clusterer.load_labels(input_path)
        print(f"Loaded {len(self.labels)} labels")
    
    def generate_text(self):
        """Generate text from labels."""
        print("Generating text...")
        if not self.labels:
            raise ValueError("No labels loaded")
        
        self.text_result = self.text_generator.generate(
            self.clusters,
            self.labels,
            len(self.audio),
            self.sample_rate,
        )
        print(f"Generated {len(self.text_result)} text segments")
    
    def save_text(
        self,
        output_txt="output_text.txt",
        output_csv="output_text_details.csv",
        output_srt="output_subtitles.srt",
    ):
        """Save text in multiple formats."""
        print("Saving results...")
        self.text_generator.save(
            self.text_result,
            output_txt,
            output_csv,
            output_srt,
        )
        print(f"Saved:")
        print(f"  - {output_txt}")
        print(f"  - {output_csv}")
        print(f"  - {output_srt}")
    
    def print_statistics(self):
        """Print transcription statistics."""
        print("\n" + "=" * 60)
        print("Transcription Statistics")
        print("=" * 60)
        
        duration = len(self.audio) / self.sample_rate
        print(f"Audio duration: {format_time(duration)}")
        print(f"Segments extracted: {len(self.segments)}")
        print(f"Clusters created: {len(self.clusters)}")
        print(f"Clusters labeled: {len(self.labels)}")
        
        if self.clusters:
            top_clusters = self.clusters[:5]
            print("\nTop 5 most frequent clusters:")
            
            total_segments = sum(
                len(c["segments"])
                for c in self.clusters
            )
            
            for cluster in top_clusters:
                count = len(cluster["segments"])
                percentage = count / total_segments * 100
                label = self.labels.get(
                    cluster["id"],
                    "unlabeled",
                )
                
                print(
                    f"  Cluster {cluster['id']}: "
                    f"{count} times ({percentage:.1f}%) "
                    f"→ {label}"
                )
        
        print("=" * 60)
    
    def transcribe(self):
        """Run full transcription pipeline."""
        print("\n" + "=" * 60)
        print("SpeechScribe - Semi-Automatic Transcription")
        print("=" * 60 + "\n")
        
        # Stage 1: Load
        self.load_audio()
        
        # Stage 2: Extract
        self.extract_segments()
        
        # Stage 3: Cluster
        self.cluster_segments()
        
        # Stage 4: Save for review
        self.save_clusters_for_review()
        self.create_labels_template()
        
        print("\n" + "=" * 60)
        print("Manual Labeling Stage")
        print("=" * 60)
        print("1. Open clusters.json")
        print("2. Listen to representative samples")
        print("3. Open manual_labels.csv")
        print("4. Assign character to each cluster")
        print("5. Save the file")
        print("=" * 60 + "\n")
        
        input("Press Enter after completing labels...")
        
        # Stage 5: Load labels
        self.load_manual_labels()
        
        # Stage 6: Generate text
        self.generate_text()
        
        # Stage 7: Save
        self.save_text()
        
        # Stage 8: Statistics
        self.print_statistics()
        
        print("\nTranscription completed successfully! 🎉")


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="SpeechScribe - Semi-Automatic Speech Transcription"
    )
    
    parser.add_argument(
        "audio_path",
        type=str,
        help="Path to audio file (WAV format)",
    )
    
    parser.add_argument(
        "--segment-ms",
        type=float,
        default=25.0,
        help="Segment length in milliseconds (default: 25.0)",
    )
    
    parser.add_argument(
        "--hop-ms",
        type=float,
        default=12.5,
        help="Hop length in milliseconds (default: 12.5)",
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Similarity threshold (default: 0.85)",
    )
    
    parser.add_argument(
        "--labels",
        type=str,
        default=None,
        help="Path to manual labels CSV file",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="output_text.txt",
        help="Output text file path",
    )
    
    args = parser.parse_args()
    
    transcriber = SpeechTranscriber(
        audio_path=args.audio_path,
        segment_ms=args.segment_ms,
        hop_ms=args.hop_ms,
        similarity_threshold=args.threshold,
    )
    
    if args.labels:
        # Just generate text from existing labels
        transcriber.load_audio()
        transcriber.extract_segments()
        transcriber.cluster_segments()
        transcriber.load_manual_labels(args.labels)
        transcriber.generate_text()
        transcriber.save_text(output_txt=args.output)
    else:
        # Full pipeline
        transcriber.transcribe()


if __name__ == "__main__":
    main()