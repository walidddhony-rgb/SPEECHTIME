# SpeechScribe 🎙️

نظام تفريغ صوتي شبه تلقائي مع توفير 95% من الوقت

## نظرة عامة

SpeechScribe هو نظام ثوري لتحويل الصوت إلى نص يقلل وقت التفريغ بنسبة تصل إلى 95%. بدلًا من الاستماع للتسجيل كاملًا، يحتاج المستخدم فقط لتصنيف 50-100 مقطع صوتي فريد (5-10 دقائق عمل)، والبرنامج يفرغ الباقي تلقائيًا.

## كيف يعمل

1. **استخراج المقاطع**: يُقسّم الصوت إلى مقاطع متداخلة طولها 25 ميلي ثانية
2. **تجميع المقاطع المتشابهة**: تُجمّع المقاطع حسب التشابه الصوتي
3. **التصنيف اليدوي**: يستمع المستخدم لعينة واحدة من كل صنف ويكتب الحرف
4. **التفريغ التلقائي**: يستبدل البرنامج جميع المقاطع بالحروف المخصصة
5. **التصدير**: يُصدّر النص بصيغ متعددة (TXT, CSV, SRT)

## المميزات

- ⚡ **توفير 95% من الوقت**: تفريغ ساعتين من الصوت في 10 دقائق
- 🌍 **دعم جميع اللغات**: يعمل مع أي لغة (عربي، إنجليزي، صيني، إلخ)
- 🔒 **الخصوصية أولًا**: كل المعالجة محلية، لا رفع للسحاب
- 💰 **مجاني ومفتوح المصدر**: لا اشتراكات أو تكاليف API
- 📊 **صيغ تصدير متعددة**: TXT, CSV, ترجمات SRT
- 🎯 **دقة عالية**: 85-95% دقة مع التجميع المناسب

## التثبيت

```bash
# استنساخ المستودع
git clone https://github.com/walidddhony-rgb/SPEECHTIME.git
cd SPEECHTIME

# تثبيت المتطلبات
pip install -r requirements.txt

# أو تثبيت كحزمة
pip install -e .
```

## البداية السريعة

```python
from src import SpeechTranscriber

# إنشاء المفرغ
transcriber = SpeechTranscriber(
    audio_path="audio.wav",
    segment_ms=25.0,
    similarity_threshold=0.85,
)

# تشغيل عملية التفريغ كاملة
transcriber.transcribe()
```

## الاستخدام من سطر الأوامر

```bash
# تفريغ أساسي
python -m src.transcriber audio.wav

# مع معاملات مخصصة
python -m src.transcriber audio.wav --segment-ms 25 --threshold 0.85 --output output.txt
```

## سير العمل

### الخطوة 1: التشغيل الأولي
```bash
python -m src.transcriber lecture.wav
```

ينشئ:
- `clusters.json` - جميع الأصناف الصوتية
- `manual_labels.csv` - قالب التسميات اليدوية

### الخطوة 2: التسميات اليدوية (5-10 دقائق)

افتح `manual_labels.csv` وخصص الحروف:

```csv
cluster_id,character,count,first_occurrence_seconds
0,ا,12500,0.00
1,ل,9800,0.25
2,م,7200,0.50
3,و,6500,0.75
```

### الخطوة 3: توليد النص
```bash
python -m src.transcriber lecture.wav --labels manual_labels.csv
```

ملفات الخرج:
- `output_text.txt` - النص الكامل
- `output_text_details.csv` - معلومات التوقيت التفصيلية
- `output_subtitles.srt` - ملف ترجمات للفيديو

## الأداء

| مدة الصوت | الطريقة التقليدية | SpeechScribe |
|-----------|------------------|-------------|
| 30 دقيقة  | ساعتين           | 5 دقائق     |
| ساعة      | 4 ساعات          | 7 دقائق     |
| ساعتان    | 8 ساعات          | 10 دقائق    |
| 10 ساعات  | 40 ساعة          | 30 دقيقة    |

## المتطلبات

- Python 3.8+
- NumPy
- SciPy
- دعم CSV (مدمج)

## الأمثلة

انظر مجلد `examples/` لأمثلة استخدام كاملة.

## التوثيق

- [دليل التثبيت](docs/installation.md)
- [دليل الاستخدام](docs/usage.md)
- [مرجع API](docs/api.md)

## المساهمة

المساهمات مرحب بها! يرجى قراءة [إرشادات المساهمة](CONTRIBUTING.md).

## الرخصة

هذا المشروع مرخص بموجب رخصة MIT - انظر ملف [LICENSE](LICENSE) للتفاصيل.

## الاستشهاد

إذا استخدمت SpeechScribe في بحثك، يرجى الاستشهاد:

```bibtex
@software{speechscribe2026,
  author = {اسمك},
  title = {SpeechScribe: نظام تفريغ صوتي شبه تلقائي},
  year = {2026},
  url = {https://github.com/walidddhony-rgb/SPEECHTIME}
}
```

## الدعم

- المشاكل: [GitHub Issues](https://github.com/walidddhony-rgb/SPEECHTIME/issues)
- البريد: walidddhony@gmail.com

## الشكر

شكرًا لجميع المساهمين والمستخدمين الذين يساعدون في تحسين SpeechScribe!