"""
Example usage of SpeechScribe.
"""

from src import SpeechTranscriber


def example_basic():
    """Basic transcription example."""
    transcriber = SpeechTranscriber(
        audio_path="audio.wav",
        segment_ms=25.0,
        similarity_threshold=0.85,
    )
    
    transcriber.transcribe()


def example_custom_params():
    """Transcription with custom parameters."""
    transcriber = SpeechTranscriber(
        audio_path="lecture.wav",
        segment_ms=20.0,  # Shorter segments
        hop_ms=10.0,
        similarity_threshold=0.90,  # Higher threshold
    )
    
    transcriber.transcribe()


def example_from_labels():
    """Generate text from existing labels."""
    transcriber = SpeechTranscriber(
        audio_path="audio.wav",
    )
    
    # Load audio and clusters
    transcriber.load_audio()
    transcriber.extract_segments()
    transcriber.cluster_segments()
    
    # Load existing labels
    transcriber.load_manual_labels("manual_labels.csv")
    
    # Generate and save text
    transcriber.generate_text()
    transcriber.save_text(
        output_txt="final_text.txt",
        output_csv="final_details.csv",
        output_srt="final_subtitles.srt",
    )


if __name__ == "__main__":
    # Run basic example
    example_basic()