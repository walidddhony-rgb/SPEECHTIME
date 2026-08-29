"""SpeechScribe professional desktop UI with multi-format audio metadata support."""

from __future__ import annotations

import contextlib
import math
import random
import wave
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from src.analysis_engine import AnalysisEngine, AnalysisProgress
from src.whisper_transcriber import LocalWhisperTranscriber, export_whisper_result
from transcript_editor import WhisperTranscriptEditor

try:
    import soundfile as sf
except ImportError:
    sf = None

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None


SUPPORTED_SUFFIXES = {".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".oga", ".aiff", ".aif"}
DURATION_ESTIMATE_SUFFIXES = {".mp3", ".m4a", ".aac"}
COMPRESSED_SUFFIXES = {".mp3", ".m4a", ".aac", ".ogg", ".oga"}


@dataclass(frozen=True)
class AudioInfo:
    path: Path
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None
    bit_depth: int | None
    size_bytes: int
    format_name: str
    backend: str
    warning: str | None = None
    estimated: bool = False

    @property
    def ready(self) -> bool:
        return self.duration_seconds is not None and self.sample_rate is not None


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "Unknown"
    seconds = max(0, int(round(seconds)))
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_srt_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    whole_secs = int(secs)
    millis = int((secs - whole_secs) * 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_secs:02d},{millis:03d}"


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def _estimate_compressed_duration(size_bytes: int) -> tuple[float, str]:
    return size_bytes / 16000.0, "Duration is estimated because no MP3/M4A decoder was found. Install soundfile or pydub + FFmpeg."


def inspect_audio(path: str | Path) -> AudioInfo:
    audio_path = Path(path).expanduser().resolve()
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file was not found: {audio_path}")

    suffix = audio_path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        allowed = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"Unsupported audio format: {suffix or 'no extension'}\nSupported: {allowed}")

    size_bytes = audio_path.stat().st_size
    format_name = suffix.lstrip(".").upper()

    if suffix == ".wav":
        try:
            with contextlib.closing(wave.open(str(audio_path), "rb")) as source:
                sample_rate = source.getframerate()
                channels = source.getnchannels()
                bit_depth = source.getsampwidth() * 8
                frame_count = source.getnframes()
            duration = frame_count / sample_rate if sample_rate else None
            return AudioInfo(audio_path, duration, sample_rate, channels, bit_depth, size_bytes, format_name, "Python wave")
        except wave.Error as exc:
            raise ValueError(f"The WAV file could not be read: {exc}") from exc

    if sf is not None:
        try:
            info = sf.info(str(audio_path))
            bit_depth = None
            subtype = (getattr(info, "subtype", "") or "").upper()
            if "PCM_16" in subtype:
                bit_depth = 16
            elif "PCM_24" in subtype:
                bit_depth = 24
            elif "PCM_32" in subtype or "FLOAT" in subtype:
                bit_depth = 32
            return AudioInfo(
                audio_path,
                float(info.duration),
                int(info.samplerate),
                int(info.channels),
                bit_depth,
                size_bytes,
                format_name,
                "soundfile / libsndfile",
            )
        except Exception:
            pass

    if AudioSegment is not None:
        try:
            audio = AudioSegment.from_file(str(audio_path))
            return AudioInfo(
                audio_path,
                len(audio) / 1000.0,
                audio.frame_rate,
                audio.channels,
                audio.sample_width * 8,
                size_bytes,
                format_name,
                "pydub + FFmpeg",
            )
        except Exception as exc:
            return AudioInfo(
                audio_path,
                None,
                None,
                None,
                None,
                size_bytes,
                format_name,
                "pydub unavailable",
                warning=(
                    f"{format_name} was selected, but it could not be decoded. "
                    "Install FFmpeg or the soundfile package. "
                    f"Decoder error: {exc}"
                ),
            )

    if suffix in DURATION_ESTIMATE_SUFFIXES:
        duration, warning = _estimate_compressed_duration(size_bytes)
        return AudioInfo(
            audio_path,
            duration,
            None,
            None,
            None,
            size_bytes,
            format_name,
            "file-size estimate",
            warning=warning,
            estimated=True,
        )

    return AudioInfo(
        audio_path,
        None,
        None,
        None,
        None,
        size_bytes,
        format_name,
        "none",
        warning=f"{format_name} requires the optional soundfile package or FFmpeg decoder.",
    )


class SpeechScribeUI(tk.Tk):
    BG = "#0B1020"
    HEADER = "#0F1730"
    PANEL = "#141B31"
    PANEL_2 = "#1C2643"
    CANVAS = "#0D1428"
    BORDER = "#2B3B62"
    TEXT = "#E8EEFC"
    MUTED = "#94A3C4"
    CYAN = "#26D9FF"
    BLUE = "#4777FF"
    GREEN = "#2EE59D"
    AMBER = "#FFB74D"
    RED = "#FF668A"

    def __init__(self):
        super().__init__()
        self.title("SpeechScribe — Semi-Automatic Speech Transcription")
        self.geometry("1440x860")
        self.minsize(1120, 700)
        self.configure(bg=self.BG)

        self.audio_info: AudioInfo | None = None
        self.total_seconds = 0.0
        self.playhead_percent = 0.0
        self.is_playing = False
        self.total_clusters = 0
        self.labeled_clusters = 0
        self.current_cluster_id = 0
        self.analysis_ready = False
        self.cluster_labels: dict[str, str] = {}

        self.analysis_engine = AnalysisEngine()
        self.analysis_progress = AnalysisProgress("", 0, "")
        self._analysis_poll_id = None

        self.whisper_worker = LocalWhisperTranscriber()
        self.whisper_result = None
        self.transcript_editor_window = None
        self._whisper_poll_id = None

        self._configure_styles()
        self._build_layout()
        self.after(120, self._redraw_waveform)
        self.after(40, self._animation_tick)

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Cyan.Horizontal.TProgressbar",
            troughcolor=self.PANEL_2,
            background=self.CYAN,
            bordercolor=self.PANEL_2,
            lightcolor=self.CYAN,
            darkcolor=self.CYAN,
            thickness=8,
        )
        style.configure(
            "Treeview",
            background="#10182D",
            foreground=self.TEXT,
            fieldbackground="#10182D",
            rowheight=29,
            font=("Segoe UI", 9),
            bordercolor=self.BORDER,
        )
        style.configure(
            "Treeview.Heading",
            background=self.PANEL_2,
            foreground=self.MUTED,
            relief="flat",
            font=("Segoe UI", 8, "bold"),
        )
        style.map("Treeview", background=[("selected", "#294876")], foreground=[("selected", "#FFFFFF")])

    def _label(self, parent, text, size=10, color=None, bold=False, bg=None, **kwargs):
        return tk.Label(parent, text=text, bg=bg or self.PANEL, fg=color or self.TEXT, font=("Segoe UI", size, "bold" if bold else "normal"), **kwargs)

    def _button(self, parent, text, command, accent=False, width=None):
        bg = self.BLUE if accent else self.PANEL_2
        active = "#698DFF" if accent else "#2B3B62"
        return tk.Button(parent, text=text, command=command, bg=bg, fg="#FFFFFF" if accent else self.TEXT, activebackground=active, activeforeground="#FFFFFF", relief="flat", bd=0, padx=12, pady=8, cursor="hand2", font=("Segoe UI", 9, "bold"), width=width)

    def _card(self, parent, height=None):
        frame = tk.Frame(parent, bg=self.PANEL, highlightthickness=1, highlightbackground=self.BORDER)
        if height:
            frame.configure(height=height)
            frame.pack_propagate(False)
        return frame

    def _build_layout(self):
        self._build_header()
        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        sidebar = tk.Frame(body, bg=self.BG, width=265)
        sidebar.pack(side="left", fill="y", padx=(0, 14))
        sidebar.pack_propagate(False)
        workspace = tk.Frame(body, bg=self.BG)
        workspace.pack(side="left", fill="both", expand=True)
        self._build_sidebar(sidebar)
        self._build_workspace(workspace)

    def _build_header(self):
        header = tk.Frame(self, bg=self.HEADER, height=72, highlightthickness=1, highlightbackground=self.BORDER)
        header.pack(fill="x")
        header.pack_propagate(False)
        left = tk.Frame(header, bg=self.HEADER)
        left.pack(side="left", padx=22)
        icon = tk.Canvas(left, width=34, height=34, bg=self.HEADER, highlightthickness=0)
        icon.pack(side="left", pady=18)
        icon.create_oval(2, 2, 32, 32, fill=self.CYAN, outline="")
        for x, y1, y2 in ((12, 12, 22), (17, 8, 26), (22, 13, 21)):
            icon.create_line(x, y1, x, y2, fill=self.HEADER, width=3)
        title_box = tk.Frame(left, bg=self.HEADER)
        title_box.pack(side="left", padx=10)
        self._label(title_box, "SpeechScribe", 15, self.TEXT, True, bg=self.HEADER).pack(anchor="w")
        self._label(title_box, "Multi-format Speech Transcription Studio", 9, self.MUTED, bg=self.HEADER).pack(anchor="w")
        right = tk.Frame(header, bg=self.HEADER)
        right.pack(side="right", padx=20)
        decoder_color = self.GREEN if (sf is not None or AudioSegment is not None) else self.AMBER
        decoder_text = "Audio decoders available" if (sf is not None or AudioSegment is not None) else "WAV active · optional decoders missing"
        self._label(right, "●", 14, decoder_color, bg=self.HEADER).pack(side="left", padx=(0, 5))
        self._label(right, decoder_text, 10, self.TEXT, True, bg=self.HEADER).pack(side="left", padx=(0, 18))
        self._button(right, "⚙ Settings", self.show_settings).pack(side="left")

    def _build_sidebar(self, parent):
        source = self._card(parent, 182)
        source.pack(fill="x", pady=(0, 14))
        self._label(source, "AUDIO SOURCE", 9, self.MUTED, True).pack(anchor="w", padx=16, pady=(15, 8))
        self.file_name_label = self._label(source, "No audio file selected", 10, self.TEXT, True)
        self.file_name_label.pack(anchor="w", padx=16)
        self.file_meta_label = self._label(source, "WAV works immediately; MP3/FLAC/M4A use installed decoders", 9, self.MUTED, wraplength=225, justify="left")
        self.file_meta_label.pack(anchor="w", padx=16, pady=(4, 10))
        self._button(source, "⌁  Select Audio File", self.select_audio, accent=True).pack(fill="x", padx=16, pady=(0, 14))

        workflow = self._card(parent)
        workflow.pack(fill="both", expand=True, pady=(0, 14))
        self._label(workflow, "WORKFLOW", 9, self.MUTED, True).pack(anchor="w", padx=16, pady=(16, 8))
        self.step_widgets = []
        steps = [("1", "Load audio", "Waiting for audio file"), ("2", "Inspect metadata", "Not started"), ("3", "Extract segments", "Next stage"), ("4", "Cluster sounds", "Next stage"), ("5", "Label clusters", "Waiting"), ("6", "Generate transcript", "Demo only")]
        for number, title, subtitle in steps:
            row = tk.Frame(workflow, bg=self.PANEL)
            row.pack(fill="x", padx=16, pady=6)
            badge = tk.Label(row, text=number, width=2, bg=self.MUTED, fg="#08101F", font=("Segoe UI", 9, "bold"), padx=4, pady=3)
            badge.pack(side="left", padx=(0, 9))
            text_box = tk.Frame(row, bg=self.PANEL)
            text_box.pack(side="left", fill="x", expand=True)
            self._label(text_box, title, 10, self.TEXT, True).pack(anchor="w")
            sub = self._label(text_box, subtitle, 8, self.MUTED)
            sub.pack(anchor="w")
            self.step_widgets.append((badge, sub))

        privacy = self._card(parent, 78)
        privacy.pack(fill="x")
        self._label(privacy, "🔒  PRIVACY-FIRST", 9, self.GREEN, True).pack(anchor="w", padx=15, pady=(13, 3))
        self._label(privacy, "Audio remains on this device.", 9, self.MUTED).pack(anchor="w", padx=15)

    def _build_workspace(self, parent):
        stats = tk.Frame(parent, bg=self.BG)
        stats.pack(fill="x", pady=(0, 14))
        self.stat_cards = {}
        specs = [("AUDIO DURATION", "--:--:--", "No file loaded", self.CYAN), ("UNIQUE CLUSTERS", "—", "Analysis not run", self.AMBER), ("ESTIMATED SAVINGS", "—", "Requires clustering", self.GREEN), ("PROCESSING STATUS", "Ready", "Select an audio file", self.BLUE)]
        for index, (title, value, subtitle, color) in enumerate(specs):
            card = self._card(stats, 96)
            card.pack(side="left", fill="x", expand=True, padx=(0 if index == 0 else 10, 0))
            self._label(card, title, 8, self.MUTED, True).pack(anchor="w", padx=15, pady=(14, 3))
            value_label = self._label(card, value, 18, color, True)
            value_label.pack(anchor="w", padx=15)
            sub_label = self._label(card, subtitle, 8, self.MUTED)
            sub_label.pack(anchor="w", padx=15)
            self.stat_cards[title] = (value_label, sub_label)

        split = tk.Frame(parent, bg=self.BG)
        split.pack(fill="both", expand=True)
        main = tk.Frame(split, bg=self.BG)
        main.pack(side="left", fill="both", expand=True, padx=(0, 14))
        clusters = tk.Frame(split, bg=self.BG, width=340)
        clusters.pack(side="left", fill="both")
        clusters.pack_propagate(False)
        self._build_audio_area(main)
        self._build_transcript_area(main)
        self._build_cluster_area(clusters)

    def _build_audio_area(self, parent):
        card = self._card(parent, 258)
        card.pack(fill="x", pady=(0, 14))
        top = tk.Frame(card, bg=self.PANEL)
        top.pack(fill="x", padx=16, pady=(14, 0))
        self._label(top, "AUDIO TIMELINE", 10, self.TEXT, True).pack(side="left")
        self.timeline_status = self._label(top, "●  Waiting for audio", 9, self.MUTED, True)
        self.timeline_status.pack(side="right")
        self.wave_canvas = tk.Canvas(card, height=122, bg=self.PANEL, highlightthickness=0, cursor="hand2")
        self.wave_canvas.pack(fill="x", padx=16, pady=(8, 2))
        self.wave_canvas.bind("<Button-1>", self.seek_audio)
        controls = tk.Frame(card, bg=self.PANEL)
        controls.pack(fill="x", padx=16, pady=(3, 13))
        self.play_button = self._button(controls, "▶  Preview", self.toggle_preview, accent=True, width=11)
        self.play_button.pack(side="left")
        self._button(controls, "■  Reset", self.stop_preview, width=9).pack(side="left", padx=8)
        self.analyze_button = self._button(controls, "🔬 Analyze", self.start_analysis, accent=True, width=11)
        self.analyze_button.pack(side="left", padx=8)
        self.analyze_button.config(state="disabled")

        self.whisper_model = tk.StringVar(value="small")
        self.whisper_model_menu = ttk.Combobox(
            controls, textvariable=self.whisper_model,
            values=("tiny", "base", "small", "medium", "large-v3-turbo"),
            state="readonly", width=8,
        )
        self.whisper_model_menu.pack(side="left", padx=(8, 4))
        self.whisper_button = self._button(controls, "📝 Whisper", self.start_whisper, accent=True, width=12)
        self.whisper_button.pack(side="left", padx=(0, 8))
        self.whisper_button.config(state="disabled")
        self.review_button = self._button(
            controls,
            "✎ Review",
            self.open_timeline_editor,
            width=10,
        )
        self.review_button.pack(side="left", padx=(0, 8))
        self.review_button.config(state="disabled")
        self.time_label = self._label(controls, "00:00:00  /  --:--:--", 10, self.MUTED, True)
        self.time_label.pack(side="left", padx=10)
        tk.Frame(controls, bg=self.PANEL).pack(side="left", fill="x", expand=True)
        self._label(controls, "Volume", 9, self.MUTED).pack(side="left", padx=(0, 7))
        self.volume = tk.Scale(controls, from_=0, to=100, orient="horizontal", length=112, showvalue=False, bg=self.PANEL, fg=self.TEXT, troughcolor=self.PANEL_2, highlightthickness=0, activebackground=self.CYAN)
        self.volume.set(75)
        self.volume.pack(side="left")

    def _build_transcript_area(self, parent):
        card = self._card(parent)
        card.pack(fill="both", expand=True)
        top = tk.Frame(card, bg=self.PANEL)
        top.pack(fill="x", padx=16, pady=(15, 10))
        self._label(top, "TRANSCRIPTION PREVIEW", 10, self.TEXT, True).pack(side="left")
        right = tk.Frame(top, bg=self.PANEL)
        right.pack(side="right")
        self.confidence_label = self._label(right, "Confidence: --", 9, self.MUTED, True)
        self.confidence_label.pack(side="left", padx=10)
        self._button(right, "↻ Refresh", self.render_transcript).pack(side="left")
        holder = tk.Frame(card, bg=self.CANVAS, highlightthickness=1, highlightbackground=self.BORDER)
        holder.pack(fill="both", expand=True, padx=16, pady=(0, 13))
        self.transcript = tk.Text(holder, bg=self.CANVAS, fg=self.TEXT, insertbackground=self.CYAN, relief="flat", bd=0, wrap="word", font=("Segoe UI", 11), padx=16, pady=14, spacing1=4, spacing3=8)
        self.transcript.pack(side="left", fill="both", expand=True)
        scroll = tk.Scrollbar(holder, command=self.transcript.yview)
        scroll.pack(side="right", fill="y")
        self.transcript.config(yscrollcommand=scroll.set)
        self.transcript.tag_configure("time", foreground=self.CYAN, font=("Consolas", 9, "bold"))
        self.transcript.tag_configure("title", foreground=self.GREEN, font=("Segoe UI", 10, "bold"))
        self.transcript.tag_configure("note", foreground=self.AMBER)
        self.render_transcript()

    def _build_cluster_area(self, parent):
        card = self._card(parent)
        card.pack(fill="both", expand=True)
        header = tk.Frame(card, bg=self.PANEL)
        header.pack(fill="x", padx=14, pady=(15, 8))
        self._label(header, "SOUND CLUSTERS", 10, self.TEXT, True).pack(side="left")
        self.cluster_count = self._label(header, "0 / 0", 9, self.MUTED, True)
        self.cluster_count.pack(side="right")
        self.cluster_progress = ttk.Progressbar(card, orient="horizontal", mode="determinate", maximum=1, value=0, style="Cyan.Horizontal.TProgressbar")
        self.cluster_progress.pack(fill="x", padx=14, pady=(0, 8))
        self._label(card, "Real clusters appear after the processing integration stage.", 9, self.MUTED, wraplength=290, justify="left").pack(anchor="w", padx=14, pady=(0, 9))
        holder = tk.Frame(card, bg=self.PANEL)
        holder.pack(fill="both", expand=True, padx=14)
        columns = ("id", "samples", "label", "state")
        self.cluster_tree = ttk.Treeview(holder, columns=columns, show="headings", height=12, selectmode="browse")
        for name, heading, width in (("id", "ID", 48), ("samples", "Samples", 82), ("label", "Label", 62), ("state", "State", 82)):
            self.cluster_tree.heading(name, text=heading)
            self.cluster_tree.column(name, width=width, anchor="center")
        scroll = ttk.Scrollbar(holder, orient="vertical", command=self.cluster_tree.yview)
        self.cluster_tree.configure(yscrollcommand=scroll.set)
        self.cluster_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.cluster_tree.bind("<<TreeviewSelect>>", self.select_cluster)
        actions = tk.Frame(card, bg=self.PANEL)
        actions.pack(fill="x", padx=14, pady=13)
        self._button(actions, "▶ Listen", self.listen_cluster, width=10).pack(side="left")
        self.label_entry = tk.Entry(
            actions,
            bg="#FFFFFF",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            bd=1,
            font=("Segoe UI", 11, "bold"),
            justify="center",
            width=14,
        )
        self.label_entry.pack(side="left", padx=7, ipady=5)
        self.label_entry.bind("<Return>", self.assign_label)
        self._button(actions, "Assign", self.assign_label, accent=True).pack(side="left")

        self.selected_cluster_label = self._label(
            card,
            "Selected: none — choose a row, type its label, press Assign",
            8,
            self.MUTED,
            wraplength=290,
            justify="left",
        )
        self.selected_cluster_label.pack(anchor="w", padx=14, pady=(0, 8))
        bottom = tk.Frame(card, bg=self.PANEL)
        bottom.pack(fill="x", padx=14, pady=(0, 15))
        self._button(bottom, "Generate Text", self.generate_text, accent=True).pack(side="left", fill="x", expand=True)
        self._button(bottom, "Export", self.export_results).pack(side="left", padx=(8, 0))

    def _redraw_waveform(self):
        canvas = self.wave_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 720)
        height = 122
        center = height / 2
        canvas.create_line(0, center, width, center, fill="#253555", width=1)
        random.seed(self.audio_info.size_bytes if self.audio_info else 42)
        colors = [self.CYAN, self.BLUE, "#7B61FF", self.CYAN, self.GREEN, self.BLUE]
        for x in range(0, width, 4):
            envelope = 7 if not self.audio_info else 14 + 27 * abs(math.sin(x / 120))
            noise = random.uniform(-7, 7)
            amplitude = max(3, envelope * abs(math.sin(x / 23)) + noise)
            canvas.create_line(x, center - amplitude, x, center + amplitude, fill=colors[(x // max(1, int(width / 12))) % len(colors)], width=2)
        for index in range(13):
            x = int(index * width / 12)
            canvas.create_line(x, 4, x, height - 4, fill="#21304E", dash=(2, 5))
            canvas.create_text(x + 4, height - 7, text=format_duration((self.total_seconds or 0) * index / 12), anchor="sw", fill=self.MUTED, font=("Consolas", 8))
        playhead = width * self.playhead_percent / 100
        canvas.create_line(playhead, 3, playhead, height - 3, fill="#FFFFFF", width=2)
        canvas.create_oval(playhead - 4, 2, playhead + 4, 10, fill="#FFFFFF", outline="")

    def _animation_tick(self):
        if self.is_playing and self.total_seconds > 0:
            self.playhead_percent += 0.10
            if self.playhead_percent >= 100:
                self.stop_preview()
            else:
                self._update_time_display()
                self._redraw_waveform()
        self.after(40, self._animation_tick)

    def _update_time_display(self):
        elapsed = self.total_seconds * self.playhead_percent / 100
        self.time_label.config(text=f"{format_duration(elapsed)}  /  {format_duration(self.total_seconds) if self.total_seconds else '--:--:--'}")

    def _short_name(self, name: str, limit: int = 38) -> str:
        if len(name) <= limit:
            return name
        return name[:18] + "…" + name[-17:]

    def _metadata_summary(self, info: AudioInfo) -> str:
        duration = format_duration(info.duration_seconds)
        if info.estimated:
            duration = f"{duration} (estimated)"
        sample_rate = f"{info.sample_rate:,} Hz" if info.sample_rate else "Unknown rate"
        if info.channels == 1:
            channel_text = "Mono"
        elif info.channels and info.channels > 1:
            channel_text = f"Stereo ({info.channels})"
        else:
            channel_text = "Channels unknown"
        if info.bit_depth:
            bit_text = f"{info.bit_depth}-bit"
        elif info.format_name in {"MP3", "M4A", "AAC", "OGG"}:
            bit_text = "Bit depth: N/A (compressed)"
        else:
            bit_text = "Bit depth unknown"
        return f"{info.format_name} · {duration} · {sample_rate} · {channel_text} · {bit_text} · {format_size(info.size_bytes)}"

    def select_audio(self):
        path = filedialog.askopenfilename(title="Select audio file", filetypes=[("Audio files", "*.wav *.mp3 *.flac *.m4a *.aac *.ogg *.oga *.aiff *.aif"), ("WAV files", "*.wav"), ("MP3 files", "*.mp3"), ("FLAC files", "*.flac"), ("OGG files", "*.ogg *.oga"), ("M4A/AAC files", "*.m4a *.aac"), ("AIFF files", "*.aiff *.aif"), ("All files", "*.*")])
        if not path:
            return
        try:
            info = inspect_audio(path)
        except (FileNotFoundError, ValueError) as exc:
            messagebox.showerror("Audio loading error", str(exc))
            return

        self.audio_info = info
        self.total_seconds = info.duration_seconds or 0.0
        self.playhead_percent = 0.0
        self.is_playing = False
        self.play_button.config(text="▶  Preview")
        self.file_name_label.config(text=self._short_name(info.path.name))
        self.file_meta_label.config(text=self._metadata_summary(info))
        self.step_widgets[0][0].config(bg=self.GREEN)
        self.step_widgets[0][1].config(text=f"{info.format_name} file loaded")

        if info.ready:
            self.step_widgets[1][0].config(bg=self.GREEN)
            self.step_widgets[1][1].config(text=f"Read via {info.backend}")
            self.timeline_status.config(text="●  Real audio metadata loaded", fg=self.GREEN)
            self.stat_cards["AUDIO DURATION"][0].config(text=format_duration(info.duration_seconds))
            self.stat_cards["AUDIO DURATION"][1].config(text=f"{info.sample_rate:,} Hz · {info.channels or '?'} channel(s)")
            self.stat_cards["PROCESSING STATUS"][0].config(text="Loaded", fg=self.CYAN)
            self.stat_cards["PROCESSING STATUS"][1].config(text="Ready for analysis")
            self.confidence_label.config(text="Confidence: pending analysis", fg=self.AMBER)
            self.analyze_button.config(state="normal")
            self.whisper_button.config(state="normal")
        else:
            self.step_widgets[1][0].config(bg=self.AMBER)
            self.step_widgets[1][1].config(text="Decoder required for details")
            self.timeline_status.config(text="●  File selected — decoder required", fg=self.AMBER)
            self.stat_cards["PROCESSING STATUS"][0].config(text="Selected", fg=self.AMBER)
            self.stat_cards["PROCESSING STATUS"][1].config(text="Install decoder for metadata")
            self.confidence_label.config(text="Confidence: metadata unavailable", fg=self.MUTED)
            self.analyze_button.config(state="disabled")
            messagebox.showinfo("Audio selected", info.warning or "Audio file selected, but its detailed metadata is unavailable.")

        self._update_time_display()
        self._redraw_waveform()
        self.render_transcript()

    def toggle_preview(self):
        if not self.audio_info:
            messagebox.showinfo("Preview unavailable", "Select an audio file first.")
            return
        if self.total_seconds <= 0:
            messagebox.showinfo("Preview unavailable", "This file needs an audio decoder before timeline preview can be used.")
            return
        self.is_playing = not self.is_playing
        self.play_button.config(text="❚❚ Pause" if self.is_playing else "▶  Preview")
        self.timeline_status.config(text="●  Preview timeline running" if self.is_playing else "●  Preview paused", fg=self.CYAN if self.is_playing else self.AMBER)

    def stop_preview(self):
        self.is_playing = False
        self.playhead_percent = 0.0
        self.play_button.config(text="▶  Preview")
        self.timeline_status.config(text="●  Ready for analysis" if self.audio_info else "●  Waiting for audio", fg=self.GREEN if self.audio_info else self.MUTED)
        self._update_time_display()
        self._redraw_waveform()

    def seek_audio(self, event):
        if self.total_seconds <= 0:
            return
        width = max(self.wave_canvas.winfo_width(), 720)
        self.playhead_percent = max(0, min(100, event.x / width * 100))
        self._update_time_display()
        self._redraw_waveform()

    def start_whisper(self):
        """Run local Arabic Whisper without freezing the desktop UI."""
        if not self.audio_info or not self.audio_info.ready:
            messagebox.showwarning("No audio", "Select a decodable audio file first.")
            return
        if self.whisper_worker.is_running:
            return

        model_name = self.whisper_model.get().strip() or "small"
        self.whisper_result = None
        self.whisper_button.config(state="disabled", text="⏳ Whisper...")
        self.analyze_button.config(state="disabled")
        self.timeline_status.config(text=f"●  Loading local Whisper model: {model_name}", fg=self.CYAN)
        self.stat_cards["PROCESSING STATUS"][0].config(text="Whisper", fg=self.CYAN)
        self.stat_cards["PROCESSING STATUS"][1].config(text="Automatic Arabic transcription")

        try:
            self.whisper_worker.start(
                self.audio_info.path,
                model_name=model_name,
                language="ar",
                device="cpu",
                compute_type="int8",
                beam_size=5,
            )
        except Exception as exc:
            self.whisper_button.config(state="normal", text="📝 Whisper")
            self.analyze_button.config(state="normal")
            messagebox.showerror("Whisper error", str(exc))
            return
        self._poll_whisper()

    def _poll_whisper(self):
        event = self.whisper_worker.next_event()
        if event:
            self.timeline_status.config(text=f"●  {event.message}", fg=self.CYAN)
            if event.stage == "complete":
                self._on_whisper_complete()
                return
            if event.stage == "error":
                self.whisper_button.config(state="normal", text="📝 Whisper")
                self.analyze_button.config(state="normal")
                messagebox.showerror("Whisper error", event.message)
                return
            if event.stage == "cancelled":
                self.whisper_button.config(state="normal", text="📝 Whisper")
                self.analyze_button.config(state="normal")
                return
        self._whisper_poll_id = self.after(120, self._poll_whisper)

    def _on_whisper_complete(self):
        self.whisper_result = self.whisper_worker.result
        self.whisper_button.config(state="normal", text="📝 Whisper")
        self.analyze_button.config(state="normal")
        if self.whisper_result is None:
            messagebox.showerror("Whisper error", "Whisper returned no transcript.")
            return

        self.transcript.delete("1.0", "end")
        self.transcript.insert("end", "SPEECHSCRIBE WHISPER TRANSCRIPT\n\n", "title")
        self.transcript.insert(
            "end",
            f"Model: {self.whisper_result.model_name} | Language: {self.whisper_result.language} | "
            f"Segments: {len(self.whisper_result.segments)}\n\n",
            "note",
        )
        for segment in self.whisper_result.segments:
            self.transcript.insert(
                "end",
                f"[{format_srt_time(segment.start)} → {format_srt_time(segment.end)}] ",
                "time",
            )
            self.transcript.insert("end", segment.text + "\n\n")
        self.stat_cards["PROCESSING STATUS"][0].config(text="Whisper", fg=self.GREEN)
        self.stat_cards["PROCESSING STATUS"][1].config(text="Arabic transcript ready")
        self.confidence_label.config(text="Whisper transcript ready", fg=self.GREEN)
        self.timeline_status.config(text="●  Automatic Arabic transcript completed", fg=self.GREEN)
        self.step_widgets[5][0].config(bg=self.GREEN)
        self.step_widgets[5][1].config(text="Whisper transcript ready")
        self.review_button.config(state="normal")


    def open_timeline_editor(self):
        """Open the editable timestamp/text review window for Whisper output."""
        if self.whisper_result is None:
            messagebox.showinfo(
                "No Whisper transcript",
                "Run 📝 Whisper first. The review editor opens after a real transcript is available.",
            )
            return
        if self.transcript_editor_window is not None and self.transcript_editor_window.winfo_exists():
            self.transcript_editor_window.focus_set()
            return
        self.transcript_editor_window = WhisperTranscriptEditor(
            self,
            self.whisper_result,
            self.apply_reviewed_whisper_result,
        )

    def apply_reviewed_whisper_result(self, revised_result):
        """Accept reviewed segments and immediately refresh the main preview."""
        self.whisper_result = revised_result
        self.transcript.delete("1.0", "end")
        self.transcript.insert("end", "SPEECHSCRIBE REVIEWED WHISPER TRANSCRIPT\n\n", "title")
        self.transcript.insert(
            "end",
            f"Model: {revised_result.model_name} | Language: {revised_result.language} | "
            f"Edited segments: {len(revised_result.segments)}\n\n",
            "note",
        )
        for segment in revised_result.segments:
            self.transcript.insert(
                "end",
                f"[{format_srt_time(segment.start)} → {format_srt_time(segment.end)}] ",
                "time",
            )
            self.transcript.insert("end", segment.text + "\n\n")
        self.stat_cards["PROCESSING STATUS"][0].config(text="Reviewed", fg=self.GREEN)
        self.stat_cards["PROCESSING STATUS"][1].config(text="Edited Whisper timeline active")
        self.confidence_label.config(text="Reviewed transcript ready", fg=self.GREEN)
        self.timeline_status.config(text="●  Timeline edits saved — ready to export", fg=self.GREEN)


    def start_analysis(self):
        if not self.audio_info or not self.audio_info.ready:
            messagebox.showwarning("No audio", "Select a decodable audio file first.")
            return
        if self.analysis_engine.is_running:
            return
        self.analyze_button.config(state="disabled", text="⏳ Analyzing...")
        self.timeline_status.config(text="●  Starting analysis...", fg=self.CYAN)
        self.cluster_tree.delete(*self.cluster_tree.get_children())
        self.total_clusters = 0
        self.labeled_clusters = 0
        self.analysis_ready = False
        self.analysis_engine.start_analysis(self.audio_info.path, segment_ms=25.0, overlap_ms=12.5, max_clusters=100)
        self._poll_analysis()

    def _poll_analysis(self):
        progress = self.analysis_engine.get_progress()
        if progress:
            self.analysis_progress = progress
            self.timeline_status.config(text=f"●  {progress.message}", fg=self.CYAN)
            if progress.stage == "complete":
                self._on_analysis_complete()
                return
            elif progress.stage == "error":
                messagebox.showerror("Analysis error", progress.message)
                self.analyze_button.config(state="normal", text="🔬 Analyze")
                return
            elif progress.stage == "cancelled":
                self.analyze_button.config(state="normal", text="🔬 Analyze")
                return
        self._analysis_poll_id = self.after(100, self._poll_analysis)

    def _on_analysis_complete(self):
        result = self.analysis_engine.result
        if not result or result.error:
            self.analyze_button.config(state="normal", text="🔬 Analyze")
            return
        self.total_clusters = result.cluster_count
        self.labeled_clusters = 0
        self.analysis_ready = True
        self.analyze_button.config(state="normal", text="🔬 Analyze")
        self.timeline_status.config(text=f"●  Analysis complete: {result.cluster_count} clusters", fg=self.GREEN)
        self.stat_cards["UNIQUE CLUSTERS"][0].config(text=str(result.cluster_count), fg=self.GREEN)
        self.stat_cards["UNIQUE CLUSTERS"][1].config(text=f"{result.segment_count:,} segments")
        self.stat_cards["PROCESSING STATUS"][0].config(text="Analyzed", fg=self.GREEN)
        self.stat_cards["PROCESSING STATUS"][1].config(text="Ready for labeling")
        self.cluster_count.config(text=f"0 / {result.cluster_count}")
        self.cluster_progress.configure(maximum=result.cluster_count, value=0)
        summary = self.analysis_engine.get_cluster_summary()
        for idx, item in enumerate(summary):
            self.cluster_tree.insert("", "end", iid=str(idx), values=(item["id"], f"{item['samples']:,}", item["label"], item["state"]))
        self.step_widgets[2][0].config(bg=self.GREEN)
        self.step_widgets[2][1].config(text=f"{result.segment_count:,} segments extracted")
        self.step_widgets[3][0].config(bg=self.GREEN)
        self.step_widgets[3][1].config(text=f"{result.cluster_count} clusters found")
        self.step_widgets[4][1].config(text=f"0 / {result.cluster_count} labeled")
        self.confidence_label.config(text="Confidence: pending labels", fg=self.AMBER)

    def select_cluster(self, _event=None):
        """Record the actual selected cluster ID and prepare its label editor."""
        selection = self.cluster_tree.selection()
        if not selection:
            return

        self.selected_tree_item = selection[0]
        values = self.cluster_tree.item(self.selected_tree_item, "values")
        if not values:
            return

        try:
            self.current_cluster_id = int(str(values[0]).replace("C-", ""))
        except ValueError:
            self.current_cluster_id = int(self.selected_tree_item)

        current_label = str(values[2]) if len(values) > 2 else "—"
        self.label_entry.delete(0, "end")
        if current_label != "—":
            self.label_entry.insert(0, current_label)

        self.selected_cluster_label.config(text=f"Selected: {values[0]}")
        self.label_entry.focus_set()

    def listen_cluster(self):
        if not self.analysis_ready:
            messagebox.showinfo("No clusters yet", "Real sound clusters will appear after the processing integration step.")
            return
        self.timeline_status.config(text="●  Cluster preview selected", fg=self.CYAN)

    def assign_label(self, _event=None):
        """Assign a user label to the cluster selected in the table."""
        if not self.analysis_ready:
            messagebox.showinfo("No clusters", "Run 🔬 Analyze before labeling clusters.")
            return

        selection = self.cluster_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Select a cluster",
                "Click one row in SOUND CLUSTERS, type its label, then click Assign.",
            )
            return

        item_id = selection[0]
        values = list(self.cluster_tree.item(item_id, "values"))
        label = self.label_entry.get().strip()
        if not label:
            messagebox.showwarning(
                "Missing label",
                "Type a character, phoneme, syllable, or word in the Label field before clicking Assign.",
            )
            self.label_entry.focus_set()
            return

        try:
            cluster_id = int(str(values[0]).replace("C-", ""))
        except (IndexError, ValueError):
            messagebox.showerror("Labeling error", "The selected row has an invalid cluster ID.")
            return

        was_unlabeled = len(values) < 3 or values[2] == "—"
        if was_unlabeled:
            self.labeled_clusters += 1

        values[2] = label
        values[3] = "Labeled"
        self.cluster_tree.item(item_id, values=values)
        self.cluster_labels[str(cluster_id)] = label

        self.cluster_count.config(text=f"{self.labeled_clusters} / {self.total_clusters}")
        self.cluster_progress.configure(maximum=max(1, self.total_clusters), value=self.labeled_clusters)
        self.step_widgets[4][0].config(bg=self.GREEN)
        self.step_widgets[4][1].config(text=f"{self.labeled_clusters} / {self.total_clusters} labeled")
        self.selected_cluster_label.config(text=f"Saved: C-{cluster_id:03d} → {label}")
        self.timeline_status.config(text=f"●  Labeled C-{cluster_id:03d} as {label}", fg=self.GREEN)

        if self.labeled_clusters >= self.total_clusters:
            self.step_widgets[5][0].config(bg=self.GREEN)
            self.step_widgets[5][1].config(text="All clusters labeled")
            self.confidence_label.config(text="Confidence: 100% labeled", fg=self.GREEN)

        children = self.cluster_tree.get_children()
        try:
            next_index = children.index(item_id) + 1
        except ValueError:
            next_index = len(children)
        if next_index < len(children):
            next_item = children[next_index]
            self.cluster_tree.selection_set(next_item)
            self.cluster_tree.focus(next_item)
            self.cluster_tree.see(next_item)
            self.select_cluster()

    def _generate_timed_transcript(self):
        """Build time-ordered transcript blocks from real cluster assignments."""
        if not self.analysis_ready or not self.analysis_engine.result:
            return []

        result = self.analysis_engine.result
        labels = result.cluster_assignments
        start_times = result.segments_start_times
        end_times = result.segments_end_times

        cluster_map = {}
        for item in self.cluster_tree.get_children():
            values = self.cluster_tree.item(item, "values")
            if len(values) >= 3 and values[2] != "—":
                try:
                    cluster_id = int(str(values[0]).replace("C-", ""))
                    cluster_map[cluster_id] = str(values[2])
                except ValueError:
                    continue

        timed_segments = []
        current_label = None
        current_start = None
        current_end = None

        for index, raw_cluster_id in enumerate(labels):
            cluster_id = int(raw_cluster_id)
            label = cluster_map.get(cluster_id, f"[unlabeled C-{cluster_id:03d}]")
            start = float(start_times[index])
            end = float(end_times[index])

            if current_label is None:
                current_label = label
                current_start = start
                current_end = end
            elif label == current_label:
                current_end = end
            else:
                timed_segments.append((current_start, current_end, current_label))
                current_label = label
                current_start = start
                current_end = end

        if current_label is not None:
            timed_segments.append((current_start, current_end, current_label))
        return timed_segments

    def generate_text(self):
        if not self.audio_info:
            messagebox.showwarning("No audio", "Select an audio file first.")
            return
        if not self.analysis_ready:
            messagebox.showwarning("No analysis", "Run 🔬 Analyze first to generate real clusters.")
            return

        if self.labeled_clusters == 0:
            messagebox.showinfo(
                "No labels",
                "No clusters are labeled yet.\n"
                "Choose a row in SOUND CLUSTERS, type a label in the white field, "
                "then click Assign.",
            )
            return

        timed_segments = self._generate_timed_transcript()

        self.transcript.delete("1.0", "end")
        self.transcript.insert("end", "SPEECHSCRIBE REAL TRANSCRIPT\n\n", "title")
        self.transcript.insert("end", f"Source: {self.audio_info.path.name}\n", "note")
        self.transcript.insert("end", f"Duration: {format_duration(self.audio_info.duration_seconds)}\n", "note")
        self.transcript.insert("end", f"Clusters: {self.total_clusters} total, {self.labeled_clusters} labeled\n\n", "note")

        if self.labeled_clusters == 0:
            self.transcript.insert("end", "⚠  No clusters labeled yet — output shows unlabeled segments.\n\n", "note")
        elif self.labeled_clusters < self.total_clusters:
            self.transcript.insert("end", f"⚠  Partial labeling: {self.labeled_clusters}/{self.total_clusters} clusters labeled.\n\n", "note")

        for start, end, label in timed_segments:
            time_tag = f"[{format_srt_time(start)}] "
            self.transcript.insert("end", time_tag, "time")
            self.transcript.insert("end", f"{label}\n\n")

        self.stat_cards["PROCESSING STATUS"][0].config(text="Transcript", fg=self.GREEN)
        self.stat_cards["PROCESSING STATUS"][1].config(text="Real text generated")
        self.confidence_label.config(text=f"Confidence: {self.labeled_clusters}/{self.total_clusters} labeled", fg=self.GREEN)
        self.timeline_status.config(text="●  Real transcript generated from labeled clusters", fg=self.GREEN)
        self.step_widgets[5][0].config(bg=self.GREEN)
        self.step_widgets[5][1].config(text="Transcript generated")

    def render_transcript(self, show_demo=False):
        self.transcript.delete("1.0", "end")
        self.transcript.insert("end", "SPEECHSCRIBE TRANSCRIPTION PREVIEW\n\n", "title")
        if self.analysis_ready:
            self.transcript.insert("end", f"Analysis complete — {self.total_clusters} clusters from {self.analysis_engine.result.segment_count:,} segments. Label clusters to generate transcript.\n\n", "note")
        else:
            self.transcript.insert("end", "Demo output only — audio analysis and clustering are not yet connected.\n\n", "note")
        if not self.audio_info:
            self.transcript.insert("end", "Select WAV immediately, or install optional decoders to inspect MP3, FLAC, M4A/AAC, OGG, and AIFF.\n\n")
            self.transcript.insert("end", "Optional decoder: py -m pip install soundfile\n", "note")
            return
        self.transcript.insert("end", "[00:00:00] ", "time")
        self.transcript.insert("end", f"Loaded file: {self.audio_info.path.name}\n\n")
        self.transcript.insert("end", "[00:00:00] ", "time")
        self.transcript.insert("end", f"Metadata — {self._metadata_summary(self.audio_info)}; reader: {self.audio_info.backend}.\n\n")
        if self.audio_info.warning:
            self.transcript.insert("end", self.audio_info.warning + "\n\n", "note")
        if show_demo and self.analysis_ready:
            self.transcript.insert("end", "[00:00:03] ", "time")
            self.transcript.insert("end", f"Analysis ready: {self.total_clusters} clusters labeled ({self.labeled_clusters}/{self.total_clusters}). Generate transcript from labels.\n\n")
        elif show_demo:
            self.transcript.insert("end", "[00:00:03] ", "time")
            self.transcript.insert("end", "Demo transcript: analysis not run yet.\n\n")
        else:
            self.transcript.insert("end", "Ready for local analysis. Use Generate Text only to preview the export workflow; it is not a real transcript yet.\n", "note")

    def export_results(self):
        if self.whisper_result is None:
            messagebox.showinfo(
                "No Whisper transcript",
                "Click 📝 Whisper after selecting an audio file. Export will then save the automatic Arabic transcript.",
            )
            return
        directory = filedialog.askdirectory(title="Choose Whisper export folder")
        if not directory:
            return
        try:
            paths = export_whisper_result(self.whisper_result, directory)
        except OSError as exc:
            messagebox.showerror("Export error", str(exc))
            return
        messagebox.showinfo(
            "Whisper export complete",
            "Created real Whisper files:\n"
            f"- {paths['txt'].name}\n- {paths['csv'].name}\n"
            f"- {paths['srt'].name}\n- {paths['json'].name}",
        )
        self.timeline_status.config(text="●  Whisper transcript exported", fg=self.GREEN)


    def show_settings(self):
        window = tk.Toplevel(self)
        window.title("SpeechScribe Settings")
        window.geometry("470x355")
        window.configure(bg=self.PANEL)
        window.resizable(False, False)
        window.transient(self)
        self._label(window, "Processing Settings", 14, self.TEXT, True).pack(anchor="w", padx=24, pady=(22, 18))
        decoder_status = "soundfile installed" if sf is not None else ("pydub installed" if AudioSegment is not None else "Standard WAV only")
        fields = [("Segment length", "25 ms"), ("Segment overlap", "50%"), ("Similarity threshold", "0.85"), ("Audio decoder", decoder_status)]
        for title, value in fields:
            row = tk.Frame(window, bg=self.PANEL)
            row.pack(fill="x", padx=24, pady=7)
            self._label(row, title, 10, self.MUTED).pack(side="left")
            entry = tk.Entry(row, bg=self.CANVAS, fg=self.TEXT, relief="flat", font=("Segoe UI", 10), width=25)
            entry.insert(0, value)
            entry.pack(side="right", ipady=5)
        self._button(window, "Close", window.destroy, accent=True).pack(anchor="e", padx=24, pady=20)


if __name__ == "__main__":
    SpeechScribeUI().mainloop()
