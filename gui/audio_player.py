"""
Audio player widget for SpeechScribe GUI.
"""

import numpy as np
from scipy.io import wavfile
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider
from PyQt5.QtCore import Qt

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False


class AudioPlayer(QObject):
    """Audio playback handler."""
    
    playback_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.audio_data = None
        self.sample_rate = None
        self.is_playing = False
    
    def load_audio(self, file_path):
        """Load audio file."""
        try:
            self.sample_rate, self.audio_data = wavfile.read(file_path)
            
            # Convert to float
            if self.audio_data.dtype == np.int16:
                self.audio_data = self.audio_data.astype(np.float64) / 32767.0
            elif self.audio_data.dtype == np.int32:
                self.audio_data = self.audio_data.astype(np.float64) / 2147483647.0
            
            # Convert to mono
            if len(self.audio_data.shape) > 1:
                self.audio_data = self.audio_data.mean(axis=1)
            
            return True
        except Exception as e:
            self.error_occurred.emit(f"Error loading audio: {str(e)}")
            return False
    
    def play_segment(self, start_sample, end_sample):
        """Play audio segment."""
        if not SOUNDDEVICE_AVAILABLE:
            self.error_occurred.emit("sounddevice not installed. Install with: pip install sounddevice")
            return
        
        if self.audio_data is None:
            self.error_occurred.emit("No audio loaded")
            return
        
        try:
            segment = self.audio_data[start_sample:end_sample]
            self.is_playing = True
            sd.play(segment, self.sample_rate)
            sd.wait()
            self.is_playing = False
            self.playback_finished.emit()
        except Exception as e:
            self.error_occurred.emit(f"Playback error: {str(e)}")
            self.is_playing = False
    
    def stop(self):
        """Stop playback."""
        if SOUNDDEVICE_AVAILABLE and self.is_playing:
            sd.stop()
            self.is_playing = False
    
    def get_duration(self):
        """Get audio duration in seconds."""
        if self.audio_data is None:
            return 0.0
        return len(self.audio_data) / self.sample_rate


class AudioPlayerWidget(QWidget):
    """Audio player widget with controls."""
    
    def __init__(self):
        super().__init__()
        self.player = AudioPlayer()
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Player controls
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setFixedWidth(80)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setFixedWidth(80)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        self.status_label = QLabel("No audio loaded")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.status_label)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connect signals."""
        self.play_btn.clicked.connect(self.on_play)
        self.stop_btn.clicked.connect(self.on_stop)
        self.player.playback_finished.connect(self.on_playback_finished)
        self.player.error_occurred.connect(self.on_error)
    
    def load_audio(self, file_path):
        """Load audio file."""
        if self.player.load_audio(file_path):
            duration = self.player.get_duration()
            self.status_label.setText(f"✓ Loaded: {duration:.2f}s")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.play_btn.setEnabled(True)
            return True
        return False
    
    def play_segment(self, start_sample, end_sample):
        """Play audio segment."""
        self.play_btn.setEnabled(False)
        self.status_label.setText("▶ Playing...")
        self.player.play_segment(start_sample, end_sample)
    
    def on_play(self):
        """Handle play button click."""
        if self.player.audio_data is not None:
            self.play_segment(0, len(self.player.audio_data))
    
    def on_stop(self):
        """Handle stop button click."""
        self.player.stop()
        self.status_label.setText("⏹ Stopped")
        self.play_btn.setEnabled(True)
    
    def on_playback_finished(self):
        """Handle playback finished."""
        self.status_label.setText("✓ Playback finished")
        self.play_btn.setEnabled(True)
    
    def on_error(self, error_msg):
        """Handle error."""
        self.status_label.setText(f"✗ Error: {error_msg}")
        self.status_label.setStyleSheet("color: #f44336;")
        self.play_btn.setEnabled(True)