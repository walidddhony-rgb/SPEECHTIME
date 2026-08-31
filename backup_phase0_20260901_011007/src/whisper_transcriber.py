"""Local Arabic Whisper transcription service for SpeechScribe."""
from __future__ import annotations
import csv, json, queue, threading
from dataclasses import asdict, dataclass
from pathlib import Path

@dataclass(frozen=True)
class WhisperWord:
    start: float
    end: float
    text: str
    probability: float | None = None

@dataclass(frozen=True)
class WhisperSegment:
    start: float
    end: float
    text: str
    avg_logprob: float | None = None
    no_speech_prob: float | None = None
    words: tuple[WhisperWord, ...] = ()

@dataclass(frozen=True)
class WhisperProgress:
    stage: str
    percent: int | None
    message: str

@dataclass(frozen=True)
class WhisperResult:
    audio_path: Path
    language: str
    language_probability: float | None
    model_name: str
    segments: tuple[WhisperSegment, ...]
    @property
    def text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments if s.text.strip()).strip()

def srt_timestamp(seconds: float) -> str:
    ms=round(max(0.0,float(seconds))*1000)
    h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

class LocalWhisperTranscriber:
    def __init__(self):
        self._events=queue.Queue(); self._thread=None; self._cancel=threading.Event()
        self._result=None; self._error=None
    @property
    def is_running(self): return self._thread is not None and self._thread.is_alive()
    @property
    def result(self): return self._result
    @property
    def error(self): return self._error
    def next_event(self):
        try: return self._events.get_nowait()
        except queue.Empty: return None
    def cancel(self): self._cancel.set()
    def _emit(self,stage,message,percent=None): self._events.put(WhisperProgress(stage,percent,message))
    def start(self,audio_path,model_name="small",language="ar",device="cpu",compute_type="int8",beam_size=5):
        if self.is_running: raise RuntimeError("Whisper transcription is already running.")
        self._cancel.clear(); self._result=None; self._error=None
        self._thread=threading.Thread(target=self._run,args=(Path(audio_path),model_name,language,device,compute_type,beam_size),daemon=True)
        self._thread.start()
    def _run(self,path,model_name,language,device,compute_type,beam_size):
        try:
            if not path.is_file(): raise FileNotFoundError(f"Audio file not found: {path}")
            try: from faster_whisper import WhisperModel
            except ImportError as exc: raise RuntimeError("faster-whisper is not installed. Run INSTALL_WHISPER.bat first.") from exc
            self._emit("model",f"Loading local Whisper '{model_name}' model...")
            model=WhisperModel(model_name,device=device,compute_type=compute_type)
            if self._cancel.is_set(): self._emit("cancelled","Whisper transcription cancelled."); return
            self._emit("transcribing","Transcribing Arabic speech locally with Whisper...")
            stream,info=model.transcribe(str(path),language=language,task="transcribe",beam_size=beam_size,vad_filter=True,word_timestamps=True,condition_on_previous_text=True)
            segments=[]
            for count,segment in enumerate(stream,1):
                if self._cancel.is_set(): self._emit("cancelled","Whisper transcription cancelled."); return
                words=tuple(WhisperWord(float(w.start),float(w.end),str(w.word),float(w.probability) if getattr(w,"probability",None) is not None else None) for w in (getattr(segment,"words",None) or []))
                segments.append(WhisperSegment(float(segment.start),float(segment.end),str(segment.text).strip(),float(segment.avg_logprob) if getattr(segment,"avg_logprob",None) is not None else None,float(segment.no_speech_prob) if getattr(segment,"no_speech_prob",None) is not None else None,words))
                self._emit("transcribing",f"Decoded {count} transcript segment(s)...")
            lang=str(getattr(info,"language",language or "unknown")); prob=getattr(info,"language_probability",None)
            self._result=WhisperResult(path,lang,float(prob) if prob is not None else None,model_name,tuple(segments))
            self._emit("complete",f"Whisper completed: {len(segments)} text segments in {lang}.",100)
        except Exception as exc:
            self._error=str(exc); self._emit("error",f"Whisper failed: {exc}")

def export_whisper_result(result, output_dir, stem="speechscribe_whisper"):
    output=Path(output_dir); output.mkdir(parents=True,exist_ok=True)
    paths={"txt":output/f"{stem}.txt","csv":output/f"{stem}.csv","srt":output/f"{stem}.srt","json":output/f"{stem}.json"}
    lines=["SpeechScribe local Whisper transcript",f"Source: {result.audio_path.name}",f"Model: {result.model_name}",f"Language: {result.language}",""]
    lines += [f"[{srt_timestamp(s.start)} -> {srt_timestamp(s.end)}] {s.text}" for s in result.segments]
    paths["txt"].write_text("\n".join(lines)+"\n",encoding="utf-8")
    with paths["csv"].open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["start_time","end_time","text","avg_logprob","no_speech_prob"]); writer.writeheader()
        for s in result.segments: writer.writerow({"start_time":srt_timestamp(s.start),"end_time":srt_timestamp(s.end),"text":s.text,"avg_logprob":s.avg_logprob,"no_speech_prob":s.no_speech_prob})
    srt=[]
    for i,s in enumerate(result.segments,1): srt.extend([str(i),f"{srt_timestamp(s.start)} --> {srt_timestamp(s.end)}",s.text,""])
    paths["srt"].write_text("\n".join(srt),encoding="utf-8")
    payload={"audio_path":str(result.audio_path),"language":result.language,"language_probability":result.language_probability,"model_name":result.model_name,"segments":[asdict(s) for s in result.segments]}
    paths["json"].write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    return paths
