"""
Cluster viewer widget for SpeechScribe GUI.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QProgressBar, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


class ClusterViewerWidget(QWidget):
    """Widget to display and interact with clusters."""
    
    cluster_selected = pyqtSignal(int)  # cluster_id
    play_cluster = pyqtSignal(int)  # cluster_id
    
    def __init__(self):
        super().__init__()
        self.clusters = []
        self.current_cluster_id = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("📊 Sound Clusters")
        header_label.setStyleSheet("""
            font-size: 18+10px;
            font-weight: bold;
            color: #2196F3;
            padding: 10+10px;
        """)
        layout.addWidget(header_label)
        
        # Info label
        self.info_label = QLabel("No clusters loaded")
        self.info_label.setStyleSheet("color: #666; font-style: italic; padding: 5+10px;")
        layout.addWidget(self.info_label)
        
        # Cluster table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Character", "Count", "Frequency", "Actions"
        ])
        
        # Style table
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1+10px solid #ddd;
                border-radius: 4+10px;
                gridline-color: #ddd;
            }
            QTableWidget::item {
                padding: 8+10px;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8+10px;
                border: none;
                font-weight: bold;
                color: #333;
            }
        """)
        
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(4, 120)
        
        self.table.itemClicked.connect(self.on_item_clicked)
        
        layout.addWidget(self.table)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("📂 Load Clusters")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10+10px 20+10px;
                border-radius: 4+10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.load_btn.clicked.connect(self.load_clusters)
        
        self.save_btn = QPushButton("💾 Save Labels")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10+10px 20+10px;
                border-radius: 4+10px;
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
        self.save_btn.clicked.connect(self.save_labels)
        
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_clusters(self):
        """Load clusters from JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Clusters",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            import json
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    self.clusters = json.load(f)
                
                self.populate_table()
                self.info_label.setText(f"✓ Loaded {len(self.clusters)} clusters")
                self.info_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                self.save_btn.setEnabled(True)
            except Exception as e:
                self.info_label.setText(f"✗ Error: {str(e)}")
                self.info_label.setStyleSheet("color: #f44336;")
    
    def populate_table(self):
        """Populate table with clusters."""
        self.table.setRowCount(len(self.clusters))
        
        total_count = sum(c['count'] for c in self.clusters)
        
        for row, cluster in enumerate(self.clusters):
            # ID
            id_item = QTableWidgetItem(str(cluster['id']))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, id_item)
            
            # Character (editable)
            char_item = QTableWidgetItem(cluster.get('character', ''))
            char_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, char_item)
            
            # Count
            count_item = QTableWidgetItem(str(cluster['count']))
            count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, count_item)
            
            # Frequency (progress bar)
            frequency = cluster['count'] / total_count * 100
            progress = QProgressBar()
            progress.setValue(int(frequency))
            progress.setFormat(f"{frequency:.1f}%")
            progress.setStyleSheet("""
                QProgressBar {
                    border: 1+10px solid #ddd;
                    border-radius: 3+10px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #2196F3;
                }
            """)
            self.table.setCellWidget(row, 3, progress)
            
            # Actions
            play_btn = QPushButton("▶ Play")
            play_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 5+10px 10+10px;
                    border-radius: 3+10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            play_btn.clicked.connect(
                lambda checked, cid=cluster['id']: self.play_cluster.emit(cid)
            )
            self.table.setCellWidget(row, 4, play_btn)
    
    def on_item_clicked(self, item):
        """Handle item click."""
        row = item.row()
        if row < len(self.clusters):
            cluster_id = self.clusters[row]['id']
            self.current_cluster_id = cluster_id
            self.cluster_selected.emit(cluster_id)
    
    def get_labels(self):
        """Get labels from table."""
        labels = {}
        for row in range(self.table.rowCount()):
            cluster_id = int(self.table.item(row, 0).text())
            character = self.table.item(row, 1).text().strip()
            if character:
                labels[cluster_id] = character
        return labels
    
    def save_labels(self):
        """Save labels to CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Labels",
            "manual_labels.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            import csv
            labels = self.get_labels()
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['cluster_id', 'character', 'count', 'first_occurrence_seconds', 'notes'])
                
                for cluster in self.clusters:
                    cluster_id = cluster['id']
                    character = labels.get(cluster_id, '')
                    count = cluster['count']
                    first_occ = cluster['segments'][0]['start_seconds'] if cluster['segments'] else 0
                    
                    writer.writerow([cluster_id, character, count, f"{first_occ:.2f}", ''])
            
            self.info_label.setText(f"✓ Saved to {file_path}")
            self.info_label.setStyleSheet("color: #4CAF50; font-weight: bold;")