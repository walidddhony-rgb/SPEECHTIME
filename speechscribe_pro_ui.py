import math
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path


class SpeechScribeUI(tk.Tk):
    BG = "#0b1020"
    PANEL = "#141b31"
    PANEL_2 = "#1c2643"
    BORDER = "#2b3b62"
    TEXT = "#e8eefc"
    MUTED = "#94a3c4"
    CYAN = "#26d9ff"
    BLUE = "#4777ff"
    GREEN = "#2ee59d"
    AMBER = "#ffb74d"
    RED = "#ff668a"

    def __init__(self):
        super().__init__()
        self.title("SpeechScribe \u2014 Semi-Automatic Speech Transcription")
        self.geometry("1440x860")
        self.minsize(1180, 720)
        self.configure(bg=self.BG)

        self.audio_path = None
        self.is_playing = False
        self.progress_value = 0
        self.total_clusters = 86
        self.labeled_clusters = 23
        self.selected_cluster = 0

        self._configure_styles()
        self._build_layout()
        self._draw_waveform()
        self._populate_clusters()
        self._update_dashboard()
        self._animate_waveform()

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "TProgressbar",
            troughcolor=self.PANEL_2,
            background=self.CYAN,
            bordercolor=self.PANEL_2,
            lightcolor=self.CYAN,
            darkcolor=self.CYAN,
            thickness=8,
        )

        style.configure(
            "Horizontal.TScale",
            background=self.PANEL,
            troughcolor=self.PANEL_2,
            sliderlength=14,
        )

    def make_button(self, parent, text, command=None, accent=False, danger=False, width=None):
        bg = self.BLUE if accent else self.PANEL_2
        fg = "#ffffff" if accent else self.TEXT
        active = "#698dff" if accent else "#263557"

        if danger:
            bg, active, fg = "#512238", "#7a314f", "#ffdbe5"

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active,
            activeforeground=fg,
            relief="flat",
            bd=0,
            padx=14,
            pady=9,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            width=width,
        )

    def make_label(self, parent, text, size=10, color=None, bold=False, **kwargs):
        return tk.Label(
            parent,
            text=text,
            bg=kwargs.pop("bg", self.PANEL),
            fg=color or self.TEXT,
            font=("Segoe UI", size, "bold" if bold else "normal"),
            **kwargs,
        )

    def card(self, parent, padx=16, pady=14):
        frame = tk.Frame(parent, bg=self.PANEL, highlightthickness=1, highlightbackground=self.BORDER)
        frame.pack_propagate(False)
        return frame

    def _build_layout(self):
        self._build_header()

        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        sidebar = tk.Frame(body, bg=self.BG, width=255)
        sidebar.pack(side="left", fill="y", padx=(0, 14))
        sidebar.pack_propagate(False)

        workspace = tk.Frame(body, bg=self.BG)
        workspace.pack(side="left", fill="both", expand=True)

        self._build_sidebar(sidebar)
        self._build_workspace(workspace)

    def _build_header(self):
        header = tk.Frame(self, bg="#0f1730", height=72, highlightthickness=1, highlightbackground=self.BORDER)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg="#0f1730")
        brand.pack(side="left", padx=22)

        icon = tk.Canvas(brand, width=34, height=34, bg="#0f1730", highlightthickness=0)
        icon.pack(side="left", pady=18)
        icon.create_oval(2, 2, 32, 32, fill=self.CYAN, outline="")
        icon.create_line(12, 12, 12, 22, fill="#0f1730", width=3)
        icon.create_line(17, 9, 17, 25, fill="#0f1730", width=3)
        icon.create_line(22, 13, 22, 21, fill="#0f1730", width=3)

        title_box = tk.Frame(brand, bg="#0f1730")
        title_box.pack(side="left", padx=10)
        tk.Label(
            title_box,
            text="SpeechScribe",
            bg="#0f1730",
            fg=self.TEXT,
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="Semi-Automatic Speech Transcription",
            bg="#0f1730",
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        right = tk.Frame(header, bg="#0f1730")
        right.pack(side="right", padx=20)

        self.status_dot = tk.Label(right, text="\u25cf", bg="#0f1730", fg=self.GREEN, font=("Segoe UI", 14))
        self.status_dot.pack(side="left", padx=(0, 5))

        tk.Label(
            right,
            text="Local Processing Ready",
            bg="#0f1730",
            fg=self.TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(0, 18))

        self.make_button(right, "\u2699 Settings", self.show_settings).pack(side="left")

    def _build_sidebar(self, parent):
        source_card = self.card(parent)
        source_card.pack(fill="x", pady=(0, 14))
        source_card.configure(height=176)

        self.make_label(source_card, "AUDIO SOURCE", 9, self.MUTED, True).pack(anchor="w", padx=16, pady=(15, 8))
        self.file_name_label = self.make_label(source_card, "No audio file selected", 10, self.TEXT, True)
        self.file_name_label.pack(anchor="w", padx=16)

        self.file_meta_label = self.make_label(source_card, "Choose WAV, MP3, FLAC or M4A", 9, self.MUTED)
        self.file_meta_label.pack(anchor="w", padx=16, pady=(4, 12))

        self.make_button(
            source_card,
            "\u23c1  Select Audio File",
            self.select_audio,
            accent=True,
        ).pack(fill="x", padx=16, pady=(0, 14))

        steps_card = self.card(parent)
        steps_card.pack(fill="both", expand=True, pady=(0, 14))

        self.make_label(steps_card, "WORKFLOW", 9, self.MUTED, True).pack(anchor="w", padx=16, pady=(16, 8))

        self.step_labels = []
        steps = [
            ("1", "Load audio", "Ready"),
            ("2", "Extract segments", "25 ms windows"),
            ("3", "Cluster sounds", "86 clusters found"),
            ("4", "Label clusters", "23 / 86 completed"),
            ("5", "Generate transcript", "Waiting"),
            ("6", "Export results", "TXT \u00b7 CSV \u00b7 SRT"),
        ]

        for i, (num, title, subtitle) in enumerate(steps):
            row = tk.Frame(steps_card, bg=self.PANEL)
            row.pack(fill="x", padx=16, pady=6)

            color = self.GREEN if i < 3 else (self.AMBER if i == 3 else self.MUTED)
            bubble = tk.Label(
                row,
                text=num,
                width=2,
                bg=color,
                fg="#08101f",
                font=("Segoe UI", 9, "bold"),
                padx=4,
                pady=3,
            )
            bubble.pack(side="left", padx=(0, 9))

            text_box = tk.Frame(row, bg=self.PANEL)
            text_box.pack(side="left", fill="x", expand=True)

            title_label = self.make_label(text_box, title, 10, self.TEXT, True)
            title_label.pack(anchor="w")
            subtitle_label = self.make_label(text_box, subtitle, 8, self.MUTED)
            subtitle_label.pack(anchor="w")
            self.step_labels.append((bubble, subtitle_label))

        local_card = self.card(parent)
        local_card.pack(fill="x")
        local_card.configure(height=78)

        self.make_label(local_card, "\U0001f512  PRIVACY-FIRST", 9, self.GREEN, True).pack(anchor="w", padx=15, pady=(13, 3))
        self.make_label(local_card, "All audio is processed locally.", 9, self.MUTED).pack(anchor="w", padx=15)

    def _build_workspace(self, parent):
        stats = tk.Frame(parent, bg=self.BG)
        stats.pack(fill="x", pady=(0, 14))

        self.stat_cards = {}
        items = [
            ("AUDIO DURATION", "01:24:36", "00:00:00", self.CYAN),
            ("UNIQUE CLUSTERS", "86", "23 labeled", self.AMBER),
            ("ESTIMATED SAVINGS", "92%", "\u2248 3h 24m saved", self.GREEN),
            ("PROCESSING STATUS", "Ready", "Local engine active", self.BLUE),
        ]

        for index, (title, value, sub, color) in enumerate(items):
            item = self.card(stats)
            item.pack(side="left", fill="x", expand=True, padx=(0 if index == 0 else 10, 0))
            item.configure(height=96)

            self.make_label(item, title, 8, self.MUTED, True).pack(anchor="w", padx=15, pady=(14, 3))
            value_label = self.make_label(item, value, 19, color, True)
            value_label.pack(anchor="w", padx=15)
            sub_label = self.make_label(item, sub, 8, self.MUTED)
            sub_label.pack(anchor="w", padx=15)
            self.stat_cards[title] = (value_label, sub_label)

        split = tk.Frame(parent, bg=self.BG)
        split.pack(fill="both", expand=True)

        main_panel = tk.Frame(split, bg=self.BG)
        main_panel.pack(side="left", fill="both", expand=True, padx=(0, 14))

        cluster_panel = tk.Frame(split, bg=self.BG, width=340)
        cluster_panel.pack(side="left", fill="both")
        cluster_panel.pack_propagate(False)

        self._build_audio_area(main_panel)
        self._build_transcript_area(main_panel)
        self._build_cluster_area(cluster_panel)

    def _build_audio_area(self, parent):
        card = self.card(parent)
        card.pack(fill="x", pady=(0, 14))
        card.configure(height=258)

        top = tk.Frame(card, bg=self.PANEL)
        top.pack(fill="x", padx=16, pady=(14, 0))

        self.make_label(top, "AUDIO TIMELINE", 10, self.TEXT, True).pack(side="left")
        self.timeline_status = self.make_label(top, "\u25cf  Ready for clustering", 9, self.GREEN, True)
        self.timeline_status.pack(side="right")

        self.wave_canvas = tk.Canvas(
            card,
            height=122,
            bg=self.PANEL,
            highlightthickness=0,
            cursor="hand2",
        )
        self.wave_canvas.pack(fill="x", padx=16, pady=(8, 2))
        self.wave_canvas.bind("<Button-1>", self.seek_audio)

        controls = tk.Frame(card, bg=self.PANEL)
        controls.pack(fill="x", padx=16, pady=(3, 13))

        self.play_button = self.make_button(controls, "\u25b6  Play", self.toggle_play, accent=True, width=10)
        self.play_button.pack(side="left")

        self.stop_button = self.make_button(controls, "\u25a0  Stop", self.stop_audio, width=9)
        self.stop_button.pack(side="left", padx=8)

        self.time_label = self.make_label(controls, "00:00:00  /  01:24:36", 10, self.MUTED, True)
        self.time_label.pack(side="left", padx=10)

        tk.Frame(controls, bg=self.PANEL).pack(side="left", fill="x", expand=True)

        self.make_label(controls, "Volume", 9, self.MUTED).pack(side="left", padx=(0, 7))

        # FIX: removed value=75 from constructor, use set() instead for cross-version Tk compatibility
        self.volume = tk.Scale(
            controls,
            from_=0,
            to=100,
            orient="horizontal",
            length=115,
            showvalue=False,
            bg=self.PANEL,
            fg=self.TEXT,
            troughcolor=self.PANEL_2,
            highlightthickness=0,
            activebackground=self.CYAN,
        )
        self.volume.set(75)
        self.volume.pack(side="left")

    def _build_transcript_area(self, parent):
        card = self.card(parent)
        card.pack(fill="both", expand=True)

        top = tk.Frame(card, bg=self.PANEL)
        top.pack(fill="x", padx=16, pady=(15, 10))

        self.make_label(top, "TRANSCRIPTION PREVIEW", 10, self.TEXT, True).pack(side="left")

        right = tk.Frame(top, bg=self.PANEL)
        right.pack(side="right")

        self.confidence_label = self.make_label(right, "Confidence: 87%", 9, self.GREEN, True)
        self.confidence_label.pack(side="left", padx=10)

        self.make_button(right, "\u21bb Refresh", self.refresh_transcript).pack(side="left")

        text_frame = tk.Frame(card, bg="#0d1428", highlightthickness=1, highlightbackground=self.BORDER)
        text_frame.pack(fill="both", expand=True, padx=16, pady=(0, 13))

        self.transcript = tk.Text(
            text_frame,
            bg="#0d1428",
            fg=self.TEXT,
            insertbackground=self.CYAN,
            relief="flat",
            bd=0,
            wrap="word",
            font=("Segoe UI", 11),
            padx=16,
            pady=14,
            spacing1=4,
            spacing3=8,
        )
        self.transcript.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(text_frame, command=self.transcript.yview)
        scroll.pack(side="right", fill="y")
        self.transcript.configure(yscrollcommand=scroll.set)

        self.transcript.tag_configure("time", foreground=self.CYAN, font=("Consolas", 9, "bold"))
        self.transcript.tag_configure("uncertain", foreground=self.AMBER)
        self.transcript.tag_configure("label", foreground=self.GREEN, font=("Segoe UI", 10, "bold"))

        self.render_transcript()

    def _build_cluster_area(self, parent):
        card = self.card(parent)
        card.pack(fill="both", expand=True)

        header = tk.Frame(card, bg=self.PANEL)
        header.pack(fill="x", padx=14, pady=(15, 8))

        self.make_label(header, "SOUND CLUSTERS", 10, self.TEXT, True).pack(side="left")
        self.cluster_count = self.make_label(header, "23 / 86", 9, self.AMBER, True)
        self.cluster_count.pack(side="right")

        progress = ttk.Progressbar(
            card,
            orient="horizontal",
            mode="determinate",
            maximum=self.total_clusters,
            value=self.labeled_clusters,
        )
        progress.pack(fill="x", padx=14, pady=(0, 8))
        self.cluster_progress = progress

        self.make_label(card, "Select a cluster, listen to its example, then assign a label.", 9, self.MUTED, wraplength=290, justify="left").pack(
            anchor="w", padx=14, pady=(0, 9)
        )

        list_frame = tk.Frame(card, bg=self.PANEL)
        list_frame.pack(fill="both", expand=True, padx=14)

        columns = ("id", "samples", "label", "state")
        self.cluster_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=12,
            selectmode="browse",
        )
        self.cluster_tree.heading("id", text="ID")
        self.cluster_tree.heading("samples", text="Samples")
        self.cluster_tree.heading("label", text="Label")
        self.cluster_tree.heading("state", text="State")

        self.cluster_tree.column("id", width=48, anchor="center")
        self.cluster_tree.column("samples", width=80, anchor="center")
        self.cluster_tree.column("label", width=64, anchor="center")
        self.cluster_tree.column("state", width=85, anchor="center")

        tree_style = ttk.Style()
        tree_style.configure(
            "Treeview",
            background="#10182d",
            foreground=self.TEXT,
            fieldbackground="#10182d",
            rowheight=29,
            font=("Segoe UI", 9),
        )
        tree_style.configure(
            "Treeview.Heading",
            background=self.PANEL_2,
            foreground=self.MUTED,
            relief="flat",
            font=("Segoe UI", 8, "bold"),
        )
        tree_style.map("Treeview", background=[("selected", "#294876")], foreground=[("selected", "#ffffff")])

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.cluster_tree.yview)
        self.cluster_tree.configure(yscrollcommand=scrollbar.set)
        self.cluster_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.cluster_tree.bind("<<TreeviewSelect>>", self.select_cluster)

        action = tk.Frame(card, bg=self.PANEL)
        action.pack(fill="x", padx=14, pady=13)

        self.make_button(action, "\u25b6 Listen", self.play_cluster, width=10).pack(side="left")

        self.label_entry = tk.Entry(
            action,
            bg="#0d1428",
            fg=self.TEXT,
            insertbackground=self.CYAN,
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            justify="center",
            width=6,
        )
        self.label_entry.pack(side="left", padx=7, ipady=5)

        self.make_button(action, "Assign", self.assign_label, accent=True).pack(side="left")

        bottom = tk.Frame(card, bg=self.PANEL)
        bottom.pack(fill="x", padx=14, pady=(0, 15))

        self.make_button(bottom, "Generate Text", self.generate_text, accent=True).pack(side="left", fill="x", expand=True)
        self.make_button(bottom, "Export", self.export_results).pack(side="left", padx=(8, 0))

    def _draw_waveform(self):
        c = self.wave_canvas
        c.delete("all")

        width = max(c.winfo_width(), 850)
        height = 122
        center = height / 2
        random.seed(42)

        c.create_line(0, center, width, center, fill="#253555", width=1)

        segment_width = width / 12
        colors = [self.CYAN, self.BLUE, "#7b61ff", self.CYAN, self.GREEN, self.BLUE]

        for x in range(0, width, 4):
            phase = x / 23
            envelope = 14 + 27 * abs(math.sin(x / 120))
            noise = random.uniform(-11, 11)
            amplitude = max(5, envelope * abs(math.sin(phase)) + noise)
            color_index = min(int(x / segment_width), 11) % len(colors)
            color = colors[color_index]
            c.create_line(x, center - amplitude, x, center + amplitude, fill=color, width=2)

        for i in range(13):
            x = int(i * width / 12)
            c.create_line(x, 4, x, height - 4, fill="#21304e", dash=(2, 5))
            minutes = int((84 * i) / 12)
            c.create_text(
                x + 4,
                height - 7,
                text=f"{minutes:02d}:00",
                anchor="sw",
                fill=self.MUTED,
                font=("Consolas", 8),
            )

        position = width * self.progress_value / 100
        c.create_line(position, 3, position, height - 3, fill="#ffffff", width=2, tags="playhead")
        c.create_oval(position - 4, 2, position + 4, 10, fill="#ffffff", outline="", tags="playhead")

    def _populate_clusters(self):
        labels = ["\u0627", "\u0644", "\u0645", "\u0648", "\u0646", "\u0628", "\u0631", "\u064a", "\u062a", "\u0633", "\u0643", "\u0647", "\u062f", "\u0639", "\u0641", "\u0642", "\u062c", "\u062d", "\u0635", "\u0636"]
        random.seed(9)

        for i in range(30):
            samples = random.randint(104, 18340)
            if i < self.labeled_clusters:
                label = labels[i % len(labels)]
                state = "Labeled"
            elif i == self.labeled_clusters:
                label = "\u2014"
                state = "Current"
            else:
                label = "\u2014"
                state = "Pending"

            self.cluster_tree.insert("", "end", iid=str(i), values=(f"C-{i:03d}", f"{samples:,}", label, state))

        self.cluster_tree.selection_set("23")
        self.cluster_tree.focus("23")

    def _update_dashboard(self):
        self.cluster_count.config(text=f"{self.labeled_clusters} / {self.total_clusters}")
        self.cluster_progress["value"] = self.labeled_clusters

        self.step_labels[3][1].config(text=f"{self.labeled_clusters} / {self.total_clusters} completed")

        percentage = int((self.labeled_clusters / self.total_clusters) * 100)
        self.stat_cards["UNIQUE CLUSTERS"][1].config(text=f"{self.labeled_clusters} labeled \u00b7 {percentage}% complete")

        if self.labeled_clusters >= self.total_clusters:
            self.stat_cards["PROCESSING STATUS"][0].config(text="Complete", fg=self.GREEN)
            self.stat_cards["PROCESSING STATUS"][1].config(text="Ready to export")
            self.step_labels[4][0].config(bg=self.GREEN)
            self.step_labels[4][1].config(text="Transcript generated")
            self.step_labels[5][0].config(bg=self.GREEN)

    def _animate_waveform(self):
        if self.is_playing:
            self.progress_value += 0.18
            if self.progress_value >= 100:
                self.stop_audio()
            self._draw_waveform()
            elapsed = int((self.progress_value / 100) * (84 * 60 + 36))
            self.time_label.config(text=f"{self.format_time(elapsed)}  /  01:24:36")

        self.after(35, self._animate_waveform)

    @staticmethod
    def format_time(seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def select_audio(self):
        path = filedialog.askopenfilename(
            title="Select audio file",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.flac *.m4a"),
                ("WAV files", "*.wav"),
                ("All files", "*.*"),
            ],
        )

        if path:
            self.audio_path = Path(path)
            self.file_name_label.config(text=self.audio_path.name)
            self.file_meta_label.config(text="Audio loaded \u00b7 44.1 kHz \u00b7 Mono \u00b7 Ready")
            self.timeline_status.config(text="\u25cf  Audio loaded", fg=self.GREEN)
            self.stat_cards["PROCESSING STATUS"][0].config(text="Loaded", fg=self.CYAN)
            self.stat_cards["PROCESSING STATUS"][1].config(text="Ready for local analysis")

    def toggle_play(self):
        self.is_playing = not self.is_playing

        if self.is_playing:
            self.play_button.config(text="\u275a\u275a Pause")
            self.timeline_status.config(text="\u25cf  Playing preview", fg=self.CYAN)
        else:
            self.play_button.config(text="\u25b6  Play")
            self.timeline_status.config(text="\u25cf  Paused", fg=self.AMBER)

    def stop_audio(self):
        self.is_playing = False
        self.progress_value = 0
        self.play_button.config(text="\u25b6  Play")
        self.timeline_status.config(text="\u25cf  Ready for clustering", fg=self.GREEN)
        self.time_label.config(text="00:00:00  /  01:24:36")
        self._draw_waveform()

    def seek_audio(self, event):
        width = max(self.wave_canvas.winfo_width(), 850)
        self.progress_value = max(0, min(100, event.x / width * 100))
        self._draw_waveform()
        elapsed = int((self.progress_value / 100) * (84 * 60 + 36))
        self.time_label.config(text=f"{self.format_time(elapsed)}  /  01:24:36")

    def select_cluster(self, event=None):
        selected = self.cluster_tree.selection()
        if not selected:
            return

        self.selected_cluster = int(selected[0])
        values = self.cluster_tree.item(selected[0], "values")
        current_label = values[2] if values[2] != "\u2014" else ""
        self.label_entry.delete(0, "end")
        self.label_entry.insert(0, current_label)

        self.timeline_status.config(
            text=f"\u25cf  Cluster {values[0]} selected",
            fg=self.AMBER,
        )

    def play_cluster(self):
        values = self.cluster_tree.item(str(self.selected_cluster), "values")
        self.timeline_status.config(text=f"\u25cf  Playing sample: {values[0]}", fg=self.CYAN)
        self.progress_value = (self.selected_cluster / 30) * 100
        self._draw_waveform()
        self.after(1200, lambda: self.timeline_status.config(text="\u25cf  Sample finished", fg=self.GREEN))

    def assign_label(self):
        label = self.label_entry.get().strip()

        if not label:
            messagebox.showwarning("Missing Label", "Enter a character, phoneme, or token first.")
            return

        item_id = str(self.selected_cluster)
        values = list(self.cluster_tree.item(item_id, "values"))
        was_unlabeled = values[2] == "\u2014"

        values[2] = label
        values[3] = "Labeled"
        self.cluster_tree.item(item_id, values=values)

        if was_unlabeled:
            self.labeled_clusters = min(self.total_clusters, self.labeled_clusters + 1)

        self._update_dashboard()
        self.timeline_status.config(text=f"\u25cf  {values[0]} labeled as \u201c{label}\u201d", fg=self.GREEN)
        self.confidence_label.config(text=f"Confidence: {min(98, 87 + self.labeled_clusters // 9)}%")

        next_id = min(self.selected_cluster + 1, 29)
        self.cluster_tree.selection_set(str(next_id))
        self.cluster_tree.focus(str(next_id))
        self.cluster_tree.see(str(next_id))
        self.select_cluster()

    def render_transcript(self):
        self.transcript.delete("1.0", "end")

        blocks = [
            ("00:00:00", "SPEECHSCRIBE OUTPUT \u2014 LIVE PREVIEW", "label"),
            ("00:00:03", "\u0645\u0631\u062d\u0628\u0627\u064b \u0628\u0643\u0645 \u0641\u064a \u0646\u0638\u0627\u0645 \u0627\u0644\u062a\u0641\u0631\u064a\u063a \u0627\u0644\u0635\u0648\u062a\u064a \u0634\u0628\u0647 \u0627\u0644\u0622\u0644\u064a. \u064a\u0642\u0648\u0645 \u0627\u0644\u0646\u0638\u0627\u0645 \u0628\u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u062a\u0633\u062c\u064a\u0644 \u0645\u062d\u0644\u064a\u0627\u064b \u0648\u062a\u062c\u0645\u064a\u0639 \u0627\u0644\u0645\u0642\u0627\u0637\u0639 \u0627\u0644\u0645\u062a\u0634\u0627\u0628\u0647\u0629 \u0635\u0648\u062a\u064a\u0627\u064b.", None),
            ("00:00:18", "\u0628\u0639\u062f \u0648\u0633\u0645 \u0627\u0644\u0639\u0646\u0627\u0642\u064a\u062f \u0627\u0644\u0623\u0633\u0627\u0633\u064a\u0629\u060c \u064a\u0633\u062a\u0637\u064a\u0639 \u0627\u0644\u0646\u0638\u0627\u0645 \u0625\u0639\u0627\u062f\u0629 \u0628\u0646\u0627\u0621 \u0627\u0644\u062a\u0633\u0644\u0633\u0644 \u0627\u0644\u0632\u0645\u0646\u064a \u0644\u0644\u0646\u0635 \u0645\u0639 \u0627\u0644\u0627\u062d\u062a\u0641\u0627\u0638 \u0628\u0627\u0644\u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0627\u0644\u0632\u0645\u0646\u064a\u0629.", None),
            ("00:00:36", "\u0647\u0630\u0647 \u0627\u0644\u0639\u0628\u0627\u0631\u0629 \u062a\u062d\u062a\u0648\u064a \u0639\u0644\u0649 \u0645\u0642\u0627\u0637\u0639 \u0642\u064a\u062f \u0627\u0644\u0645\u0631\u0627\u062c\u0639\u0629 ", None),
            ("", "[\u063a\u064a\u0631 \u0645\u0624\u0643\u062f]", "uncertain"),
            ("00:00:51", "\u064a\u0645\u0643\u0646 \u0644\u0644\u0645\u0633\u062a\u062e\u062f\u0645 \u062a\u0639\u062f\u064a\u0644 \u0623\u064a \u0648\u0633\u0645 \u062b\u0645 \u0625\u0639\u0627\u062f\u0629 \u062a\u0648\u0644\u064a\u062f \u0627\u0644\u0646\u0635 \u0648\u0627\u0644\u0645\u0644\u0641\u0627\u062a \u0627\u0644\u062a\u0635\u062f\u064a\u0631\u064a\u0629 \u0645\u0628\u0627\u0634\u0631\u0629.", None),
            ("00:01:12", "\u0627\u0644\u062e\u0635\u0648\u0635\u064a\u0629 \u0645\u062d\u0641\u0648\u0638\u0629: \u0644\u0627 \u064a\u062a\u0645 \u0631\u0641\u0639 \u0627\u0644\u0645\u0644\u0641 \u0627\u0644\u0635\u0648\u062a\u064a \u0623\u0648 \u0627\u0644\u0646\u062a\u0627\u0626\u062c \u0625\u0644\u0649 \u0623\u064a \u062e\u062f\u0645\u0629 \u0633\u062d\u0627\u0628\u064a\u0629.", None),
        ]

        for time_text, content, tag in blocks:
            if time_text:
                self.transcript.insert("end", f"[{time_text}] ", "time")
            self.transcript.insert("end", content, tag)
            self.transcript.insert("end", "\n\n")

        self.transcript.insert("end", "Tip: ", "label")
        self.transcript.insert(
            "end",
            "\u0627\u062e\u062a\u0631 \u0639\u0646\u0642\u0648\u062f\u0627\u064b \u0645\u0646 \u0627\u0644\u0644\u0648\u062d\u0629 \u0627\u0644\u064a\u0645\u0646\u0649\u060c \u0627\u0633\u062a\u0645\u0639 \u0644\u0644\u0645\u062b\u0627\u0644\u060c \u062b\u0645 \u0623\u062f\u062e\u0644 \u0627\u0644\u062d\u0631\u0641 \u0623\u0648 \u0627\u0644\u0631\u0645\u0632 \u0627\u0644\u0645\u0646\u0627\u0633\u0628.",
        )
        self.transcript.config(state="normal")

    def refresh_transcript(self):
        self.render_transcript()
        self.timeline_status.config(text="\u25cf  Preview refreshed", fg=self.GREEN)

    def generate_text(self):
        progress_window = tk.Toplevel(self)
        progress_window.title("Generating Transcript")
        progress_window.geometry("420x150")
        progress_window.configure(bg=self.PANEL)
        progress_window.resizable(False, False)
        progress_window.transient(self)
        progress_window.grab_set()

        tk.Label(
            progress_window,
            text="Generating transcription preview\u2026",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 12, "bold"),
        ).pack(pady=(25, 10))

        text = tk.Label(
            progress_window,
            text="Applying cluster labels and timestamps",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        )
        text.pack()

        bar = ttk.Progressbar(progress_window, maximum=100, mode="determinate")
        bar.pack(fill="x", padx=28, pady=16)

        def run(value=0):
            bar["value"] = value
            if value < 100:
                progress_window.after(18, lambda: run(value + 2))
            else:
                progress_window.destroy()
                self.refresh_transcript()
                self.stat_cards["PROCESSING STATUS"][0].config(text="Generated", fg=self.GREEN)
                self.stat_cards["PROCESSING STATUS"][1].config(text="Transcript preview updated")
                self.step_labels[4][0].config(bg=self.GREEN)
                self.step_labels[4][1].config(text="Preview generated")
                messagebox.showinfo("SpeechScribe", "Transcript preview generated successfully.")

        run()

    def export_results(self):
        folder = filedialog.askdirectory(title="Choose export folder")
        if not folder:
            return

        output = Path(folder)
        try:
            (output / "speechscribe_output.txt").write_text(
                "SpeechScribe transcription output\n\n"
                "\u0645\u0631\u062d\u0628\u0627\u064b \u0628\u0643\u0645 \u0641\u064a \u0646\u0638\u0627\u0645 \u0627\u0644\u062a\u0641\u0631\u064a\u063a \u0627\u0644\u0635\u0648\u062a\u064a \u0634\u0628\u0647 \u0627\u0644\u0622\u0644\u064a.\n",
                encoding="utf-8",
            )
            (output / "speechscribe_output.csv").write_text(
                "start_time,end_time,text,confidence\n"
                "00:00:03,00:00:18,\u0645\u0631\u062d\u0628\u0627\u064b \u0628\u0643\u0645 \u0641\u064a \u0646\u0638\u0627\u0645 \u0627\u0644\u062a\u0641\u0631\u064a\u063a \u0627\u0644\u0635\u0648\u062a\u064a \u0634\u0628\u0647 \u0627\u0644\u0622\u0644\u064a,0.92\n",
                encoding="utf-8",
            )
            (output / "speechscribe_subtitles.srt").write_text(
                "1\n00:00:03,000 --> 00:00:18,000\n"
                "\u0645\u0631\u062d\u0628\u0627\u064b \u0628\u0643\u0645 \u0641\u064a \u0646\u0638\u0627\u0645 \u0627\u0644\u062a\u0641\u0631\u064a\u063a \u0627\u0644\u0635\u0648\u062a\u064a \u0634\u0628\u0647 \u0627\u0644\u0622\u0644\u064a.\n",
                encoding="utf-8",
            )

            self.step_labels[5][0].config(bg=self.GREEN)
            self.step_labels[5][1].config(text="TXT \u00b7 CSV \u00b7 SRT exported")
            self.timeline_status.config(text="\u25cf  Files exported successfully", fg=self.GREEN)

            messagebox.showinfo(
                "Export Complete",
                f"Three demo files were exported to:\n{output}",
            )
        except OSError as exc:
            messagebox.showerror("Export Error", f"Could not write files:\n{exc}")

    def show_settings(self):
        window = tk.Toplevel(self)
        window.title("SpeechScribe Settings")
        window.geometry("460x390")
        window.configure(bg=self.PANEL)
        window.resizable(False, False)
        window.transient(self)

        tk.Label(
            window,
            text="Processing Settings",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w", padx=24, pady=(22, 18))

        fields = [
            ("Segment length", "25 ms"),
            ("Segment overlap", "50%"),
            ("Similarity threshold", "0.85"),
            ("Feature extractor", "Waveform similarity (simulation)"),
        ]

        for title, value in fields:
            row = tk.Frame(window, bg=self.PANEL)
            row.pack(fill="x", padx=24, pady=7)
            tk.Label(row, text=title, bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 10)).pack(side="left")
            entry = tk.Entry(row, bg="#0d1428", fg=self.TEXT, relief="flat", font=("Segoe UI", 10))
            entry.insert(0, value)
            entry.pack(side="right", ipadx=8, ipady=5)

        self.make_button(window, "Save Settings", window.destroy, accent=True).pack(
            anchor="e", padx=24, pady=20
        )


if __name__ == "__main__":
    app = SpeechScribeUI()
    app.mainloop()
