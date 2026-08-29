"""Editable timeline review window for SpeechScribe Whisper transcripts."""
from __future__ import annotations

from dataclasses import replace
import tkinter as tk
from tkinter import messagebox, ttk

from src.whisper_transcriber import WhisperResult, WhisperSegment, srt_timestamp


class WhisperTranscriptEditor(tk.Toplevel):
    """Review and edit Whisper segment text and timing before export."""

    BG = "#141B31"
    CANVAS = "#0D1428"
    BORDER = "#2B3B62"
    TEXT = "#E8EEFC"
    MUTED = "#94A3C4"
    CYAN = "#26D9FF"
    BLUE = "#4777FF"
    GREEN = "#2EE59D"
    AMBER = "#FFB74D"

    def __init__(self, parent, result: WhisperResult, on_save):
        super().__init__(parent)
        self.parent = parent
        self.result = result
        self.on_save = on_save
        self.segments = list(result.segments)
        self.current_index: int | None = None

        self.title("SpeechScribe — Timeline Transcript Review")
        self.geometry("1180x720")
        self.minsize(900, 570)
        self.configure(bg=self.BG)
        self.transient(parent)

        self._style()
        self._build()
        self._populate()
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Review.Treeview",
            background=self.CANVAS,
            foreground=self.TEXT,
            fieldbackground=self.CANVAS,
            rowheight=32,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Review.Treeview.Heading",
            background="#1C2643",
            foreground=self.MUTED,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
        )
        style.map("Review.Treeview", background=[("selected", "#294876")], foreground=[("selected", "#FFFFFF")])

    def _button(self, parent, text, command, accent=False, width=None):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.BLUE if accent else "#1C2643",
            fg="#FFFFFF" if accent else self.TEXT,
            activebackground="#698DFF" if accent else "#2B3B62",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            width=width,
        )

    def _build(self):
        header = tk.Frame(self, bg=self.BG)
        header.pack(fill="x", padx=18, pady=(16, 10))
        tk.Label(header, text="WHISPER TIMELINE REVIEW", bg=self.BG, fg=self.TEXT, font=("Segoe UI", 14, "bold")).pack(side="left")
        self.status = tk.Label(header, text="Select a row to edit its timestamp or text", bg=self.BG, fg=self.MUTED, font=("Segoe UI", 9))
        self.status.pack(side="right")

        summary = tk.Label(
            self,
            text=f"Source: {self.result.audio_path.name}  |  Model: {self.result.model_name}  |  Language: {self.result.language}  |  Segments: {len(self.segments)}",
            bg="#1C2643",
            fg=self.CYAN,
            anchor="w",
            padx=14,
            pady=8,
            font=("Segoe UI", 9, "bold"),
        )
        summary.pack(fill="x", padx=18, pady=(0, 10))

        table_box = tk.Frame(self, bg=self.BG)
        table_box.pack(fill="both", expand=True, padx=18)
        columns = ("number", "start", "end", "text")
        self.tree = ttk.Treeview(table_box, columns=columns, show="headings", style="Review.Treeview", selectmode="browse")
        headings = {"number": "#", "start": "Start", "end": "End", "text": "Transcript text"}
        widths = {"number": 55, "start": 120, "end": 120, "text": 760}
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="center" if column != "text" else "w")
        scroll = ttk.Scrollbar(table_box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.select_row)

        edit = tk.Frame(self, bg="#1C2643", highlightthickness=1, highlightbackground=self.BORDER)
        edit.pack(fill="x", padx=18, pady=12)
        tk.Label(edit, text="Selected segment", bg="#1C2643", fg=self.MUTED, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=12, pady=(10, 3), sticky="w")
        tk.Label(edit, text="Start (seconds)", bg="#1C2643", fg=self.MUTED, font=("Segoe UI", 9, "bold")).grid(row=0, column=1, padx=6, pady=(10, 3), sticky="w")
        tk.Label(edit, text="End (seconds)", bg="#1C2643", fg=self.MUTED, font=("Segoe UI", 9, "bold")).grid(row=0, column=2, padx=6, pady=(10, 3), sticky="w")
        tk.Label(edit, text="Corrected text", bg="#1C2643", fg=self.MUTED, font=("Segoe UI", 9, "bold")).grid(row=0, column=3, padx=6, pady=(10, 3), sticky="w")

        self.segment_id = tk.Label(edit, text="—", bg="#1C2643", fg=self.TEXT, font=("Segoe UI", 10, "bold"))
        self.segment_id.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="w")
        self.start_entry = tk.Entry(edit, width=15, bg="#FFFFFF", fg="#111827", insertbackground="#111827", font=("Consolas", 10))
        self.start_entry.grid(row=1, column=1, padx=6, pady=(0, 12), ipady=5, sticky="ew")
        self.end_entry = tk.Entry(edit, width=15, bg="#FFFFFF", fg="#111827", insertbackground="#111827", font=("Consolas", 10))
        self.end_entry.grid(row=1, column=2, padx=6, pady=(0, 12), ipady=5, sticky="ew")
        self.text_entry = tk.Entry(edit, bg="#FFFFFF", fg="#111827", insertbackground="#111827", font=("Segoe UI", 11), justify="right")
        self.text_entry.grid(row=1, column=3, padx=6, pady=(0, 12), ipady=5, sticky="ew")
        edit.columnconfigure(3, weight=1)
        self._button(edit, "Save Segment", self.save_segment, accent=True).grid(row=1, column=4, padx=12, pady=(0, 12))

        footer = tk.Frame(self, bg=self.BG)
        footer.pack(fill="x", padx=18, pady=(0, 16))
        self._button(footer, "↻ Restore original text", self.restore_selected).pack(side="left")
        self._button(footer, "Save review to main app", self.apply_review, accent=True).pack(side="right")
        self._button(footer, "Close", self.close).pack(side="right", padx=(0, 8))

    def _populate(self):
        self.tree.delete(*self.tree.get_children())
        for index, segment in enumerate(self.segments):
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(index + 1, srt_timestamp(segment.start), srt_timestamp(segment.end), segment.text),
            )

    def select_row(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        self.current_index = int(selected[0])
        segment = self.segments[self.current_index]
        self.segment_id.config(text=f"Segment {self.current_index + 1}")
        for entry, value in ((self.start_entry, f"{segment.start:.3f}"), (self.end_entry, f"{segment.end:.3f}"), (self.text_entry, segment.text)):
            entry.delete(0, "end")
            entry.insert(0, value)
        self.status.config(text=f"Editing segment {self.current_index + 1}", fg=self.CYAN)
        self.text_entry.focus_set()

    def save_segment(self):
        if self.current_index is None:
            messagebox.showwarning("Select a segment", "Select one transcript row first.", parent=self)
            return
        try:
            start = float(self.start_entry.get().strip())
            end = float(self.end_entry.get().strip())
        except ValueError:
            messagebox.showerror("Invalid time", "Start and end must be numeric seconds, for example 12.500.", parent=self)
            return
        text = self.text_entry.get().strip()
        if start < 0 or end <= start:
            messagebox.showerror("Invalid time", "End time must be greater than start time, and start cannot be negative.", parent=self)
            return
        if not text:
            messagebox.showwarning("Empty text", "Transcript text cannot be empty.", parent=self)
            return
        self.segments[self.current_index] = replace(self.segments[self.current_index], start=start, end=end, text=text)
        self._populate()
        item = str(self.current_index)
        self.tree.selection_set(item)
        self.tree.focus(item)
        self.tree.see(item)
        self.status.config(text=f"Saved segment {self.current_index + 1}", fg=self.GREEN)

    def restore_selected(self):
        if self.current_index is None:
            messagebox.showwarning("Select a segment", "Select one transcript row first.", parent=self)
            return
        original = self.result.segments[self.current_index]
        self.segments[self.current_index] = original
        self.select_row()
        self._populate()
        self.tree.selection_set(str(self.current_index))
        self.status.config(text=f"Restored original segment {self.current_index + 1}", fg=self.AMBER)

    def apply_review(self):
        revised = replace(self.result, segments=tuple(self.segments))
        self.on_save(revised)
        self.status.config(text="Review saved to SpeechScribe. Use Export for corrected TXT/CSV/SRT/JSON.", fg=self.GREEN)
        messagebox.showinfo("Review saved", "Your corrected timeline is now active in the main application.", parent=self)

    def close(self):
        self.destroy()
