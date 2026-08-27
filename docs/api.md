# API Reference

## SpeechTranscriber

### Constructor

```python
SpeechTranscriber(
    audio_path: str,
    segment_ms: float = 25.0,
    hop_ms: float = 12.5,
    similarity_threshold: float = 0.85,
)
```

### Methods

#### `load_audio()`
Load audio file.

#### `extract_segments()`
Extract audio segments.

#### `cluster_segments()`
Cluster similar segments.

#### `save_clusters_for_review(output_path)`
Save clusters to JSON.

#### `create_labels_template(output_path)`
Create labeling template.

#### `load_manual_labels(input_path)`
Load manual labels.

#### `generate_text()`
Generate text from labels.

#### `save_text(output_txt, output_csv, output_srt)`
Save text in multiple formats.

#### `transcribe()`
Run full pipeline.

## Example

```python
from src import SpeechTranscriber

transcriber = SpeechTranscriber("audio.wav")
transcriber.transcribe()
```