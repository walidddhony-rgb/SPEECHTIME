"""
Tests for AudioProcessor.
"""

import unittest

import numpy as np

from src.audio_processor import AudioProcessor


class TestAudioProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = AudioProcessor()
    
    def test_extract_segments(self):
        """Test segment extraction."""
        # Create test audio
        sample_rate = 16000
        audio = np.random.randn(sample_rate)  # 1 second
        
        # Extract segments
        segments = self.processor.extract_segments(
            audio,
            sample_rate,
            segment_ms=25.0,
            hop_ms=12.5,
        )
        
        # Check results
        self.assertGreater(len(segments), 0)
        self.assertEqual(
            len(segments[0]["data"]),
            400,  # 25ms at 16kHz
        )


if __name__ == "__main__":
    unittest.main()