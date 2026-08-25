"""
Absolute-positioning PDF generator — pixel-perfect replica of my.gov.uz docs.
All coordinates in mm (reportlab origin bottom-left). Sizes in pt.
"""
import os, io, random, string, datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import black, grey
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE = os.path.dirname(os.path.abspath(__file__))
FONT = 'Helvetica'
_report = os.path.join(BASE, 'assets', 'arial.ttf')
_reportb = os.path.join(BASE, 'assets', 'arialbd.ttf')
if os.path.exists(_report):
    try:
        pdfmetrics.registerFont(TTFont('UZ', _report))
        pdfmetrics.registerFont(TTFont('UZ-Bold', _reportb))
        FONT = 'UZ'
        FONT_BOLD = 'UZ-Bold'
    except Exception:
        FONT = 'Helvetica'; FONT_BOLD = 'Helvetica-Bold'
else:
    FONT = 'Helvetica'; FONT_BOLD = 'Helvetica-Bold'

QR_BASE_URL = 'https://my-gov-uz-cfuz.onrender.com/verify?doc='
def set_qr_base_url(u):
    global QR_BASE_URL
    QR_BASE_URL = u

import qrcode
from reportlab.platypus import HRFlowable
from reportlab.lib.utils import ImageReader

def gen_doc_number():
    return '-'.join(''.join(random.choices(string.hexdigits[:6].lower(), k=4)) for _ in range(6))

def make_qr(docno):
    url = QR_BASE_URL + docno
    qr = qrcode.QRCode(box_size=6, border=1)
    qr.add_data(url)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
    return buf

def _draw_header(c, now, ministry_lines, logo_path, emblem_path):
    """Draw header: logo left (~15,272), emblem center (~90,268), ministry right (~135,266)."""
    # logo
    if logo_path and os.path.exists(logo_path):
        c.drawImage(logo_path, 15*mm, 272*mm, width=40*mm, height=11*mm, preserveAspectRatio=True)
    # emblem
    if emblem_path and os.path.exists(emblem_path):
        c.drawImage(emblem_path, 88*mm, 266*mm, width=24*mm, height=24*mm, preserveAspectRatio=True)
    # ministry (right, multiple lines)
    c.setFont(FONT, 10.5)
    c.setFillColor(black)
    y = 266*mm
    for line in ministry_lines:
        c.drawRightString(180*mm, y, line)
        y -= 4.6*mm
    # timestamp top-right edge
    if now:
        c.setFont(FONT, 8)
        c.drawRightString(195*mm, 287*mm, now)
    # separator line
    c.setStrokeColor(grey); c.setLineWidth(0.6)
    c.line(15*mm, 262*mm, 195*mm, 262*mm)

def _legal(c, lang, y_top):
    if lang == 'ru':
        txt = ("Настоящий документ является копией электронного документа, сформированного на Едином портале "
               "интерактивных государственных услуг в соответствии с Постановлением Кабинета Министров № 728 от "
               "15 сентября 2017 года. Подлинность документа можно проверить, введя уникальный номер документа "
               "на сайте repo.gov.uz или просканировав QR-код с помощью мобильного телефона.")
    elif lang == 'en':
        txt = ("This document is a copy of an electronic document generated on the Single Portal of Interactive Public "
               "Services pursuant to Resolution of the Cabinet of Ministers No. 728 of September 15, 2017. The "
               "authenticity of the document can be verified by entering the unique document number on repo.gov.uz "
               "or by scanning the QR code with a mobile phone.")
    else:
        txt = ("Ushbu hujjat Yagona interaktiv davlat xizmatlari portali (my.gov.uz)da 2017-yil 15-sentabrdagi "
               "Vazirlar Mahkamasining 728-son qaroriga muvofiq shakllantirilgan elektron hujjatning nusxasi bo‘lib, "
               "davlat organlari tomonidan ushbu hujjatni qabul qilishni rad etishlari qat‘iyan taqiqlanadi. "
               "Hujjat haqiqiyligini repo.gov.uz veb-saytida hujjatning noyob raqamini kiritib yoki mobil "
               "telefon yordamida QR-kodni skaner qilish orqali tekshirish mumkin.")
    c.setFont(FONT, 7); c.setFillColor(black)
    # wrap text
    from reportlab.lib.utils import simpleSplit
    lines = simpleSplit(txt, FONT, 7, 180*mm)
    y = y_top
    for ln in lines:
        c.drawString(15*mm, y, ln)
        y -= 3.2*mm

# ===================== STUDENT (absolute) =====================
def generate_student(data, lang='uz'):
    docno = data.get('doc_no') or gen_doc_number()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    created = data.get('created') or datetime.datetime.now().strftime('%Y-%m-%d')
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W,H = A4
    logo = os.path.join(BASE,'assets','logo.png'); emb = os.path.join(BASE,'assets','emblem.png')
    min_uz = ["O'zbekiston Respublikasi","Oliy ta'lim, fan va","innovatsiyalar vazirligi"]
    min_ru = ["Республика Узбекистан","Министерство высшего образования,","науки и инноваций"]
    min_en = ["Republic of Uzbekistan","Ministry of Higher Education,","Science and Innovation"]
    ministry = {'uz':min_uz,'ru':min_ru,'en':min_en}[lang]
    _draw_header(c, now, ministry, logo, emb)
    # metadata block (left col x=15.8, right col x=119.5)
    c.setFont(FONT, 10.5)
    c.drawString(15.8*mm, 229*mm, "№ "+docno)
    c.drawString(15.8*mm, 224.6*mm, "Hujjat yaratilgan sana: "+created)
    c.drawString(15.8*mm, 220.2*mm, "Ariza raqami: "+(data.get('app_no') or ''))
    c.drawString(119.5*mm, 229*mm, "Hujjat berilgan: "+(data.get('fio') or ''))
    c.drawString(167.0*mm, 224.6*mm, (data.get('fio') or '').split(' ')[-1] if data.get('fio') else '')
    c.drawString(148.3*mm, 220.2*mm, "JShShIR: "+(data.get('pinfl') or ''))
    # title
    c.setFont(FONT_BOLD if False else FONT, 10.5)
    c.drawCentredString(105*mm, 206.7*mm, "O'QISH JOYIDAN MA'LUMOTNOMA")
    c.drawCentredString(105*mm, 201.5*mm, "СПРАВКА С МЕСТА УЧЕБЫ")
    # table rows
    rows = [
        ("F.I.O. / Ф.И.О.:", data.get('fio','')),
        ("JSH ShIR / ПИН ФЛ:", data.get('pinfl','')),
        ("Tug'ilgan sanasi / Дата рождения:", data.get('birth','')),
        ("Fuqaroligi / Гражданство:", data.get('citizenship','')),
        ("Ta'lim turi / Тип образования:", data.get('edu_type','')),
        ("Ta'lim shakli / Форма обучения:", data.get('edu_form','')),
        ("Qabul turi / Тип приема:", data.get('admission','')),
        ("O'qishga kirgan yili / Год зачисления:", data.get('enroll_year','')),
        ("Oliy ta'lim muassasasi / Высшее учебное заведение:", data.get('university','')),
        ("Fakultet / Факультет:", data.get('faculty','')),
        ("Yo'nalish / Направление:", data.get('direction','')),
        ("O'quv kursi / Учебный курс:", data.get('course','')),
    ]
    y = 184.6*mm
    for lab,val in rows:
        c.drawString(16.6*mm, y, lab)
        c.drawString(106.5*mm, y, str(val))
        y -= 7.3*mm
    # note line
    c.drawString(15*mm, 193.6*mm, "Ma'lumot so'ralgan joyga taqdim etish uchun berildi.")
    # footer on page 2
    c.showPage()
    _draw_footer_page(c, docno, lang, now, ministry, logo, emb)
    c.save()
    buf.seek(0); return buf.getvalue(), docno

def _draw_footer_page(c, docno, lang, now, ministry, logo, emb, y_start=None):
    _draw_header(c, now, ministry, logo, emb)
    # large code left
    c.setFont(FONT_BOLD, 28)
    code_y = y_start if y_start else 40*mm
    c.drawString(15*mm, code_y, docno[-4:])
    # QR right
    qr = make_qr(docno)
    qr_y = code_y - 2*mm
    c.drawImage(ImageReader(qr), 150*mm, qr_y, width=30*mm, height=30*mm)
    # legal
    _legal(c, lang, code_y - 15*mm)

def generate_qaydvarag(data, lang='uz'):
    docno = data.get('doc_no') or gen_doc_number()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    created = data.get('created') or datetime.datetime.now().strftime('%Y-%m-%d')
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    logo = os.path.join(BASE,'assets','logo.png'); emb = os.path.join(BASE,'assets','emblem.png')
    ministry = ["O'zbekiston Respublikasi","Adliya vazirligi","Davlat xizmatlari","departamenti"]
    _draw_header(c, now, ministry, logo, emb)
    c.setFont(FONT, 10.5)
    c.drawString(15.8*mm, 233.5*mm, "№ "+docno)
    c.drawString(15.8*mm, 229.0*mm, "Hujjat yaratilgan sana: "+created)
    c.drawString(15.8*mm, 224.6*mm, "Ariza raqami: "+(data.get('app_no') or ''))
    c.drawString(106.3*mm, 231.3*mm, "Hujjat berilgan: "+(data.get('issued_to') or data.get('head_name','')))
    c.drawString(148.3*mm, 226.8*mm, "JShShIR: "+(data.get('pinfl') or data.get('head_stir','')))
    # subtitle
    c.drawString(16.6*mm, 211.1*mm, "Yuridik shaxslar va tadbirkorlik sub'ektlari")
    c.drawString(16.6*mm, 206.5*mm, "ro'yxatidan o'tkazish to'g'risida")
    c.drawCentredString(105*mm, 205.9*mm, "QAYD VARAG'I")
    # section
    c.drawCentredString(105*mm, 189.0*mm, "Umumiy ma'lumot")
    rows = [
        ("STIR", data.get('stir','')),
        ("Ro'yxatga olingan sana", data.get('reg_date','')),
        ("Ro'yxatdan o'tkazilgan raqami", data.get('reg_no','')),
        ("Yuridik shaxsning nomi", data.get('entity_name','')),
        ("Tashkiliy-huquqiy shakl", data.get('org_form','')),
        ("Mulkchilik shakli", data.get('own_form','')),
        ("Faoliyat turi", data.get('activity','')),
        ("Davlat va xo'jalik boshqaruv organining nomi", data.get('gov_body','') or '—'),
        ("Yuridik shaxs turi", data.get('entity_type','')),
        ("Ustav fondi", data.get('charter_capital','')),
    ]
    y = 181.7*mm
    for lab,val in rows:
        c.drawString(16.6*mm, y, lab)
        c.drawString(106.5*mm, y, str(val))
        y -= 7.3*mm
    c.drawCentredString(105*mm, 99.2*mm, "Boshqaruvchi haqida ma'lumot")
    # head rows
    c.drawString(16.6*mm, 91.8*mm, "Rahbarning F.I.O.")
    c.drawString(106.5*mm, 91.8*mm, data.get('head_name',''))
    c.drawString(16.6*mm, 84.5*mm, "Rahbarning STIR")
    c.drawString(106.5*mm, 84.5*mm, data.get('head_stir',''))
    # contact section
    c.drawCentredString(105*mm, 77.1*mm, "Kontakt ma'lumotlari")
    c.drawString(16.6*mm, 69.7*mm, "Elektron pochta manzili")
    c.drawString(106.5*mm, 69.7*mm, data.get('email',''))
    c.drawString(16.6*mm, 62.4*mm, "Telefon")
    c.drawString(106.5*mm, 62.4*mm, data.get('phone',''))
    c.drawString(16.6*mm, 55.0*mm, "Tuman")
    c.drawString(106.5*mm, 55.0*mm, data.get('district',''))
    c.drawString(16.6*mm, 47.7*mm, "Manzil")
    c.drawString(106.5*mm, 47.7*mm, data.get('address',''))
    # footer p2
    c.showPage()
    _draw_footer_page(c, docno, lang, now, ministry, logo, emb)
    c.save()
    buf.seek(0); return buf.getvalue(), docno

def generate_salary(data, lang='en'):
    docno = data.get('doc_no') or gen_doc_number()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    created = data.get('created') or datetime.datetime.now().strftime('%Y-%m-%d')
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    logo = os.path.join(BASE,'assets','logo.png'); emb = os.path.join(BASE,'assets','emblem.png')
    ministry = ["Single Portal of","Interactive","Public Services","The State Tax Committee","of the Republic of Uzbekistan"]
    _draw_header(c, now, ministry, logo, emb)
    c.setFont(FONT, 10.5)
    c.drawString(15.8*mm, 229.0*mm, "№ "+docno)
    c.drawString(15.8*mm, 224.6*mm, "Document creation date: "+created)
    c.drawString(15.8*mm, 220.2*mm, "Application number: "+(data.get('app_no') or ''))
    c.drawString(117.1*mm, 229.0*mm, "Document issued: "+(data.get('issued_to') or ''))
    c.drawString(171.3*mm, 224.6*mm, (data.get('issued_to') or '').split(' ')[-1] if data.get('issued_to') else '')
    c.drawString(151.3*mm, 220.2*mm, "PINFL: "+(data.get('pinfl') or ''))
    c.drawCentredString(105*mm, 206.7*mm, "CERTIFICATE OF CALCULATED WAGES")
    c.drawString(15.0*mm, 191.0*mm, "Name: "+(data.get('issued_to') or ''))
    c.drawString(15.0*mm, 185.8*mm, "PRSA: "+(data.get('pinfl') or '')+"  Total amount of other income: "+(data.get('other_income') or '0'))
    c.drawString(15.0*mm, 170.2*mm, "Issued in that the above person has received the following income:")
    c.drawString(15.0*mm, 162.3*mm, "Total estimated salary: "+(data.get('total_salary') or ''))
    c.drawString(15.0*mm, 152.0*mm, "Income tax: "+(data.get('income_tax') or ''))
    # page 2: table
    c.showPage()
    _draw_header(c, now, ministry, logo, emb)
    # table header
    c.setFont(FONT, 10.5)
    hdrs = ["Year","Month","Enterprise (Organization)","Accrued wage (UZS)","Personal Income Tax (PIT)","Other income","INPS"]
    xs = [17.0, 29.2, 55.2, 120.0, 150.0, 172.0, 182.0]
    y = 121.7*mm
    for h,xc in zip(hdrs, xs):
        c.drawString(xc*mm, y, h)
    y -= 7.3*mm
    for r in data.get('salary_rows', []):
        c.drawString(17.0*mm, y, str(r.get('year','')))
        c.drawString(29.2*mm, y, r.get('month',''))
        c.drawString(55.2*mm, y, r.get('org',''))
        c.drawString(120.0*mm, y, str(r.get('wage','')))
        c.drawString(150.0*mm, y, str(r.get('pit','')))
        c.drawString(172.0*mm, y, str(r.get('other','')))
        c.drawString(182.0*mm, y, str(r.get('inps','')))
        y -= 7.3*mm
    # footer on same page 2 (below table)
    _draw_footer_page(c, docno, lang, now, ministry, logo, emb, y_start=y-10*mm)
    c.save()
    buf.seek(0); return buf.getvalue(), docno

def generate_employment(data, lang='uz'):
    docno = data.get('doc_no') or gen_doc_number()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    created = data.get('created') or datetime.datetime.now().strftime('%Y-%m-%d')
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    logo = os.path.join(BASE,'assets','logo.png'); emb = os.path.join(BASE,'assets','emblem.png')
    ministry = ["O'zbekiston Respublikasi","Bandlik va kambag'allikni","qisqartirish vazirligi"]
    _draw_header(c, now, ministry, logo, emb)
    c.setFont(FONT, 10.5)
    c.drawString(15.8*mm, 229.0*mm, "№ "+docno)
    c.drawString(15.8*mm, 224.6*mm, "Hujjat yaratilgan sana: "+created)
    c.drawString(15.8*mm, 220.2*mm, "Ariza raqami: "+(data.get('app_no') or ''))
    c.drawString(119.5*mm, 229.0*mm, "Hujjat berilgan: "+(data.get('issued_to') or ''))
    c.drawString(148.3*mm, 220.2*mm, "JShShIR: "+(data.get('pinfl') or ''))
    c.drawCentredString(105*mm, 206.7*mm, "Ish staji haqida ma'lumotnoma")
    c.drawString(15.0*mm, 191.0*mm, "Quyidagi shaxs ish staji bo'yicha quyidagi ma'lumotlarga ega:")
    # table
    hdrs = ["№","Boshlanish sanasi","Tugash sanasi","Tashkilot","STIR","Lavozim","Bo'lim"]
    xs = [17.0, 30.0, 55.0, 80.0, 130.0, 150.0, 175.0]
    y = 170*mm
    c.drawString(15.0*mm, y+10*mm, "Ish joylari ro'yxati:")
    for h,xc in zip(hdrs, xs):
        c.drawString(xc*mm, y, h)
    y -= 7.3*mm
    for i,w in enumerate(data.get('works', []), 1):
        c.drawString(17.0*mm, y, str(i))
        c.drawString(30.0*mm, y, w.get('start',''))
        c.drawString(55.0*mm, y, w.get('end',''))
        c.drawString(80.0*mm, y, w.get('org',''))
        c.drawString(130.0*mm, y, w.get('inn',''))
        c.drawString(150.0*mm, y, w.get('position',''))
        c.drawString(175.0*mm, y, w.get('dept',''))
        y -= 7.3*mm
    c.showPage()
    _draw_footer_page(c, docno, lang, now, ministry, logo, emb)
    c.save()
    buf.seek(0); return buf.getvalue(), docno

def generate(doc_type, data, lang='uz'):
    if doc_type == 'student': return generate_student(data, lang)
    if doc_type == 'qaydvarag': return generate_qaydvarag(data, lang)
    if doc_type == 'salary': return generate_salary(data, lang)
    if doc_type == 'employment': return generate_employment(data, lang)
    raise NotImplementedError(doc_type)
