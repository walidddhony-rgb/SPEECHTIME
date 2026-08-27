"""
Result viewer widget for SpeechScribe GUI.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ResultViewerWidget(QWidget):
    """Widget to display transcription results."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("📄 Transcription Results")
        header_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2196F3;
            padding: 10px;
        """)
        layout.addWidget(header_label)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
            }
            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
            }
        """)
        
        # Text tab
        self.text_tab = QWidget()
        text_layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Arial",10+ 12))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                background-color: #fafafa;
            }
        """)
        self.text_edit.setReadOnly(True)
        
        text_layout.addWidget(self.text_edit)
        self.text_tab.setLayout(text_layout)
        
        # Details tab
        self.details_tab = QWidget()
        details_layout = QVBoxLayout()
        
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(5)
        self.details_table.setHorizontalHeaderLabels([
            "Character", "Start Sample", "End Sample", "Start Time", "End Time"
        ])
        
        self.details_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                gridline-color: #ddd;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #333;
            }
        """)
        
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        details_layout.addWidget(self.details_table)
        self.details_tab.setLayout(details_layout)
        
        self.tabs.addTab(self.text_tab, "📝 Text")
        self.tabs.addTab(self.details_tab, "📊 Details")
        
        layout.addWidget(self.tabs)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("📂 Load Results")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.load_btn.clicked.connect(self.load_results)
        
        self.save_btn = QPushButton("💾 Save Text")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
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
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_text)
        
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_results(self):
        """Load results from text file."""
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
                self.save_btn.setEnabled(True)
            except Exception as e:
                self.text_edit.setText(f"Error loading file: {str(e)}")
    
    def save_text(self):
        """Save text to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Text",
            "output_text.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                text = self.text_edit.toPlainText()
                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    f.write(text)
            except Exception as e:
                print(f"Error saving file: {str(e)}")
    
    def set_text(self, text):
        """Set text content."""
        self.text_edit.setText(text)
        self.save_btn.setEnabled(True)
    
    def set_details(self, details):
        """Set details table."""
        self.details_table.setRowCount(len(details))
        
        for row, item in enumerate(details):
            self.details_table.setItem(row, 0, QTableWidgetItem(item.get('character', '')))
            self.details_table.setItem(row, 1, QTableWidgetItem(str(item.get('start', 0))))
            self.details_table.setItem(row, 2, QTableWidgetItem(str(item.get('end', 0))))
            self.details_table.setItem(row, 3, QTableWidgetItem(f"{item.get('start_seconds', 0):.3f}"))
            self.details_table.setItem(row, 4, QTableWidgetItem(f"{item.get('end_seconds', 0):.3f}"))