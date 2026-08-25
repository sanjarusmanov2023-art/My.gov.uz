# Hujjat Generator — shaxsiy PDF generator

O'zbekiston davlat portali (my.gov.uz) uslubidagi hujjatlarni **o'zingizning kiritgan
ma'lumotlaringiz asosida** PDF shaklida generatsiya qiluvchi shaxsiy (private) veb-ilova.

> ⚠️ Huquqiy eslatma: Bu ilova faqat shaxsiy foydalanish uchun. Yaratilgan hujjatlar
> "asl davlat hujjati" emas — ular foydalanuvchi tomonidan to'ldirilgan nusxalar.

## Imkoniyatlar
- 3 ta hujjat turi: QAYD VARAG'I, Ish staji ma'lumotnomasi, Maosh hisoboti
- Til tanlovi: O'zbekcha / Ruscha / Inglizcha
- Har bir PDF'da QR-kod (skan qilganda `/verify?doc=...` sahifasi ochiladi)
- Faqat admin (siz) kira oladi — login talab qilinadi
- Bepul deploy: Render.com (free tier) + o'z domeningiz

## Loyiha tuzilishi
```
app.py            Flask ilova (login, dashboard, generate, verify)
generator.py      PDF yaratish moduli (reportlab + qrcode)
templates/        HTML shablonlar
requirements.txt  Python bog'liqliklari
Procfile          Render uchun ishga tushirish
```

## Lokalda ishga tushirish
```bash
pip install -r requirements.txt
python app.py
# brauzerda: http://localhost:5000
# login: admin / parol: admin123
```

## Render.com ga deploy (bepul)
1. GitHub'ga push qiling.
2. https://render.com → "New Web Service" → GitHub repo ulang.
3. Build: `pip install -r requirements.txt`, Start: `gunicorn app:app`
4. Environment: `ADMIN_PASS` (yangi parol), `SECRET_KEY` ni o'rnating.
5. "Deploy" → tayyor. O'z domeningizni "Settings → Custom Domains" dan ulang.

## Muhim
- `DOCS` xotirasi va `cache/` papkasi vaqtinchalik. Render free instanceni uxlatganda
  tozalanadi — doimiy saqlash uchun keyinroq SQLite ga o'tkazish mumkin.
- Admin parolni albatta o'zgartiring (`ADMIN_PASS` env yoki kod ichida).
