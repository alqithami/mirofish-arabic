<div align="center">

<img src="./static/image/MiroFish_logo_compressed.jpeg" alt="MiroFish Logo" width="75%"/>

<a href="https://trendshift.io/repositories/16144" target="_blank"><img src="https://trendshift.io/api/badge/repositories/16144" alt="666ghj%2FMiroFish | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

محرك ذكاء جماعي بسيط ومرن لتوقّع أي شيء
</br>
<em>A Simple and Universal Swarm Intelligence Engine, Predicting Anything</em>

<a href="https://www.shanda.com/" target="_blank"><img src="./static/image/shanda_logo.png" alt="666ghj%2MiroFish | Shanda" height="40"/></a>

[![GitHub Stars](https://img.shields.io/github/stars/666ghj/MiroFish?style=flat-square&color=DAA520)](https://github.com/666ghj/MiroFish/stargazers)
[![GitHub Watchers](https://img.shields.io/github/watchers/666ghj/MiroFish?style=flat-square)](https://github.com/666ghj/MiroFish/watchers)
[![GitHub Forks](https://img.shields.io/github/forks/666ghj/MiroFish?style=flat-square)](https://github.com/666ghj/MiroFish/network)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/666ghj/MiroFish)

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.com/channels/1469200078932545606/1469201282077163739)
[![X](https://img.shields.io/badge/X-Follow-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/mirofish_ai)
[![Instagram](https://img.shields.io/badge/Instagram-Follow-E4405F?style=flat-square&logo=instagram&logoColor=white)](https://www.instagram.com/mirofish_ai/)

[العربية](./README.md) | [English](./README-EN.md) | [中文文档](./README-ZH.md)

</div>

## ⚡ نظرة عامة

**MiroFish** هو محرك تنبؤ قائم على الذكاء الاصطناعي متعدد الوكلاء. يستخرج بذور المعلومات من العالم الواقعي — مثل الأخبار العاجلة، مسودات السياسات، أو الإشارات المالية — ثم يبني عالماً رقمياً موازياً عالي الدقة. داخل هذا العالم تتفاعل آلاف الشخصيات الذكية ذات الذاكرة طويلة المدى والسلوك المستقل والتفضيلات المختلفة لتوليد تطور اجتماعي يمكن مراقبته وتحليله.

الفكرة الأساسية بسيطة:

> أنت ترفع المواد الأولية وتكتب متطلب التنبؤ بلغتك الطبيعية.</br>
> MiroFish يعيد لك تقريراً تنبؤياً مفصلاً وعالماً رقمياً تفاعلياً يمكن استكشافه بعمق.

### الرؤية

يهدف MiroFish إلى بناء مرآة ذكاء جماعي تعكس الواقع. بدلاً من الاكتفاء بالتحليل الوصفي، يسمح لك النظام بتجريب المتغيرات داخل بيئة محاكاة ومراقبة النتائج الناشئة من تفاعل الأفراد والجماعات.

- على المستوى الكلي: مختبر تمهيدي لصناع القرار لاختبار السياسات والرأي العام دون مخاطرة مباشرة.
- على المستوى الفردي: صندوق رمل إبداعي لاستكشاف سيناريوهات خيالية أو استنتاج نهايات الروايات أو تصميم تجارب اجتماعية غير تقليدية.

## 🔄 سير العمل

1. **بناء الرسم المعرفي**: استخراج البذور، حقن الذاكرة الفردية والجماعية، وبناء GraphRAG.
2. **إعداد البيئة**: استخراج الكيانات والعلاقات، توليد الشخصيات، وحقن إعدادات الوكلاء.
3. **المحاكاة**: تشغيل محاكاة متوازية على منصتين، تحليل متطلبات التنبؤ، وتحديث الذاكرة الزمنية ديناميكياً.
4. **توليد التقرير**: استخدام ReportAgent مع مجموعة أدوات تحليلية للتفاعل مع عالم ما بعد المحاكاة.
5. **التفاعل العميق**: الدردشة مع أي وكيل داخل العالم المحاكى أو مع ReportAgent نفسه.

## 🌐 النسخة التجريبية المباشرة

يمكنك تجربة العرض الحي للمشروع عبر الصفحة التجريبية:

[mirofish-live-demo](https://666ghj.github.io/mirofish-demo/)

## 🚀 البدء السريع

### الخيار الأول: التشغيل من الكود المصدري

#### المتطلبات

| الأداة | الإصدار | الوصف | التحقق |
|------|---------|-------------|--------|
| **Node.js** | 18+ | تشغيل الواجهة الأمامية ويشمل npm | `node -v` |
| **Python** | ≥3.11 و ≤3.12 | تشغيل الواجهة الخلفية | `python --version` |
| **uv** | أحدث إصدار | مدير حزم Python | `uv --version` |

### 1) إعداد متغيرات البيئة

```bash
cp .env.example .env
```

ثم افتح ملف `.env` وأدخل المفاتيح المطلوبة.

#### المتغيرات الأساسية

```env
# إعدادات واجهة LLM (أي مزود متوافق مع OpenAI SDK)
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# إعدادات Zep Cloud
ZEP_API_KEY=your_zep_api_key
```

### 2) تثبيت التبعيات

```bash
# تثبيت كل التبعيات مرة واحدة (الجذر + الواجهة + الخلفية)
npm run setup:all
```

أو خطوة بخطوة:

```bash
# تثبيت تبعيات Node (الجذر + الواجهة)
npm run setup

# تثبيت تبعيات Python للواجهة الخلفية
npm run setup:backend
```

### 3) تشغيل الخدمات

```bash
# تشغيل الواجهة الأمامية والخلفية معاً من جذر المشروع
npm run dev
```

#### العناوين الافتراضية

- الواجهة الأمامية: `http://localhost:3000`
- واجهة API الخلفية: `http://localhost:5001`

يمكنك أيضاً تشغيل كل خدمة على حدة:

```bash
npm run backend   # تشغيل الخلفية فقط
npm run frontend  # تشغيل الواجهة فقط
```

## 🐳 الخيار الثاني: التشغيل عبر Docker

```bash
# 1) إعداد ملف البيئة
cp .env.example .env

# 2) تشغيل الخدمات
docker compose up -d
```

يقرأ Docker ملف `.env` من جذر المشروع ويستخدم المنافذ `3000` للواجهة الأمامية و`5001` للواجهة الخلفية.

## 🌍 ملاحظات خاصة بالنسخة العربية

هذا الفرع العربي يضيف أساساً عملياً للتعريب، لكنه لا يقتصر على ترجمة النصوص فقط. الهدف هو جعل الواجهة والتقارير وسلوك النظام أقرب إلى تجربة عربية حقيقية:

- دعم الواجهة العربية واتجاه **RTL**.
- تمرير اللغة إلى الخلفية عبر `Accept-Language`.
- جعل تقرير Step 4 أقل اعتماداً على النصوص الصينية الخام وأكثر اعتماداً على البيانات المنظمة.
- تمهيد الطريق لتقارير ومقابلات ومخرجات عربية أصلية بدلاً من مجرد واجهة مترجمة.

إذا كنت تعمل على فرع عربي مخصص، فالأولوية التالية تكون عادةً:

1. جعل مخرجات الأدوات الخلفية منظمة بالكامل JSON.
2. إنهاء تعريب جميع شاشات الواجهة المتبقية.
3. تعريب المطالبات الخلفية والتقارير والمقابلات بشكل شامل.
4. تحسين الإنتاجية والأمان قبل النشر العام.

## 🙌 المساهمات

إذا كنت تبني نسخة عربية أو محلية مخصصة، فمن الأفضل تنفيذ العمل على مراحل صغيرة:

- أولاً: تعريب الواجهة السطحية.
- ثانياً: تمرير اللغة إلى الواجهة الخلفية.
- ثالثاً: تحويل العقود الهشة المعتمدة على regex إلى JSON منظم.
- رابعاً: تحسين الوثائق، الاختبارات، والإعدادات الإنتاجية.

## 📄 الشكر والتقدير

حصل **MiroFish** على دعم استراتيجي واحتضان من **Shanda Group**.

كما يعتمد محرك المحاكاة على مشروع **[OASIS (Open Agent Social Interaction Simulations)](https://github.com/camel-ai/oasis)**، مع خالص الشكر لفريق CAMEL-AI على مساهماتهم مفتوحة المصدر.
