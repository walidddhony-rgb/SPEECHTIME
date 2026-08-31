# Usage Guide

## Basic Usage

### Command Line

```bash
# Full transcription pipeline
python -m src.transcriber audio.wav

# With custom parameters
python -m src.transcriber audio.wav --segment-ms 25 --threshold 0.85
```

### Python API

```python
from src import SpeechTranscriber

transcriber = SpeechTranscriber(
    audio_path="audio.wav",
    segment_ms=25.0,
    similarity_threshold=0.85,
)

transcriber.transcribe()
```

## Workflow

### Step 1: Initial Run

```bash
python -m src.transcriber lecture.wav
```

Generates:
- `clusters.json`
- `manual_labels.csv`

### Step 2: Manual Labeling

Edit `manual_labels.csv`:

```csv
cluster_id,character,count
0,ا,12500
1,ل,9800
2,م,7200
```

### Step 3: Generate Text

```bash
python -m src.transcriber lecture.wav --labels manual_labels.csv
```

## Output Files

- `output_text.txt` - Plain text
- `output_text_details.csv` - Detailed timing
- `output_subtitles.srt` - Subtitles

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--segment-ms` | 25.0 | Segment length in ms |
| `--hop-ms` | 12.5 | Hop length in ms |
| `--threshold` | 0.85 | Similarity threshold |

## Tips

- Lower threshold → More clusters
- Higher threshold → Fewer, tighter clusters
- Shorter segments → Better for fast speech
- Longer segments → Better for slow speech