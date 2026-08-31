"""Arabic text normalization for fair ASR evaluation.

Raw WER on unnormalized Arabic punishes orthographic variants that do
not change meaning (diacritics, hamza seats, ta marbuta, alef maqsura,
tatweel). This module applies a conservative normalization before
scoring so engine errors are counted, not spelling conventions.
"""
from __future__ import annotations

import re

_ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_TATWEEL = "\u0640"

_KEEP = re.compile(r"[^\u0600-\u06FF\u0750-\u077FA-Za-z0-9\s]")


def normalize_ar(text: str) -> str:
    """Normalize Arabic/Latin text for WER/CER scoring."""
    if not text:
        return ""
    text = _ARABIC_DIACRITICS.sub("", text)
    text = text.replace(_TATWEEL, "")
    text = re.sub("[\u0623\u0625\u0622\u0671]", "\u0627", text)  # أ إ آ ٱ -> ا
    text = text.replace("\u0649", "\u064A")  # ى -> ي
    text = text.replace("\u0629", "\u0647")  # ة -> ه
    text = text.replace("\u0624", "\u0648")  # ؤ -> و
    text = text.replace("\u0626", "\u064A")  # ئ -> ي
    text = _KEEP.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()
