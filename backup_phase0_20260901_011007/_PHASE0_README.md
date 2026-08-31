# حزمة إصلاح المرحلة 0 — SPEECHTIME (SpeechScribe)

**التاريخ:** 2026-09-01 · **الإصدار:** phase0 · **تغلق:** Issue #4

**النطاق:** إصلاح كل روابط المستودع القديم `walidddhony-rgb/SPEECHTIME` لتشير إلى `walidddhony-rgb/SPEECHTIME` + توحيد بيانات المؤلفين في `pyproject.toml` + توسيع `.gitignore` — **دون أي تغيير وظيفي في الكود**.

## محتويات الحزمة

| الملف | الحالة | الإجراء بعد الاستخراج |
|---|---|---|
| `pyproject.toml` | معدَّل (روابط + مؤلفون) | استبدال الموجود |
| `.gitignore` | موسَّع بالكامل | استبدال الموجود |
| `apply_phase0.py` | جديد | تشغيله مرة واحدة من جذر المشروع |
| `_PHASE0_README.md` | هذا الدليل | للقراءة، ثم يمكن حذفه |

> **ملاحظة:** لم تُرفق نسخ معدلة من `README.md` و`README_ar.md` و`CHANGELOG.md` و`CONTRIBUTING.md` عمدًا. السكربت `apply_phase0.py` يصلحها في نسختك المحلية باستبدال نصي جراحي لا يمس أي محتوى آخر، فتحتفظ بكل تنسيقك وشاراتك كما هي.

## خطوات التطبيق بالترتيب

### الخطوة 1 — نقطة أمان قبل البدء
من جذر المشروع:
```powershell
git add -A
git commit -m "chore: snapshot before phase 0 patch"
```
أو أرشف مجلد المشروع يدويًا إلى خارج المستودع.

### الخطوة 2 — الاستخراج
استخرج محتويات الأرشيف **داخل جذر المشروع مباشرة** (بدون مجلد وسيط) ووافق على استبدال `pyproject.toml` و`.gitignore`.

### الخطوة 3 — تشغيل أداة الإصلاح
```powershell
python apply_phase0.py
```
تقوم الأداة تلقائيًا بـ:
- إنشاء نسخة احتياطية كاملة: `backup_phase0_YYYYMMDD_HHMMSS/` (بدون `.git`)
- استبدال كل صيغ الرابط القديم في كل الملفات النصية (md, toml, py, json, ...):
  - `https://github.com/walidddhony-rgb/SPEECHTIME.git` ← `https://github.com/walidddhony-rgb/SPEECHTIME.git`
  - `https://github.com/walidddhony-rgb/SPEECHTIME` ← `https://github.com/walidddhony-rgb/SPEECHTIME`
  - أي إشارة مجردة لـ `walidddhony-rgb/SPEECHTIME` ← `walidddhony-rgb/SPEECHTIME`
  - `cd SPEECHTIME` ← `cd SPEECHTIME` (في تعليمات التثبيت)
- طباعة تقرير مفصل: كل ملف + عدد الاستبدالات
- تحقق نهائي: التأكد أن `slam-prog` لم يبقَ له أثر في أي ملف نصي

المتوقع تقريبًا: 10-20 استبدالًا عبر 2-5 ملفات (README.md وREADME_ar.md وربما CHANGELOG.md وCONTRIBUTING.md وdocs وملفات py). ملف `pyproject.toml` سيُظهر 0 استبدال لأنه مُصلَح مسبقًا في هذه الحزمة — هذا طبيعي.

### الخطوة 4 — الالتزام الأول (الروابط)
```powershell
git add -A
git commit -m "fix: update all repository links to walidddhony-rgb/SPEECHTIME and extend .gitignore (closes #4)"
```
عبارة `(closes #4)` ستغلق القضية تلقائيًا عند الدفع.

### الخطوة 5 — تنظيف الجذر
إزالة مخرجات التشغيل من التتبع (تبقى على قرصك ولن تُرفع مرة أخرى):
```powershell
git rm --cached Voice.wav
git rm --cached output.txt
git rm --cached output-srt.txt
git rm -r --cached results
```

### الخطوة 6 — حذف الملف المكرر بعد فحص الأمان
```powershell
findstr /s /i "transcriber1" *.py
```
إن لم تظهر نتائج سوى `src\transcriber1.py` نفسه:
```powershell
git rm src/transcriber1.py
```

### الخطوة 7 — الالتزام الثاني والوسم والدفع
```powershell
git add -A
git commit -m "chore: untrack runtime outputs and remove duplicate transcriber1.py"
git tag v0.1.0-baseline
git push origin main --tags
```

## قائمة التحقق النهائية
- [ ] `git grep -n "slam-prog"` لا يُرجع أي نتيجة
- [ ] `git status` نظيف بعد الدفع
- [ ] صفحة GitHub تعرض README بالروابط الجديدة (جرّب رابط Issues وكتلة Citation)
- [ ] Issue #4 أُغلقت تلقائيًا
- [ ] `Voice.wav` و`output*.txt` و`results/` لم تعد ظاهرة في المستودع على GitHub

## ما الذي تغير بالضبط في pyproject.toml؟
1. قسم `[project.urls]`: الروابط الخمسة (Homepage, Documentation, Repository, Issues, Changelog) تشير الآن إلى `walidddhony-rgb/SPEECHTIME`.
2. `authors` و`maintainers`: صارت إدخالين منفصلين بالاسمين الكاملين، والبريد `walidddhony@gmail.com` مرتبط باسم صاحبه (WALID) بدلًا من NAJIB — عدّل الترتيب إن رغبت.
3. كل ما عداه (الاعتماديات، الحزم، إعدادات black/isort/mypy) بقي كما هو حرفيًا — راجع الفرق بـ `git diff pyproject.toml`.

## ما الجديد في .gitignore؟
تغطية شاملة: مخرجات بايثون، البيئات الافتراضية، الاختبارات والتغطية، أدوات الفحص، المحررات، ملفات النظام، **كل صيغ الصوت** (wav/mp3/... لن تُتتبع بعد الآن)، مخرجات التشغيل (`output*` و`Export/` و`results/` و`clusters.json` و`manual_labels.csv`)، ملفات نماذج Whisper (pt/bin/onnx/gguf)، والنسخ الاحتياطية والأرشيفات (`backup*/` و`*.zip`).
> لإضافة ملف صوت عينة إجباريًا مستقبلًا: `git add -f examples/sample.wav`

## ملاحظات
- مجلد النسخة الاحتياطية الذي ينشئه السكربت يحتفظ بالروابط القديمة بالتصميم — محلي فقط ومتجاهَل في git.
- أقسام README الحالية مكررة (Contributing/License/Contact مضافة مرتين من القالب) — تُنظف في مرحلة التوثيق (المرحلة 4) وليس الآن، حفاظًا على حد أدنى من التغييرات.
- وصف الحزمة في pyproject ما زال يحمل "Save 95%" — يُحدَّث في المرحلة 2 بعد القياس الفعلي (WER/CER + دراسة الزمن).
- إن كنت تعمل عبر المتصفح فقط حتى الآن، فهذه الحزمة فرصة مثالية للتحول إلى git محلي (clone ← تطبيق الحزمة ← push).

**الخطوة التالية بعد هذه الحزمة:** المرحلة 1 — إضافة CI عبر GitHub Actions وتوسيع الاختبارات، أو إنشاء القضايا العشر المقترحة في المستودع.
