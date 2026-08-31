"""
Text generation utilities.
"""

import csv


class TextGenerator:
    """Generate text from clustered segments."""
    
    def generate(
        self,
        clusters,
        labels,
        audio_length,
        sample_rate,
    ):
        """
        Generate text timeline from labeled clusters.
        
        Args:
            clusters: List of cluster dictionaries
            labels: Dictionary mapping cluster_id to character
            audio_length: Total audio length in samples
            sample_rate: Sample rate in Hz
            
        Returns:
            list: List of text segment dictionaries
        """
        # Create timeline
        text_timeline = [None] * audio_length
        
        # Fill timeline with characters
        for cluster in clusters:
            cluster_id = cluster["id"]
            
            if cluster_id not in labels:
                continue
            
            character = labels[cluster_id]
            
            for segment in cluster["segments"]:
                start = segment["start"]
                end = segment["end"]
                
                for pos in range(start, end + 1):
                    if pos < len(text_timeline):
                        text_timeline[pos] = character
        
        # Group consecutive characters
        text_result = []
        current_char = None
        current_start = None
        
        for pos, char in enumerate(text_timeline):
            if char != current_char:
                if current_char is not None:
                    text_result.append({
                        "character": current_char,
                        "start": current_start,
                        "end": pos - 1,
                        "start_seconds": current_start / sample_rate,
                        "end_seconds": (pos - 1) / sample_rate,
                    })
                current_char = char
                current_start = pos
        
        if current_char is not None:
            text_result.append({
                "character": current_char,
                "start": current_start,
                "end": audio_length - 1,
                "start_seconds": current_start / sample_rate,
                "end_seconds": (audio_length - 1) / sample_rate,
            })
        
        return text_result
    
    def save(
        self,
        text_result,
        output_txt,
        output_csv,
        output_srt,
    ):
        """
        Save text in multiple formats.
        
        Args:
            text_result: List of text segment dictionaries
            output_txt: Output TXT file path
            output_csv: Output CSV file path
            output_srt: Output SRT file path
        """
        # Save TXT
        with open(output_txt, "w", encoding="utf-8-sig") as f:
            for item in text_result:
                if item["character"]:
                    f.write(item["character"])
        
        # Save CSV
        with open(
            output_csv,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as f:
            writer = csv.writer(f)
            
            writer.writerow([
                "character",
                "start_sample",
                "end_sample",
                "start_time",
                "end_time",
            ])
            
            for item in text_result:
                writer.writerow([
                    item["character"] or "",
                    item["start"],
                    item["end"],
                    f"{item['start_seconds']:.3f}",
                    f"{item['end_seconds']:.3f}",
                ])
        
        # Save SRT
        with open(output_srt, "w", encoding="utf-8-sig") as f:
            subtitle_index = 1
            
            for item in text_result:
                if not item["character"]:
                    continue
                
                start_time = self._seconds_to_srt_time(
                    item["start_seconds"]
                )
                
                end_time = self._seconds_to_srt_time(
                    item["end_seconds"]
                )
                
                f.write(f"{subtitle_index}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{item['character']}\n\n")
                
                subtitle_index += 1
    
    def _seconds_to_srt_time(self, seconds):
        """Convert seconds to SRT time format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"