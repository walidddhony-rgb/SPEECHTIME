from __future__ import annotations
import argparse, time
from pathlib import Path
from src.whisper_transcriber import LocalWhisperTranscriber, export_whisper_result
p=argparse.ArgumentParser(description="SpeechScribe local Whisper transcription")
p.add_argument("audio"); p.add_argument("--model",default="small",choices=["tiny","base","small","medium","large-v3-turbo"]); p.add_argument("--language",default="ar"); p.add_argument("--output",default="Export")
a=p.parse_args(); worker=LocalWhisperTranscriber(); worker.start(a.audio,model_name=a.model,language=None if a.language=="auto" else a.language)
while worker.is_running:
    event=worker.next_event()
    if event: print(event.message)
    time.sleep(0.1)
while True:
    event=worker.next_event()
    if not event: break
    print(event.message)
if worker.error or worker.result is None:
    raise SystemExit(f"ERROR: {worker.error or 'No transcript returned'}")
for kind,path in export_whisper_result(worker.result,Path(a.output)).items(): print(f"{kind.upper()}: {path}")
