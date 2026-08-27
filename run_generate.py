#!/usr/bin/env python3
"""
SpeechScribe - Generate Text from Labels.
Usage: python run_generate.py
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from hybrid_transcriber_masked import HybridTranscriberMasked


def main():
    """Main entry point."""
    print("="*60)
    print("🎙️ SpeechScribe - Generate Text")
    print("="*60)
    
    # Check if files exist
    if not Path('clusters.json').exists():
        print("\n❌ Error: 'clusters.json' not found!")
        print("   Run 'python run_hybrid.py <audio_file.wav>' first.")
        sys.exit(1)
    
    if not Path('manual_labels.csv').exists():
        print("\n❌ Error: 'manual_labels.csv' not found!")
        print("   Please label the clusters first.")
        sys.exit(1)
    
    try:
        # Create dummy transcriber
        transcriber = HybridTranscriberMasked()
        
        # Load clusters from JSON
        with open('clusters.json', 'r', encoding='utf-8-sig') as f:
            clusters_data = json.load(f)
        
        # Reconstruct minimal clusters
        transcriber.clusters = []
        for cluster_data in clusters_data:
            cluster = {
                'id': cluster_data['id'],
                'count': cluster_data['count'],
                'representative': {
                    'start_seconds': cluster_data['representative']['start_seconds'],
                    'end_seconds': cluster_data['representative']['end_seconds'],
                },
                'segments': [
                    {
                        'index': i,
                        'start': int(seg['start_seconds'] * 16000),
                        'end': int(seg['end_seconds'] * 16000),
                        'start_seconds': seg['start_seconds'],
                        'end_seconds': seg['end_seconds'],
                    }
                    for i, seg in enumerate(cluster_data['segments'])
                ],
            }
            transcriber.clusters.append(cluster)
        
        print(f"Loaded {len(transcriber.clusters)} clusters")
        
        # Load labels
        transcriber.load_manual_labels('manual_labels.csv')
        
        # Generate text
        transcriber.generate_text()
        
        # Save results
        transcriber.save_text(
            output_txt='output_text.txt',
            output_csv='output_text_details.csv',
            output_srt='output_subtitles.srt',
        )
        
        print("\n" + "="*60)
        print("✅ Text Generation Complete!")
        print("="*60)
        print("\n📄 Output Files:")
        print("  - output_text.txt (transcribed text)")
        print("  - output_text_details.csv (detailed info)")
        print("  - output_subtitles.srt (subtitles)")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()