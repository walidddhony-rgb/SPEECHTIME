"""
إنشاء ملف صوتي تجريبي لاختبار SpeechScribe.
"""

import numpy as np
from scipy.io import wavfile

def create_test_audio(
    filename="c:/test_audio.wav",
    duration=5.0,
    sample_rate=16000,
):
    """
    إنشاء ملف WAV تجريبي.
    
    Args:
        filename: اسم الملف
        duration: المدة بالثواني
        sample_rate: معدل العينة
    """
    print(f"Creating {duration}s audio file at {sample_rate}Hz...")
    
    # إنشاء مصفوفة زمنية
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # إنشاء نغمات متعددة (محاكاة أصوات مختلفة)
    audio = np.zeros_like(t)
    
    # نغمة 440 Hz (A4)
    audio += 0.5 * np.sin(2 * np.pi * 440 * t)
    
    # نغمة 880 Hz (A5)
    audio += 0.3 * np.sin(2 * np.pi * 880 * t)
    
    # نغمة 220 Hz (A3)
    audio += 0.2 * np.sin(2 * np.pi * 220 * t)
    
    # إضافة بعض الضوضاء البيضاء
    noise = np.random.normal(0, 0.05, len(t))
    audio += noise
    
    # تطبيع السعة
    audio = audio / np.max(np.abs(audio))
    
    # تحويل إلى int16
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # حفظ الملف
    wavfile.write(filename, sample_rate, audio_int16)
    
    print(f"✅ Created: {filename}")
    print(f"   Duration: {duration}s")
    print(f"   Sample rate: {sample_rate}Hz")
    print(f"   Samples: {len(audio_int16)}")
    
    return filename


if __name__ == "__main__":
    # إنشاء ملف 5 ثواني
    create_test_audio("c:/test_audio.wav", duration=5.0)
    
    # إنشاء ملف 10 ثواني
    create_test_audio("c:/test_audio_long.wav", duration=10.0)
    
    print("\n✅ Test audio files created successfully!")
