# -*- coding: utf-8 -*-
"""PDF generator for 4 government-style document types.
Languages: uz / ru / en. Each generated PDF embeds a QR code."""
import io, os, random, string, datetime, glob
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image as RLImage)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode
from PIL import Image as PILImage

BASE = os.path.dirname(os.path.abspath(__file__))

# --- Fonts: load Arial from repo assets (works on local + Render) ---
FONT = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
_arial = os.path.join(BASE, 'assets', 'arial.ttf')
_arial_b = os.path.join(BASE, 'assets', 'arialbd.ttf')
if os.path.exists(_arial):
    try:
        pdfmetrics.registerFont(TTFont('UZ', _arial)); FONT = 'UZ'
        if os.path.exists(_arial_b):
            pdfmetrics.registerFont(TTFont('UZ-Bold', _arial_b)); FONT_BOLD = 'UZ-Bold'
    except Exception:
        pass

def _styles():
    ss = getSampleStyleSheet()
    def s(name, **kw):
        kw.setdefault('fontName', FONT)
        return ParagraphStyle(name, parent=ss['Normal'], **kw)
    return {
        'header': s('header', fontSize=8, leading=10, alignment=TA_CENTER),
        'ministry': s('ministry', fontSize=9, leading=11, alignment=TA_CENTER),
        'docno': s('docno', fontSize=8, leading=10),
        'title': s('title', fontSize=13, leading=16, alignment=TA_CENTER),
        'subtitle': s('subtitle', fontSize=10, leading=13, alignment=TA_CENTER),
        'lab': s('lab', fontSize=8.5, leading=11),
        'labb': s('labb', fontSize=8.5, leading=11),
        'val': s('val', fontSize=8.5, leading=11),
        'note': s('note', fontSize=7, leading=9),
        'bigcode': s('bigcode', fontSize=28, leading=30, alignment=TA_LEFT, fontName=FONT_BOLD),
        'sec': s('sec', fontSize=9, leading=12, alignment=TA_CENTER),
    }

# Base URL for QR codes (set per-request from app.py via set_qr_base_url)
QR_BASE_URL = "https://my-gov-uz-cfuz.onrender.com/verify?doc="

def set_qr_base_url(url):
    global QR_BASE_URL
    QR_BASE_URL = url

def make_qr(docno: str) -> RLImage:
    data = QR_BASE_URL + docno
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return RLImage(buf, width=28*mm, height=28*mm)

def _assets():
    base = os.path.join(BASE, 'assets')
    return os.path.join(base, 'logo.png'), os.path.join(base, 'emblem.png')

def make_header(ministry_html, now=None):
    """Returns a Table with: my.gov.uz logo (left) | emblem (center) | ministry name (right).
    Optionally includes timestamp row above and a separator line below."""
    from reportlab.platypus import HRFlowable
    logo_path, emblem_path = _assets()
    logo = RLImage(logo_path, width=34*mm, height=12*mm) if os.path.exists(logo_path) else Spacer(1, 12*mm)
    emb = RLImage(emblem_path, width=18*mm, height=18*mm) if os.path.exists(emblem_path) else Spacer(1, 18*mm)
    mst = _styles()['ministry']
    mpara = Paragraph(ministry_html, mst)
    elems = []
    if now:
        tst = _styles()['header']
        elems.append(Paragraph(now, tst))
        elems.append(HRFlowable(width='100%', thickness=0.6, color=colors.grey, spaceBefore=2, spaceAfter=4))
    header_tbl = Table([[logo, emb, mpara]], colWidths=[40*mm, 22*mm, 100*mm])
    header_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elems.append(header_tbl)
    elems.append(HRFlowable(width='100%', thickness=0.6, color=colors.grey, spaceBefore=4, spaceAfter=6))
    return elems


def gen_doc_number():
    parts = [''.join(random.choices(string.hexdigits[:6].lower(), k=4)) for _ in range(6)]
    return '-'.join(parts)

def _legal_note(lang):
    if lang == 'ru':
        return ("Настоящий документ является копией электронного документа, сформированного на "
                "Едином портале интерактивных государственных услуг в соответствии с Постановлением "
                "Кабинета Министров № 728 от 15 сентября 2017 года. Подлинность документа можно "
                "проверить, введя уникальный номер документа на сайте repo.gov.uz или просканировав "
                "QR-код с помощью мобильного телефона.")
    if lang == 'en':
        return ("This document is a copy of an electronic document generated in accordance with the "
                "provision on the Single Portal of Interactive Public Services, approved by the "
                "Cabinet of Ministers of the Republic of Uzbekistan dated September 15, 2017 No. 728. "
                "To verify the document, enter its unique number on repo.gov.uz or scan the QR code "
                "with a mobile device.")
    return ("Mazkur hujjat Vazirlar Mahkamasining 2017 yil 15 sentyabrdagi 728-son qaroriga muvofiq "
            "Yagona interaktiv davlat xizmatlari portalida shakllantirilgan elektron hujjatning nusxasi. "
            "Haqiqiyligini repo.gov.uz saytida noyob raqamni kiritib yoki QR-kodni skaner qilib tekshirish mumkin.")

# ===================== TYPE 1: QAYD VARAG'I (legal entity) =====================
def generate_qaydvarag(data, lang='uz'):
    st = _styles()
    docno = data.get('doc_no') or gen_doc_number()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    created = data.get('created') or datetime.datetime.now().strftime('%Y-%m-%d')
    T = {
        'uz': dict(ministry="O'zbekiston Respublikasi<br/>Adliya vazirligi<br/>Davlat xizmatlari departamenti",
                   title="QAYD VARAG'I", sub="",
                   hdr=["STIR","Ro'yxatga olingan sana","Ro'yxatdan o'tkazilgan raqami","Yuridik shaxsning nomi",
                        "Tashkiliy-huquqiy shakl","Mulkchilik shakli","Faoliyat turi",
                        "Davlat va xo'jalik boshqaruvi organining nomi","Yuridik shaxs turi","Ustav fondi",
                        "Rahbarning F.I.SH.","Rahbarning STIR","Ta'sischining nomi","Ustav fondi (%)",
                        "Elektron pochta manzili","Telefon","Tuman","Manzil"],
                   sectitle="Umumiy ma'lumot", sec2="Boshqaruvchi haqida ma'lumot",
                   sec3="Ta'sischilar va ularning ustav fondidagi ulushi", sec4="Kontakt ma'lumotlari",
                   issued="Hujjat berilgan:", pinfl="JShShIR:", appno="Ariza raqami:"),
        'ru': dict(ministry="Республика Узбекистан<br/>Министерство юстиции<br/>Департамент государственных услуг",
                   title="РЕГИСТРАЦИОННЫЙ ЛИСТ", sub="",
                   hdr=["ИНН","Дата регистрации","Регистрационный номер","Наименование юр. лица",
                        "Организационно-правовая форма","Форма собственности","Вид деятельности",
                        "Наименование гос. органа","Тип юр. лица","Уставный фонд",
                        "Ф.И.О. руководителя","ИНН руководителя","Наименование учредителя","Уставный фонд (%)",
                        "Эл. почта","Телефон","Район","Адрес"],
                   sectitle="Общая информация", sec2="Сведения о руководителе",
                   sec3="Учредители и их доли в уставном фонде", sec4="Контактные данные",
                   issued="Документ выдан:", pinfl="ПИНФЛ:", appno="Номер заявки:"),
        'en': dict(ministry="Republic of Uzbekistan<br/>Ministry of Justice<br/>Department of Public Services",
                   title="REGISTRATION SHEET", sub="",
                   hdr=["TIN","Date of registration","Registration number","Name of legal entity",
                        "Organizational-legal form","Form of ownership","Type of activity",
                        "Name of state body","Type of legal entity","Charter capital",
                        "Head's full name","Head's TIN","Founder's name","Charter capital (%)",
                        "E-mail","Phone","District","Address"],
                   sectitle="General information", sec2="Information about the head",
                   sec3="Founders and their share in the charter capital", sec4="Contact information",
                   issued="Document issued:", pinfl="PINFL:", appno="Application No:"),
    }[lang]
    d = data
    rows1 = [
        (T['hdr'][0], d.get('stir','')),
        (T['hdr'][1], d.get('reg_date','')),
        (T['hdr'][2], d.get('reg_no','')),
        (T['hdr'][3], d.get('entity_name','')),
        (T['hdr'][4], d.get('org_form','')),
        (T['hdr'][5], d.get('own_form','')),
        (T['hdr'][6], d.get('activity','')),
        (T['hdr'][7], d.get('gov_body','') or '—'),
        (T['hdr'][8], d.get('entity_type','')),
        (T['hdr'][9], d.get('charter_capital','')),
    ]
    rows2 = [(T['hdr'][10], d.get('head_name','')), (T['hdr'][11], d.get('head_stir',''))]
    founders = d.get('founders', []) or [(d.get('head_name',''),'100')]
    rows3 = [(T['hdr'][12], f"{n} — {p}%") for n,p in founders]
    rows4 = [(T['hdr'][14], d.get('email','')), (T['hdr'][15], d.get('phone','')),
             (T['hdr'][16], d.get('district','')), (T['hdr'][17], d.get('address',''))]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=14*mm, bottomMargin=14*mm, title="Qayd varag'i")
    story = []
    story.extend(make_header(T['ministry'], now))
    story.append(Paragraph("№ " + docno, st['docno']))
    story.append(Paragraph(T['appno'] + " " + (d.get('app_no') or ''), st['docno']))
    story.append(Paragraph(T['issued'] + " " + (d.get('issued_to') or d.get('head_name','')), st['docno']))
    story.append(Paragraph(T['pinfl'] + " " + (d.get('pinfl') or d.get('head_stir','')), st['docno']))
    story.append(Spacer(1,6))
    story.append(Paragraph(T['title'], st['title']))
    story.append(Spacer(1,8))
    def block(title, rows):
        story.append(Paragraph(title, st['sec']))
        tdata = [[Paragraph(f"{k}", st['labb']), Paragraph(str(v), st['val'])] for k,v in rows]
        t = Table(tdata, colWidths=[70*mm, 94*mm])
        t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),FONT),('GRID',(0,0),(-1,-1),0.4,colors.lightgrey),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
            ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5)]))
        story.append(t); story.append(Spacer(1,8))
    block(T['sectitle'], rows1)
    block(T['sec2'], rows2)
    block(T['sec3'], rows3)
    block(T['sec4'], rows4)
    story.append(Spacer(1,6))
    qr = make_qr(docno)
    code_para = Paragraph("[" + docno[-4:] + "]", st['note'])
    qr_cell = Table([[qr],[code_para]], colWidths=[28*mm])
    qr_cell.setStyle(TableStyle([('ALIGN',(0,0),(0,0),'CENTER'),('ALIGN',(0,1),(0,1),'CENTER'),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    legal = Paragraph(_legal_note(lang), st['note'])
    ft = Table([[legal, qr_cell]], colWidths=[120*mm, 44*mm])
    ft.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(1,0),(1,0),'RIGHT'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    story.append(ft)
    doc.build(story)
    buf.seek(0)
    return buf.getvalue(), docno

# ===================== TYPE 2: ISH STAJI (employment history) =====================
def generate_employment(data, lang='uz'):
    st = _styles()
    docno = data.get('doc_no') or gen_doc_number()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    created = data.get('created') or datetime.datetime.now().strftime('%Y-%m-%d')
    T = {
        'ru': dict(ministry="Министерство занятости и сокращения бедности<br/>Республики Узбекистан",
                   title="Информация о стаже работы", issued="Документ выдан:", pinfl="ПИНФЛ:",
                   appno="Номер заявки:", cols=["№","Дата начала","Дата окончания","Организация","ИНН","Должность","Отдел"]),
        'uz': dict(ministry="Bandlik va kambag‘allikni qisqartirish<br/>vazirligi<br/>O‘zbekiston Respublikasi",
                   title="Ish staji haqida ma'lumotnoma", issued="Hujjat berilgan:", pinfl="JShShIR:",
                   appno="Ariza raqami:", cols=["№","Boshlanish sanasi","Tugash sanasi","Tashkilot","STIR","Lavozim","Bo‘lim"]),
        'en': dict(ministry="Ministry of Employment and Poverty Reduction<br/>Republic of Uzbekistan",
                   title="Employment History Certificate", issued="Document issued:", pinfl="PINFL:",
                   appno="Application No.:", cols=["#","Start date","End date","Organization","TIN","Position","Dept"]),
    }[lang]
    works = data.get('works', [])
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=14*mm, bottomMargin=14*mm, title="Ish staji")
    story=[]
    story.extend(make_header(T['ministry'], now))
    story.append(Paragraph("№ " + docno, st['docno']))
    story.append(Paragraph(T['appno'] + " " + (data.get('app_no') or ''), st['docno']))
    story.append(Paragraph(T['issued'] + " " + (data.get('issued_to') or ''), st['docno']))
    story.append(Paragraph(T['pinfl'] + " " + (data.get('pinfl') or ''), st['docno']))
    story.append(Spacer(1,6))
    story.append(Paragraph(T['title'], st['title']))
    story.append(Spacer(1,8))
    header = [Paragraph(f"{c}", st['labb']) for c in T['cols']]
    body=[]
    for i,w in enumerate(works,1):
        body.append([Paragraph(str(i),st['val']),Paragraph(w.get('start',''),st['val']),
                     Paragraph(w.get('end',''),st['val']),Paragraph(w.get('org',''),st['val']),
                     Paragraph(w.get('inn',''),st['val']),Paragraph(w.get('position',''),st['val']),
                     Paragraph(w.get('dept',''),st['val'])])
    t=Table([header]+body, colWidths=[8*mm,22*mm,22*mm,40*mm,22*mm,28*mm,22*mm], repeatRows=1)
    t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),FONT),('GRID',(0,0),(-1,-1),0.4,colors.lightgrey),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]))
    story.append(t)
    story.append(Spacer(1,8))
    code_para = Paragraph(docno[-4:], st['bigcode'])
    qr = make_qr(docno)
    ft = Table([[code_para, qr]], colWidths=[44*mm, 44*mm])
    ft.setStyle(TableStyle([('VALIGN',(0,0),(0,0),'MIDDLE'),('ALIGN',(0,0),(0,0),'LEFT'),
        ('VALIGN',(1,0),(1,0),'MIDDLE'),('ALIGN',(1,0),(1,0),'RIGHT'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    legal = Paragraph(_legal_note(lang), st['note'])
    story.append(ft)
    story.append(legal)
    doc.build(story)
    buf.seek(0); return buf.getvalue(), docno

# ===================== TYPE 3: MAOSH HISOBOTI (salary certificate) =====================
def generate_salary(data, lang='en'):
    st = _styles()
    docno = data.get('doc_no') or gen_doc_number()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    created = data.get('created') or datetime.datetime.now().strftime('%Y-%m-%d')
    T = {
        'en': dict(ministry="Single Portal of Interactive Public Services<br/>The State Tax Committee of the Republic of Uzbekistan",
                   title="CERTIFICATE OF CALCULATED WAGES",
                   name="Name:", prsa="PRSA:", intro="Issued in that the above person has received the following income:",
                   total="Total estimated salary:", tax="Income tax:",
                   cols=["Year","Month","Enterprise (Organization)","Accrued wage (UZS)","Personal Income Tax (PIT)","Other income","INPS"]),
        'ru': dict(ministry="Единый портал интерактивных государственных услуг<br/>Государственный налоговый комитет Республики Узбекистан",
                   title="СПРАВКА О НАЧИСЛЕННОЙ ЗАРАБОТНОЙ ПЛАТЕ",
                   name="Имя:", prsa="ПРСА:", intro="Выдано в том, что указанное лицо получило следующий доход:",
                   total="Всего начислено:", tax="Подоходный налог:",
                   cols=["Год","Месяц","Предприятие","Начислено (UZS)","Подоходный налог","Прочий доход","ИНПС"]),
        'uz': dict(ministry="Interaktiv davlat xizmatlari bitim portali<br/>O'zbekiston Respublikasi Davlat soliq qo'mitasi",
                   title="HISOBLANGAN ISH HAQI TO'G'RISIDA MA'LUMOTNOMA",
                   name="F.I.SH.:", prsa="STIR:", intro="Yuqoridagi shaxs quyidagi daromadni olganligi to'g'risida:",
                   total="Jami hisoblangan ish haqi:", tax="Daromad solig'i:",
                   cols=["Yil","Oy","Tashkilot","Hisoblangan ish haqi (UZS)","Daromad solig'i","Boshqa daromad","INPS"]),
    }[lang]
    rows = data.get('salary_rows', [])
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16*mm, rightMargin=16*mm,
                            topMargin=14*mm, bottomMargin=14*mm, title="Salary certificate")
    story=[]
    story.extend(make_header(T['ministry'], now))
    story.append(Paragraph("№ " + docno, st['docno']))
    story.append(Paragraph("Document creation date: " + created, st['docno']))
    story.append(Paragraph("Application number: " + (data.get('app_no') or ''), st['docno']))
    story.append(Paragraph("Document issued: " + (data.get('issued_to') or ''), st['docno']))
    story.append(Paragraph("PINFL: " + (data.get('pinfl') or ''), st['docno']))
    story.append(Spacer(1,8))
    story.append(Paragraph(T['title'], st['title']))
    story.append(Spacer(1,8))
    story.append(Paragraph(T['name'] + " " + (data.get('issued_to') or ''), st['lab']))
    story.append(Paragraph(T['prsa'] + " " + (data.get('pinfl') or ''), st['lab']))
    story.append(Spacer(1,4))
    story.append(Paragraph(T['intro'], st['lab']))
    story.append(Paragraph(f"{T['total']} {data.get('total_salary','')}", st['lab']))
    story.append(Paragraph(f"{T['tax']} {data.get('income_tax','')}", st['lab']))
    story.append(Spacer(1,6))
    header=[Paragraph(f"{c}", st['labb']) for c in T['cols']]
    body=[]
    for r in rows:
        body.append([Paragraph(str(r.get('year','')),st['val']),Paragraph(r.get('month',''),st['val']),
                     Paragraph(r.get('org',''),st['val']),Paragraph(str(r.get('wage','')),st['val']),
                     Paragraph(str(r.get('pit','')),st['val']),Paragraph(str(r.get('other','')),st['val']),
                     Paragraph(str(r.get('inps','')),st['val'])])
    t=Table([header]+body, colWidths=[14*mm,20*mm,46*mm,30*mm,28*mm,22*mm,16*mm], repeatRows=1)
    t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),FONT),('GRID',(0,0),(-1,-1),0.4,colors.lightgrey),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
        ('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]))
    story.append(t)
    story.append(Spacer(1,8))
    code_para = Paragraph(docno[-4:], st['bigcode'])
    qr = make_qr(docno)
    ft = Table([[code_para, qr]], colWidths=[44*mm, 44*mm])
    ft.setStyle(TableStyle([('VALIGN',(0,0),(0,0),'MIDDLE'),('ALIGN',(0,0),(0,0),'LEFT'),
        ('VALIGN',(1,0),(1,0),'MIDDLE'),('ALIGN',(1,0),(1,0),'RIGHT'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    legal = Paragraph(_legal_note(lang), st['note'])
    story.append(ft)
    story.append(legal)
    doc.build(story)
    buf.seek(0); return buf.getvalue(), docno

# ===================== TYPE 4: TALABA MA'LUMOTNOMASI (student certificate) =====================
def generate_student(data, lang='uz'):
    st = _styles()
    docno = data.get('doc_no') or gen_doc_number()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    created = data.get('created') or datetime.datetime.now().strftime('%Y-%m-%d')
    T = {
        'uz': dict(ministry="O'zbekiston Respublikasi<br/>Oliy ta'lim, fan va<br/>innovatsiyalar vazirligi",
                   title="O'QISH JOYIDAN MA'LUMOTNOMA",
                   subtitle="СПРАВКА С МЕСТА УЧЕБЫ",
                   issued="Hujjat berilgan:", pinfl="JShShIR:", appno="Ariza raqami:",
                   rows=[
                       ("F.I.O. / Ф.И.О.", "fio"),
                       ("JSH ShIR / ПИН ФЛ", "pinfl"),
                       ("Tug'ilgan sanasi / Дата рождения", "birth"),
                       ("Fuqaroligi / Гражданство", "citizenship"),
                       ("Ta'lim turi / Тип образования", "edu_type"),
                       ("Ta'lim shakli / Форма обучения", "edu_form"),
                       ("Qabul turi / Тип приема", "admission"),
                       ("O'qishga kirgan yili / Год зачисления", "enroll_year"),
                       ("Oliy ta'lim muassasasi / Высшее учебное заведение", "university"),
                       ("Fakultet / Факультет", "faculty"),
                       ("Yo'nalish / Направление", "direction"),
                       ("O'quv kursi / Курс обучения", "course"),
                   ],
                   note_line="Ma'lumot so'ralgan joyga taqdim etish uchun berildi."),
        'ru': dict(ministry="Республика Узбекистан<br/>Министерство высшего образования,<br/>науки и инноваций",
                   title="СПРАВКА С МЕСТА УЧЕБЫ",
                   subtitle="O'QISH JOYIDAN MA'LUMOTNOMA",
                   issued="Документ выдан:", pinfl="ПИНФЛ:", appno="Номер заявки:",
                   rows=[
                       ("Ф.И.О.", "fio"),
                       ("ПИНФЛ", "pinfl"),
                       ("Дата рождения", "birth"),
                       ("Гражданство", "citizenship"),
                       ("Тип образования", "edu_type"),
                       ("Форма обучения", "edu_form"),
                       ("Тип приема", "admission"),
                       ("Год зачисления", "enroll_year"),
                       ("Высшее учебное заведение", "university"),
                       ("Факультет", "faculty"),
                       ("Направление", "direction"),
                       ("Курс обучения", "course"),
                   ],
                   note_line="Справка выдана для предоставления по месту требования."),
        'en': dict(ministry="Republic of Uzbekistan<br/>Ministry of Higher Education,<br/>Science and Innovation",
                   title="CERTIFICATE FROM PLACE OF STUDY",
                   subtitle="СПРАВКА С МЕСТА УЧЕБЫ",
                   issued="Document issued:", pinfl="PINFL:", appno="Application No.:",
                   rows=[
                       ("Full name", "fio"),
                       ("PINFL", "pinfl"),
                       ("Date of birth", "birth"),
                       ("Citizenship", "citizenship"),
                       ("Type of education", "edu_type"),
                       ("Form of education", "edu_form"),
                       ("Type of admission", "admission"),
                       ("Year of enrollment", "enroll_year"),
                       ("Higher education institution", "university"),
                       ("Faculty", "faculty"),
                       ("Field of study", "direction"),
                       ("Year of study", "course"),
                   ],
                   note_line="Issued for submission to the requesting party."),
    }[lang]
    d = data
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=14*mm, bottomMargin=14*mm, title="Talaba malumotnomasi")
    story = []
    story.extend(make_header(T['ministry'], now))
    meta = Table([[
        Paragraph("№ " + docno + "<br/>" + T['appno'] + " " + (d.get('app_no') or ''), st['docno']),
        Paragraph(T['issued'] + " " + (d.get('fio') or '') + "<br/>" + T['pinfl'] + " " + (d.get('pinfl') or ''), st['docno']),
    ]], colWidths=[92*mm, 92*mm])
    meta.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('ALIGN',(1,0),(1,0),'RIGHT'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    story.append(meta)
    story.append(Spacer(1,10))
    story.append(Paragraph(T['title'], st['title']))
    story.append(Paragraph(T['subtitle'], st['subtitle']))
    story.append(Spacer(1,10))
    tdata = []
    for label, key in T['rows']:
        val = d.get(key, '')
        if key == 'birth' and not val:
            val = d.get('birth_date','')
        tdata.append([Paragraph(f"{label}", st['labb']), Paragraph(str(val), st['val'])])
    t = Table(tdata, colWidths=[95*mm, 69*mm])
    t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),FONT),('GRID',(0,0),(-1,-1),0.4,colors.lightgrey),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6)]))
    story.append(t)
    story.append(Spacer(1,8))
    story.append(Paragraph(T['note_line'], st['note']))
    story.append(Spacer(1,8))
    # code (large) on LEFT, QR on RIGHT — matching original my.gov.uz layout
    code_para = Paragraph(docno[-4:], st['bigcode'])
    qr = make_qr(docno)
    ft = Table([[code_para, qr]], colWidths=[44*mm, 44*mm])
    ft.setStyle(TableStyle([('VALIGN',(0,0),(0,0),'MIDDLE'),('ALIGN',(0,0),(0,0),'LEFT'),
        ('VALIGN',(1,0),(1,0),'MIDDLE'),('ALIGN',(1,0),(1,0),'RIGHT'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    # legal text below the code/qr row (left aligned, full width)
    legal = Paragraph(_legal_note(lang), st['note'])
    story.append(ft)
    story.append(legal)
    doc.build(story)
    buf.seek(0); return buf.getvalue(), docno

def generate(doc_type, data, lang='uz'):
    if doc_type == 'qaydvarag':
        return generate_qaydvarag(data, lang)
    if doc_type == 'employment':
        return generate_employment(data, lang)
    if doc_type == 'salary':
        return generate_salary(data, lang)
    if doc_type == 'student':
        return generate_student(data, lang)
    raise ValueError("unknown doc_type")
