"""
Audio processing utilities.
"""

import numpy as np
from scipy.io import wavfile


class AudioProcessor:
    """Handle audio file operations."""
    
    def __init__(self):
        pass
    
    def load(self, path):
        """
        Load audio file and convert to mono.
        
        Returns:
            tuple: (sample_rate, audio_data)
        """
        sample_rate, audio = wavfile.read(path)
        
        # Convert to mono if stereo
        if audio.ndim == 2:
            audio = audio.mean(axis=1)
        
        # Convert to float64
        audio = audio.astype(np.float64)
        
        # Remove DC offset
        audio -= np.mean(audio)
        
        # Normalize amplitude
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio /= max_val
        
        return sample_rate, audio
    
    def extract_segments(self, audio, sample_rate, segment_ms=25.0, hop_ms=12.5):
        """
        Extract overlapping segments from audio.
        
        Args:
            audio: Audio data array
            sample_rate: Sample rate in Hz
            segment_ms: Segment length in milliseconds
            hop_ms: Hop length in milliseconds
            
        Returns:
            list: List of segment dictionaries
        """
        segment_length = int(round(sample_rate * segment_ms / 1000.0))
        hop_length = int(round(sample_rate * hop_ms / 1000.0))
        
        segments = []
        
        for start in range(0, len(audio) - segment_length + 1, hop_length):
            end = start + segment_length
            segment = audio[start:end]
            
            segments.append({
                'index': len(segments),
                'start': start,
                'end': end - 1,
                'data': segment,
                'start_seconds': start / sample_rate,
                'end_seconds': (end - 1) / sample_rate,
                'labeled': False,
                'cluster_id': -1,
            })
        
        return segments