# THRS Recruitment Premium UI V9

تحديث UX/UI لصفحة Recruitment فقط، مبني على الصفحة الحالية في `THRS/main` مع الحفاظ على الـAPI والـbusiness logic كما هي.

## الملفات

- Patch: `THRS_RECRUITMENT_PREMIUM_UI_V9_2026-08-28.patch`
- OpenHands prompt: `OPENHANDS_PROMPT_THRS_RECRUITMENT_PREMIUM_UI_V9_2026-08-28.txt`

## ماذا يغير الـPatch؟

- يضيف import واحد داخل `frontend/src/pages/Recruitment.jsx`.
- يضيف stylesheet مستقل: `frontend/src/styles/thrs-recruitment-v9-premium.css`.
- يعيد تصميم الـRecruitment hero، KPI cards، recruitment pipeline، tabs، filters، applicants/jobs tables، pagination، responsive layout، RTL/LTR، وdark theme بشكل أكثر احترافية وتنظيمًا.
- التعديلات scoped داخل صفحة Recruitment حتى لا تؤثر على باقي THRS.

## ماذا لا يغير؟

لا توجد تغييرات في backend، database، API، routes، authentication، recruitment statuses، filtering logic، pagination logic، candidate/job operations أو أي module آخر.

## طريقة التطبيق الآمنة

من root الخاص بـTHRS:

```bash
git apply --check /path/to/THRS_RECRUITMENT_PREMIUM_UI_V9_2026-08-28.patch
git apply /path/to/THRS_RECRUITMENT_PREMIUM_UI_V9_2026-08-28.patch
cd frontend
npm run build
CI=true npm test -- --watchAll=false --passWithNoTests
```

استخدم ملف OpenHands prompt الموجود بجانب الـPatch للتطبيق على السيرفر مع backup وvalidation وsmoke test، ومن دون commit أو push إلى THRS.
