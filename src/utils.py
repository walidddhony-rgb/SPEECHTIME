"""
Utility functions.
"""

from datetime import timedelta


def format_time(seconds):
    """Format seconds as HH:MM:SS."""
    td = timedelta(seconds=int(seconds))
    return str(td)


def seconds_to_srt_time(seconds):
    """Convert seconds to SRT time format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"