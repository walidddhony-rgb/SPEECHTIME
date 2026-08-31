"""SpeechScribe core package.

Exports the documented public API so that ``from src import SpeechTranscriber``
(README, docs/api.md, examples) works as documented.
"""
from .transcriber import SpeechTranscriber

__all__ = ["SpeechTranscriber"]
