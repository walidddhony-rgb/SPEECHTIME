"""
Main window for SpeechScribe GUI - Complete Version with Settings.
"""

import sys
import os
import json
import csv
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QProgressBar,
    QMessageBox, QSplitter, QFrame, QScrollArea, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QGroupBox, QLineEdit, QFormLayout, QDoubleSpinBox,
    QSpinBox, QComboBox, QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette


class TranscriptionWorker(QThread):
    """Worker thread for transcription."""
    
    progress = pyqtSignal(int, str)  # percentage, message
    finished = pyqtSignal(object)  # result
    error = pyqtSignal(str)  # error message
    
    def __init__(self, audio_path, segment_ms=25.0, hop_ms=12.5, threshold=0.85):
        super().__init__()
        self.audio_path = audio_path
        self.segment_ms = segment_ms
        self.hop_ms = hop_ms
        self.threshold = threshold
    
    def run(self):
        """Run transcription."""
        try:
            from src.transcriber import SpeechTranscriber
            
            self.progress.emit(10, "Loading audio...")
            
            transcriber = SpeechTranscriber(
                audio_path=self.audio_path,
                segment_ms=self.segment_ms,
                hop_ms=self.hop_ms,
                similarity_threshold=self.threshold,
            )
            
            self.progress.emit(20, "Extracting segments...")
            transcriber.load_audio()
            
            self.progress.emit(40, "Clustering segments...")
            transcriber.extract_segments()
            transcriber.cluster_segments()
            
            self.progress.emit(80, "Saving clusters...")
            transcriber.save_clusters_for_review("gui_clusters.json")
            transcriber.create_labels_template("gui_labels.csv")
            
            self.progress.emit(100, "Done!")
            
            self.finished.emit({
                'transcriber': transcriber,
                'clusters_file': 'gui_clusters.json',
                'labels_file': 'gui_labels.csv',
            })
            
        except Exception as e:
            self.error.emit(str(e))


class SpeechScribeMainWindow(QMainWindow):
    """Main window for SpeechScribe application."""
    
    def __init__(self):
        super().__init__()
        self.audio_path = None
        self.clusters = []
        self.labels = {}
        self.transcriber = None
        
        # Default settings
        self.segment_ms = 25.0
        self.hop_ms = 12.5
        self.threshold = 0.85
        
        # Playback duration setting
        self.playback_duration = 1.0  # seconds
        
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("🎙️ SpeechScribe - Semi-Automatic Transcription")
        self.setMinimumSize(1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        central_widget.setLayout(main_layout)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Settings section
        settings_section = self.create_settings_section()
        main_layout.addWidget(settings_section)
        
        # File selection
        file_section = self.create_file_section()
        main_layout.addWidget(file_section)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 15px;
                text-align: center;
                font-size: 16px;
                font-weight: bold;
                background-color: #f5f5f5;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 13px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)
        
        # Left panel - Audio player and clusters
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Results and controls
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([600, 600])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.statusBar().showMessage("Ready - Configure settings and select an audio file to begin")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #f5f5f5;
                border-top: 2px solid #ddd;
                color: #666;
                font-size: 14px;
                padding: 5px;
            }
        """)
    
    def create_header(self):
        """Create header widget."""
        header = QFrame()
        header.setFrameStyle(QFrame.StyledPanel)
        header.setFixedHeight(300)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                padding: 15px;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        title = QLabel("🎙️ SpeechScribe")
        title.setFont(QFont("Arial", 15, QFont.Bold))
        title.setStyleSheet("color: white;")
        
        subtitle = QLabel("Semi-Automatic Speech Transcription System")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setStyleSheet("color: white; opacity: 0.95;")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        header.setLayout(layout)
        
        return header
    
    def create_settings_section(self):
        """Create settings section with segment, hop, and threshold controls."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                padding: 20px;
                border-radius: 10px;
                border: 2px solid #2196F3;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Section title
        title_label = QLabel("⚙️ Processing Settings")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #1976D2;")
        layout.addWidget(title_label)
        
        # Settings grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        # Segment Length
        seg_label = QLabel("📏 Segment Length (ms):")
        seg_label.setFont(QFont("Arial", 15, QFont.Bold))
        seg_label.setStyleSheet("color: #333;")
        
        self.segment_spinbox = QDoubleSpinBox()
        self.segment_spinbox.setFont(QFont("Arial", 15, QFont.Bold))
        self.segment_spinbox.setRange(10.0, 1000.0)  # Extended to 1 second
        self.segment_spinbox.setValue(25.0)
        self.segment_spinbox.setSingleStep(5.0)
        self.segment_spinbox.setSuffix(" ms")
        self.segment_spinbox.setMinimumHeight(45)
        self.segment_spinbox.setStyleSheet("""
            QDoubleSpinBox {
                padding: 10px;
                border: 2px solid #2196F3;
                border-radius: 6px;
                background-color: white;
                font-weight: bold;
            }
            QDoubleSpinBox::focus {
                border: 2px solid #1976D2;
            }
        """)
        self.segment_spinbox.valueChanged.connect(self.on_segment_changed)
        
        seg_desc = QLabel("Duration of each audio segment (10ms - 1000ms)")
        seg_desc.setFont(QFont("Arial", 12))
        seg_desc.setStyleSheet("color: #666; font-style: italic;")
        
        grid_layout.addWidget(seg_label, 0, 0)
        grid_layout.addWidget(self.segment_spinbox, 0, 1)
        grid_layout.addWidget(seg_desc, 0, 2)
        
        # Hop Length
        hop_label = QLabel("🦘 Hop Length (ms):")
        hop_label.setFont(QFont("Arial", 15, QFont.Bold))
        hop_label.setStyleSheet("color: #333;")
        
        self.hop_spinbox = QDoubleSpinBox()
        self.hop_spinbox.setFont(QFont("Arial", 13, QFont.Bold))
        self.hop_spinbox.setRange(5.0, 1000.0)  # Extended to 1 second
        self.hop_spinbox.setValue(12.5)
        self.hop_spinbox.setSingleStep(2.5)
        self.hop_spinbox.setSuffix(" ms")
        self.hop_spinbox.setMinimumHeight(45)
        self.hop_spinbox.setStyleSheet("""
            QDoubleSpinBox {
                padding: 10px;
                border: 2px solid #FF9800;
                border-radius: 6px;
                background-color: white;
                font-weight: bold;
            }
            QDoubleSpinBox::focus {
                border: 2px solid #F57C00;
            }
        """)
        self.hop_spinbox.valueChanged.connect(self.on_hop_changed)
        
        hop_desc = QLabel("Step between segments (5ms - 1000ms)")
        hop_desc.setFont(QFont("Arial", 12))
        hop_desc.setStyleSheet("color: #666; font-style: italic;")
        
        grid_layout.addWidget(hop_label, 1, 0)
        grid_layout.addWidget(self.hop_spinbox, 1, 1)
        grid_layout.addWidget(hop_desc, 1, 2)
        
        # Similarity Threshold
        thresh_label = QLabel("🎯 Similarity Threshold:")
        thresh_label.setFont(QFont("Arial", 13, QFont.Bold))
        thresh_label.setStyleSheet("color: #333;")
        
        self.threshold_spinbox = QDoubleSpinBox()
        self.threshold_spinbox.setFont(QFont("Arial", 13, QFont.Bold))
        self.threshold_spinbox.setRange(0.50, 0.99)
        self.threshold_spinbox.setValue(0.85)
        self.threshold_spinbox.setSingleStep(0.05)
        self.threshold_spinbox.setDecimals(2)
        self.threshold_spinbox.setMinimumHeight(45)
        self.threshold_spinbox.setStyleSheet("""
            QDoubleSpinBox {
                padding: 10px;
                border: 2px solid #4CAF50;
                border-radius: 6px;
                background-color: white;
                font-weight: bold;
            }
            QDoubleSpinBox::focus {
                border: 2px solid #45a049;
            }
        """)
        self.threshold_spinbox.valueChanged.connect(self.on_threshold_changed)
        
        thresh_desc = QLabel("Clustering sensitivity (0.50 - 0.99)")
        thresh_desc.setFont(QFont("Arial", 12))
        thresh_desc.setStyleSheet("color: #666; font-style: italic;")
        
        grid_layout.addWidget(thresh_label, 2, 0)
        grid_layout.addWidget(self.threshold_spinbox, 2, 1)
        grid_layout.addWidget(thresh_desc, 2, 2)
        
        # Preset buttons
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(10)
        
        preset_label = QLabel("📋 Quick Presets:")
        preset_label.setFont(QFont("Arial", 14, QFont.Bold))
        preset_label.setStyleSheet("color: #333;")
        
        # Fast preset
        fast_btn = QPushButton("⚡ Fast (50ms/25ms)")
        fast_btn.setFont(QFont("Arial", 13, QFont.Bold))
        fast_btn.setMinimumHeight(30)
        fast_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        fast_btn.clicked.connect(lambda: self.apply_preset(50.0, 25.0, 0.85))
        
        # Balanced preset
        balanced_btn = QPushButton("⚖️ Balanced (25ms/12.5ms)")
        balanced_btn.setFont(QFont("Arial", 13, QFont.Bold))
        balanced_btn.setMinimumHeight(30)
        balanced_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        balanced_btn.clicked.connect(lambda: self.apply_preset(25.0, 12.5, 0.85))
        
        # Fine preset
        fine_btn = QPushButton("🔬 Fine (15ms/7.5ms)")
        fine_btn.setFont(QFont("Arial", 13, QFont.Bold))
        fine_btn.setMinimumHeight(30)
        fine_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        fine_btn.clicked.connect(lambda: self.apply_preset(15.0, 7.5, 0.85))
        
        # High threshold preset
        high_thresh_btn = QPushButton("🎯 High Threshold (0.95)")
        high_thresh_btn.setFont(QFont("Arial", 13, QFont.Bold))
        high_thresh_btn.setMinimumHeight(30)
        high_thresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        high_thresh_btn.clicked.connect(lambda: self.apply_preset(None, None, 0.95))
        
        # Low threshold preset
        low_thresh_btn = QPushButton("🎯 Low Threshold (0.75)")
        low_thresh_btn.setFont(QFont("Arial", 13, QFont.Bold))
        low_thresh_btn.setMinimumHeight(30)
        low_thresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        low_thresh_btn.clicked.connect(lambda: self.apply_preset(None, None, 0.75))
        
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(fast_btn)
        preset_layout.addWidget(balanced_btn)
        preset_layout.addWidget(fine_btn)
        preset_layout.addWidget(high_thresh_btn)
        preset_layout.addWidget(low_thresh_btn)
        preset_layout.addStretch()
        
        # Current settings display
        self.settings_display = QLabel(
            f"Current: Segment={self.segment_ms}ms | Hop={self.hop_ms}ms | Threshold={self.threshold}"
        )
        self.settings_display.setFont(QFont("Arial", 14, QFont.Bold))
        self.settings_display.setStyleSheet("color: #1976D2; padding: 10px; background-color: white; border-radius: 6px;")
        
        grid_layout.addLayout(preset_layout, 3, 0, 1, 3)
        grid_layout.addWidget(self.settings_display, 4, 0, 1, 3)
        
        layout.addLayout(grid_layout)
        frame.setLayout(layout)
        
        return frame
    
    def create_file_section(self):
        """Create file selection section."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border: 2px solid #e0e0e0;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # File label
        self.file_label = QLabel("📁 No audio file selected")
        self.file_label.setFont(QFont("Arial", 13))
        self.file_label.setStyleSheet("color: #666; font-style: italic;")
        self.file_label.setMinimumWidth(500)
        self.file_label.setMinimumHeight(60)
        self.file_label.setAlignment(Qt.AlignCenter)
        
        # Select button
        self.select_btn = QPushButton("📂 Select Audio File")
        self.select_btn.setFont(QFont("Arial", 13, QFont.Bold))
        self.select_btn.setMinimumHeight(60)
        self.select_btn.setMinimumWidth(200)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self.select_btn.clicked.connect(self.select_audio_file)
        
        # Transcribe button
        self.transcribe_btn = QPushButton("🎯 Start Transcription")
        self.transcribe_btn.setFont(QFont("Arial", 13, QFont.Bold))
        self.transcribe_btn.setMinimumHeight(60)
        self.transcribe_btn.setMinimumWidth(220)
        self.transcribe_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.clicked.connect(self.start_transcription)
        
        layout.addWidget(self.file_label)
        layout.addWidget(self.select_btn)
        layout.addWidget(self.transcribe_btn)
        
        frame.setLayout(layout)
        return frame
    
    def create_left_panel(self):
        """Create left panel with audio player and clusters."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Audio player group
        audio_group = QGroupBox("🔊 Audio Player")
        audio_group.setFont(QFont("Arial", 18, QFont.Bold))
        audio_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #2196F3;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #2196F3;
            }
        """)
        
        audio_layout = QVBoxLayout()
        audio_layout.setSpacing(10)
        
        self.audio_info_label = QLabel("Load an audio file to begin")
        self.audio_info_label.setFont(QFont("Arial", 14))
        self.audio_info_label.setStyleSheet("color: #666; padding: 10px;")
        
        # Playback duration control
        duration_layout = QHBoxLayout()
        duration_layout.setSpacing(10)
        
        duration_label = QLabel("⏱️ Play Duration:")
        duration_label.setFont(QFont("Arial", 14, QFont.Bold))
        duration_label.setStyleSheet("color: #333;")
        
        self.duration_spinbox = QDoubleSpinBox()
        self.duration_spinbox.setFont(QFont("Arial", 14, QFont.Bold))
        self.duration_spinbox.setRange(0.1, 5.0)
        self.duration_spinbox.setValue(1.0)
        self.duration_spinbox.setSingleStep(0.1)
        self.duration_spinbox.setSuffix(" sec")
        self.duration_spinbox.setMinimumHeight(40)
        self.duration_spinbox.setMinimumWidth(120)
        self.duration_spinbox.setStyleSheet("""
            QDoubleSpinBox {
                padding: 8px;
                border: 2px solid #2196F3;
                border-radius: 6px;
                background-color: white;
                font-weight: bold;
            }
            QDoubleSpinBox::focus {
                border: 2px solid #1976D2;
            }
        """)
        self.duration_spinbox.valueChanged.connect(self.on_duration_changed)
        
        duration_info = QLabel("(Time to play for each cluster)")
        duration_info.setFont(QFont("Arial", 12))
        duration_info.setStyleSheet("color: #666; font-style: italic;")
        
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_spinbox)
        duration_layout.addWidget(duration_info)
        duration_layout.addStretch()
        
        # Playback controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        self.play_all_btn = QPushButton("▶ Play All")
        self.play_all_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.play_all_btn.setMinimumHeight(45)
        self.play_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.play_all_btn.clicked.connect(self.play_all_audio)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setFont(QFont("Arial", 13, QFont.Bold))
        self.stop_btn.setMinimumHeight(45)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_audio)
        
        controls_layout.addWidget(self.play_all_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch()
        
        audio_layout.addWidget(self.audio_info_label)
        audio_layout.addLayout(duration_layout)
        audio_layout.addLayout(controls_layout)
        audio_group.setLayout(audio_layout)
        
        # Clusters group
        clusters_group = QGroupBox("📊 Sound Clusters")
        clusters_group.setFont(QFont("Arial", 14, QFont.Bold))
        clusters_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #FF9800;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #FF9800;
            }
        """)
        
        clusters_layout = QVBoxLayout()
        clusters_layout.setSpacing(10)
        
        # Cluster info
        self.cluster_info_label = QLabel("No clusters loaded - Start transcription first")
        self.cluster_info_label.setFont(QFont("Arial", 13))
        self.cluster_info_label.setStyleSheet("color: #666; padding: 10px;")
        
        # Cluster table
        self.cluster_table = QTableWidget()
        self.cluster_table.setFont(QFont("Arial", 13))
        self.cluster_table.setColumnCount(5)
        self.cluster_table.setHorizontalHeaderLabels([
            "ID", "Character", "Count", "Frequency", "Actions"
        ])
        self.cluster_table.setMinimumHeight(300)
        
        # Style table
        self.cluster_table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                gridline-color: #ddd;
                background-color: white;
            }
            QTableWidget::item {
                padding: 12px;
                border: 1px solid #eee;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QHeaderView::section {
                background-color: #FF9800;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        self.cluster_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.cluster_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.cluster_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.cluster_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.cluster_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.cluster_table.setColumnWidth(0, 80)
        self.cluster_table.setColumnWidth(1, 100)
        self.cluster_table.setColumnWidth(4, 140)
        
        self.cluster_table.itemClicked.connect(self.on_cluster_item_clicked)
        
        # Save labels button
        self.save_labels_btn = QPushButton("💾 Save Labels")
        self.save_labels_btn.setFont(QFont("Arial", 13, QFont.Bold))
        self.save_labels_btn.setMinimumHeight(45)
        self.save_labels_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.save_labels_btn.setEnabled(False)
        self.save_labels_btn.clicked.connect(self.save_labels)
        
        clusters_layout.addWidget(self.cluster_info_label)
        clusters_layout.addWidget(self.cluster_table)
        clusters_layout.addWidget(self.save_labels_btn)
        clusters_group.setLayout(clusters_layout)
        
        layout.addWidget(audio_group)
        layout.addWidget(clusters_group)
        panel.setLayout(layout)
        
        return panel
    
    def create_right_panel(self):
        """Create right panel with results and controls."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Controls group
        controls_group = QGroupBox("🎛️ Controls")
        controls_group.setFont(QFont("Arial", 18, QFont.Bold))
        controls_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #4CAF50;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #4CAF50;
            }
        """)
        
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        # Generate text button
        self.generate_btn = QPushButton("✨ Generate Text")
        self.generate_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.setMinimumWidth(200)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00ACC1;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self.generate_text)
        
        # Load results button
        self.load_results_btn = QPushButton("📂 Load Results")
        self.load_results_btn.setFont(QFont("Arial", 16, QFont.Bold))
        self.load_results_btn.setMinimumHeight(50)
        self.load_results_btn.setMinimumWidth(180)
        self.load_results_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F4511E;
            }
        """)
        self.load_results_btn.clicked.connect(self.load_results)
        
        controls_layout.addWidget(self.generate_btn)
        controls_layout.addWidget(self.load_results_btn)
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        
        # Results group
        results_group = QGroupBox("📄 Transcription Results")
        results_group.setFont(QFont("Arial", 18, QFont.Bold))
        results_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #00BCD4;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #00BCD4;
            }
        """)
        
        results_layout = QVBoxLayout()
        results_layout.setSpacing(10)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 14))
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 12px 24px;
                border: 2px solid #ddd;
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                font-weight: bold;
                font-size: 14px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #00BCD4;
            }
            QTabBar::tab:hover {
                background-color: #f5f5f5;
            }
        """)
        
        # Text tab
        self.text_tab = QWidget()
        text_layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Arial", 18))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                background-color: #fafafa;
                font-size: 18px;
            }
        """)
        self.text_edit.setReadOnly(True)
        
        text_layout.addWidget(self.text_edit)
        self.text_tab.setLayout(text_layout)
        
        # Details tab
        self.details_tab = QWidget()
        details_layout = QVBoxLayout()
        
        self.details_table = QTableWidget()
        self.details_table.setFont(QFont("Arial", 14))
        self.details_table.setColumnCount(5)
        self.details_table.setHorizontalHeaderLabels([
            "Character", "Start Sample", "End Sample", "Start Time (s)", "End Time (s)"
        ])
        
        self.details_table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                gridline-color: #ddd;
                background-color: white;
            }
            QTableWidget::item {
                padding: 12px;
                border: 1px solid #eee;
            }
            QHeaderView::section {
                background-color: #00BCD4;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        details_layout.addWidget(self.details_table)
        self.details_tab.setLayout(details_layout)
        
        self.tabs.addTab(self.text_tab, "📝 Text Output")
        self.tabs.addTab(self.details_tab, "📊 Detailed View")
        
        # Save results button
        self.save_results_btn = QPushButton("💾 Save Results")
        self.save_results_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.save_results_btn.setMinimumHeight(45)
        self.save_results_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.save_results_btn.setEnabled(False)
        self.save_results_btn.clicked.connect(self.save_results)
        
        results_layout.addWidget(self.tabs)
        results_layout.addWidget(self.save_results_btn)
        results_group.setLayout(results_layout)
        
        layout.addWidget(controls_group)
        layout.addWidget(results_group)
        panel.setLayout(layout)
        
        return panel
    
    def apply_styles(self):
        """Apply application-wide styles."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QToolTip {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                padding: 8px;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
    
    # ========== Settings Handlers ==========
    
    def on_segment_changed(self, value):
        """Handle segment length change."""
        self.segment_ms = value
        self.update_settings_display()
    
    def on_hop_changed(self, value):
        """Handle hop length change."""
        self.hop_ms = value
        self.update_settings_display()
    
    def on_threshold_changed(self, value):
        """Handle threshold change."""
        self.threshold = value
        self.update_settings_display()
    
    def on_duration_changed(self, value):
        """Handle playback duration change."""
        self.playback_duration = value
        self.statusBar().showMessage(f"Playback duration set to {value:.1f} seconds")
    
    def update_settings_display(self):
        """Update settings display label."""
        self.settings_display.setText(
            f"Current: Segment={self.segment_ms}ms | Hop={self.hop_ms}ms | Threshold={self.threshold}"
        )
    
    def apply_preset(self, segment=None, hop=None, threshold=None):
        """Apply preset settings."""
        if segment is not None:
            self.segment_spinbox.setValue(segment)
            self.segment_ms = segment
        
        if hop is not None:
            self.hop_spinbox.setValue(hop)
            self.hop_ms = hop
        
        if threshold is not None:
            self.threshold_spinbox.setValue(threshold)
            self.threshold = threshold
        
        self.update_settings_display()
        
        self.statusBar().showMessage(
            f"Settings applied: Segment={self.segment_ms}ms | "
            f"Hop={self.hop_ms}ms | Threshold={self.threshold}"
        )
    
    # ========== File and Transcription Handlers ==========
    
    def select_audio_file(self):
        """Select audio file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "WAV Files (*.wav);;All Files (*)"
        )
        
        if file_path:
            self.audio_path = file_path
            filename = Path(file_path).name
            
            self.file_label.setText(f"✓ {filename}")
            self.file_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.transcribe_btn.setEnabled(True)
            
            # Get audio info
            try:
                from scipy.io import wavfile
                sample_rate, audio = wavfile.read(file_path)
                duration = len(audio) / sample_rate
                self.audio_info_label.setText(
                    f"✓ Loaded: {filename}\n"
                    f"Duration: {duration:.2f}s | Sample Rate: {sample_rate}Hz"
                )
                self.audio_info_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            except:
                self.audio_info_label.setText(f"✓ Loaded: {filename}")
            
            self.statusBar().showMessage(f"Selected: {file_path}")
    
    def start_transcription(self):
        """Start transcription process."""
        if not self.audio_path:
            QMessageBox.warning(
                self,
                "Warning",
                "Please select an audio file first!",
            )
            return
        
        # Confirm settings
        reply = QMessageBox.question(
            self,
            "Confirm Settings",
            f"Start transcription with these settings?\n\n"
            f"📏 Segment: {self.segment_ms} ms\n"
            f"🦘 Hop: {self.hop_ms} ms\n"
            f"🎯 Threshold: {self.threshold}\n\n"
            f"File: {Path(self.audio_path).name}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.No:
            return
        
        # Disable buttons
        self.transcribe_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start worker
        self.worker = TranscriptionWorker(
            self.audio_path,
            segment_ms=self.segment_ms,
            hop_ms=self.hop_ms,
            threshold=self.threshold,
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_transcription_finished)
        self.worker.error.connect(self.on_transcription_error)
        self.worker.start()
    
    def on_progress(self, percentage, message):
        """Handle progress update."""
        self.progress_bar.setValue(percentage)
        self.statusBar().showMessage(message)
    
    def on_transcription_finished(self, result):
        """Handle transcription finished."""
        self.transcriber = result['transcriber']
        
        # Load clusters
        with open(result['clusters_file'], 'r', encoding='utf-8-sig') as f:
            self.clusters = json.load(f)
        
        # Update cluster table
        self.populate_cluster_table()
        
        # Update info
        self.cluster_info_label.setText(
            f"✓ Created {len(self.clusters)} clusters - "
            f"Listen to each and assign characters"
        )
        self.cluster_info_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        # Enable buttons
        self.transcribe_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.save_labels_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.statusBar().showMessage(
            f"Transcription completed with Segment={self.segment_ms}ms, "
            f"Hop={self.hop_ms}ms, Threshold={self.threshold}"
        )
        
        QMessageBox.information(
            self,
            "Transcription Complete",
            f"✓ Created {len(self.clusters)} clusters\n\n"
            f"Settings used:\n"
            f"📏 Segment: {self.segment_ms} ms\n"
            f"🦘 Hop: {self.hop_ms} ms\n"
            f"🎯 Threshold: {self.threshold}\n\n"
            "Please listen to each cluster and assign characters.\n"
            "Then click 'Generate Text' to create the transcription.",
        )
    
    def on_transcription_error(self, error_msg):
        """Handle transcription error."""
        self.transcribe_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Error", f"Transcription failed:\n{error_msg}")
        self.statusBar().showMessage("Error occurred")
    
    def populate_cluster_table(self):
        """Populate cluster table."""
        if not self.clusters:
            return
        
        self.cluster_table.setRowCount(len(self.clusters))
        
        total_count = sum(c['count'] for c in self.clusters)
        
        for row, cluster in enumerate(self.clusters):
            # ID
            id_item = QTableWidgetItem(str(cluster['id']))
            id_item.setTextAlignment(Qt.AlignCenter)
            id_item.setFont(QFont("Arial", 14, QFont.Bold))
            self.cluster_table.setItem(row, 0, id_item)
            
            # Character (editable)
            char_item = QTableWidgetItem(cluster.get('character', ''))
            char_item.setTextAlignment(Qt.AlignCenter)
            char_item.setFont(QFont("Arial", 16, QFont.Bold))
            self.cluster_table.setItem(row, 1, char_item)
            
            # Count
            count_item = QTableWidgetItem(str(cluster['count']))
            count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            count_item.setFont(QFont("Arial", 14))
            self.cluster_table.setItem(row, 2, count_item)
            
            # Frequency (progress bar)
            frequency = cluster['count'] / total_count * 100
            progress = QProgressBar()
            progress.setValue(int(frequency))
            progress.setFormat(f"{frequency:.1f}%")
            progress.setMinimumHeight(35)
            progress.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #ddd;
                    border-radius: 15px;
                    text-align: center;
                    font-weight: bold;
                    font-size: 14px;
                    background-color: #f5f5f5;
                }
                QProgressBar::chunk {
                    background-color: #2196F3;
                    border-radius: 13px;
                }
            """)
            self.cluster_table.setCellWidget(row, 3, progress)
            
            # Actions - Play button
            play_btn = QPushButton("▶ Play")
            play_btn.setFont(QFont("Arial", 13, QFont.Bold))
            play_btn.setMinimumHeight(40)
            play_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            play_btn.setToolTip(f"Play {self.playback_duration:.1f}s from cluster start")
            play_btn.clicked.connect(
                lambda checked, cid=cluster['id']: self.play_cluster(cid)
            )
            self.cluster_table.setCellWidget(row, 4, play_btn)
    
    def on_cluster_item_clicked(self, item):
        """Handle cluster item click."""
        row = item.row()
        if row < len(self.clusters):
            cluster_id = self.clusters[row]['id']
            self.statusBar().showMessage(f"Selected cluster {cluster_id}")
    
    def play_cluster(self, cluster_id):
        """Play cluster audio segment with configurable duration."""
        try:
            import sounddevice as sd
            from scipy.io import wavfile
            import numpy as np
            
            if self.audio_path is None:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "No audio file loaded!\n\nPlease select an audio file first.",
                )
                return
            
            # Find cluster
            cluster = None
            for c in self.clusters:
                if c['id'] == cluster_id:
                    cluster = c
                    break
            
            if cluster is None:
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"Cluster {cluster_id} not found!",
                )
                return
            
            if not cluster['segments']:
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"Cluster {cluster_id} has no segments!",
                )
                return
            
            # Get first segment
            segment = cluster['segments'][0]
            start_seconds = segment['start_seconds']
            end_seconds = segment['end_seconds']
            
            # Calculate segment duration
            segment_duration = end_seconds - start_seconds
            
            # Use configured playback duration
            play_duration = min(self.playback_duration, segment_duration)
            
            # Load audio
            sample_rate, audio = wavfile.read(self.audio_path)
            
            # Convert to float
            if audio.dtype == np.int16:
                audio = audio.astype(np.float64) / 32767.0
            elif audio.dtype == np.int32:
                audio = audio.astype(np.float64) / 2147483647.0
            elif audio.dtype == np.uint8:
                audio = audio.astype(np.float64) / 127.0 - 1.0
            
            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
            
            # Calculate samples
            start_sample = int(start_seconds * sample_rate)
            play_samples = int(play_duration * sample_rate)
            end_sample = start_sample + play_samples
            
            # Ensure we don't go beyond audio length
            end_sample = min(end_sample, len(audio))
            
            # Extract segment
            segment_audio = audio[start_sample:end_sample]
            
            if len(segment_audio) == 0:
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"Cannot extract audio for cluster {cluster_id}",
                )
                return
            
            # Normalize audio
            max_val = np.max(np.abs(segment_audio))
            if max_val > 0:
                segment_audio = segment_audio / max_val * 0.9
            
            # Play using sounddevice
            try:
                sd.play(segment_audio, sample_rate)
                sd.wait()
                
                self.statusBar().showMessage(
                    f"✓ Playing cluster {cluster_id} | "
                    f"Start: {start_seconds:.3f}s | "
                    f"Duration: {play_duration:.3f}s"
                )
                
            except Exception as e:
                # Fallback: show info dialog
                QMessageBox.information(
                    self,
                    "Audio Playback Info",
                    f"Cluster {cluster_id}\n\n"
                    f"📍 Start Time: {start_seconds:.3f}s\n"
                    f"📍 End Time: {end_seconds:.3f}s\n"
                    f"⏱️ Segment Duration: {segment_duration:.3f}s\n"
                    f"▶️ Playing: {play_duration:.3f}s\n\n"
                    f"💡 To enable audio playback, install sounddevice:\n"
                    f"   pip install sounddevice\n\n"
                    f"Or use an external audio player (VLC, etc.)\n"
                    f"and navigate to {start_seconds:.3f} seconds.",
                )
                
        except ImportError as e:
            QMessageBox.information(
                self,
                "Missing Dependency",
                f"🔊 sounddevice is not installed.\n\n"
                f"Install it with:\n"
                f"   pip install sounddevice\n\n"
                f"Error: {str(e)}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Cannot play cluster {cluster_id}:\n\n{str(e)}",
            )
    
    def play_all_audio(self):
        """Play all audio."""
        try:
            import sounddevice as sd
            from scipy.io import wavfile
            import numpy as np
            
            if self.audio_path is None:
                return
            
            sample_rate, audio = wavfile.read(self.audio_path)
            if audio.dtype == np.int16:
                audio = audio.astype(np.float64) / 32767.0
            
            sd.play(audio, sample_rate)
            self.statusBar().showMessage("Playing full audio...")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot play audio: {str(e)}")
    
    def stop_audio(self):
        """Stop audio playback."""
        try:
            import sounddevice as sd
            sd.stop()
            self.statusBar().showMessage("Playback stopped")
        except:
            pass
    
    def save_labels(self):
        """Save labels to CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Labels",
            "manual_labels.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                import csv
                
                # Get labels from table
                labels = {}
                for row in range(self.cluster_table.rowCount()):
                    cluster_id = int(self.cluster_table.item(row, 0).text())
                    character = self.cluster_table.item(row, 1).text().strip()
                    if character:
                        labels[cluster_id] = character
                
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'cluster_id', 'character', 'count',
                        'first_occurrence_seconds', 'notes'
                    ])
                    
                    for cluster in self.clusters:
                        cluster_id = cluster['id']
                        character = labels.get(cluster_id, '')
                        count = cluster['count']
                        first_occ = (
                            cluster['segments'][0]['start_seconds']
                            if cluster['segments'] else 0
                        )
                        
                        writer.writerow([
                            cluster_id, character, count,
                            f"{first_occ:.2f}", ''
                        ])
                
                self.statusBar().showMessage(f"Labels saved to {file_path}")
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"✓ Labels saved to:\n{file_path}",
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save labels:\n{str(e)}",
                )
    
    def generate_text(self):
        """Generate text from labels."""
        if not self.transcriber:
            QMessageBox.warning(
                self,
                "Warning",
                "Please transcribe audio first!",
            )
            return
        
        # Get labels from table
        labels = {}
        for row in range(self.cluster_table.rowCount()):
            cluster_id = int(self.cluster_table.item(row, 0).text())
            character = self.cluster_table.item(row, 1).text().strip()
            if character:
                labels[cluster_id] = character
        
        if not labels:
            QMessageBox.warning(
                self,
                "Warning",
                "Please label at least one cluster!",
            )
            return
        
        try:
            # Generate text
            self.transcriber.labels = labels
            self.transcriber.generate_text()
            self.transcriber.save_text(
                output_txt="gui_output.txt",
                output_csv="gui_output.csv",
                output_srt="gui_output.srt",
            )
            
            # Display results
            with open("gui_output.txt", 'r', encoding='utf-8-sig') as f:
                text = f.read()
            
            self.text_edit.setText(text)
            self.set_details_table(self.transcriber.text_result)
            
            self.statusBar().showMessage("Text generated successfully!")
            self.save_results_btn.setEnabled(True)
            
            QMessageBox.information(
                self,
                "Success",
                f"✓ Generated {len(self.transcriber.text_result)} text segments\n\n"
                "Results saved to:\n"
                "- gui_output.txt\n"
                "- gui_output.csv\n"
                "- gui_output.srt",
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate text:\n{str(e)}",
            )
    
    def set_details_table(self, details):
        """Set details table content."""
        if not details:
            return
        
        self.details_table.setRowCount(len(details))
        
        for row, item in enumerate(details):
            self.details_table.setItem(
                row, 0,
                QTableWidgetItem(item.get('character', ''))
            )
            self.details_table.setItem(
                row, 1,
                QTableWidgetItem(str(item.get('start', 0)))
            )
            self.details_table.setItem(
                row, 2,
                QTableWidgetItem(str(item.get('end', 0)))
            )
            self.details_table.setItem(
                row, 3,
                QTableWidgetItem(f"{item.get('start_seconds', 0):.3f}")
            )
            self.details_table.setItem(
                row, 4,
                QTableWidgetItem(f"{item.get('end_seconds', 0):.3f}")
            )
    
    def load_results(self):
        """Load results from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Results",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    text = f.read()
                
                self.text_edit.setText(text)
                self.save_results_btn.setEnabled(True)
                
                self.statusBar().showMessage(f"Loaded: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load file:\n{str(e)}",
                )
    
    def save_results(self):
        """Save results to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            "output_text.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                text = self.text_edit.toPlainText()
                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    f.write(text)
                
                self.statusBar().showMessage(f"Saved to: {file_path}")
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"✓ Results saved to:\n{file_path}",
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save file:\n{str(e)}",
                )


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("SpeechScribe")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SpeechScribe Team")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    # Create and show main window
    window = SpeechScribeMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()