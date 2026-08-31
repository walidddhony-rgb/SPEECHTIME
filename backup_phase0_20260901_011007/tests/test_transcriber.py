"""
Tests for SpeechTranscriber.
"""

import unittest
from pathlib import Path

import numpy as np
from scipy.io import wavfile

from src.transcriber import SpeechTranscriber


class TestSpeechTranscriber(unittest.TestCase):
    
    def setUp(self):
        """Create test audio file."""
        # Generate simple test audio
        sample_rate = 16000
        duration = 1.0  # 1 second
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        
        # Save test file
        self.test_audio_path = "test_audio.wav"
        wavfile.write(
            self.test_audio_path,
            sample_rate,
            (audio * 32767).astype(np.int16),
        )
    
    def tearDown(self):
        """Clean up test files."""
        test_file = Path(self.test_audio_path)
        if test_file.exists():
            test_file.unlink()
    
    def test_transcriber_creation(self):
        """Test transcriber initialization."""
        transcriber = SpeechTranscriber(
            audio_path=self.test_audio_path,
        )
        
        self.assertIsNotNone(transcriber)
        self.assertEqual(
            transcriber.audio_path,
            Path(self.test_audio_path),
        )
    
    def test_load_audio(self):
        """Test audio loading."""
        transcriber = SpeechTranscriber(
            audio_path=self.test_audio_path,
        )
        
        transcriber.load_audio()
        
        self.assertIsNotNone(transcriber.audio)
        self.assertIsNotNone(transcriber.sample_rate)
        self.assertEqual(transcriber.sample_rate, 16000)


if __name__ == "__main__":
    unittest.main()