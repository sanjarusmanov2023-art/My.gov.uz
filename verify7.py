import fitz, os, sys, io, json
sys.path.insert(0, r"C:\Users\Asus\Projects\govpdf")
import app as APP

DPI = 200
PX_PER_MM = DPI/72*25.4
ATT = r"C:\Users\Asus\AppData\Local\hermes\attachments"
OUT = r"C:\Users\Asus\Projects\govpdf\compare"
os.makedirs(OUT, exist_ok=True)

def spans(path):
    d = fitz.open(stream=open(path,'rb').read(), filetype='pdf')
    out = []
    for pi in range(d.page_count):
        for b in d[pi].get_text("dict")["blocks"]:
            if "lines" not in b: continue
            for l in b["lines"]:
                for s in l["spans"]:
                    x0,y0,x1,y1 = s["bbox"]
                    out.append({"page": pi+1,"t": s["text"],
                        "y0": y0,"x0": x0,"x1": x1,
                        "yp": round(y0*DPI/72,1),"xp": round(x0*DPI/72,1),
                        "size": round(s["size"],1)})
    return out, d.page_count

def find(spans, key):
    return [s for s in spans if key.lower() in s["t"].lower()]

def mm(v): return round(v/PX_PER_MM,1)

cases = {
 "student": ("Камилов Мухаммадали ўқиш жойидан маълумотнома -3.pdf",
   {'fio':"KAMILOV M A",'pinfl':'52806077090017','birth':'28.06.2007','citizenship':"O'zbekiston Respublikasi fuqarosi",
    'edu_type':'Bakalavr','edu_form':'Kunduzgi','admission':"To'lov-shartnoma",'enroll_year':'2025',
    'university':'Toshkent Turin','faculty':'Umumtexnika','direction':'Biznes','course':'1-kurs','app_no':'273429363'}),
 "qaydvarag": ("4182-516a-6ac9-7013-7709-9470-8241-2.pdf",
   {'stir':'312294467','reg_date':'21.07.2025','reg_no':'2885831','entity_name':'FELIKS TRAVEL MCHJ','org_form':'MCHJ',
    'own_form':'Xususiy','activity':'Sayohat','entity_type':'Yuridik shaxs','charter_capital':'10000000',
    'head_name':'KARIMOV A','head_stir':'123','email':'a@b.uz','phone':'99','district':'Yangihayot','address':'Yangi Umid','issued_to':'KARIMOVA S','pinfl':'41912912920015','app_no':'317791863'}),
 "salary": ("income statement.pdf",
   {'issued_to':'ABDULLAYEVA G','pinfl':'41407870420049','app_no':'326555675','total_salary':'66 535 317','income_tax':'7 984 238',
    'salary_rows':[{'year':'2025','month':'Noyabr','org':'NAFTA-TRADE MCHJ','wage':'2 840 909','pit':'340 909','other':'0','inps':'0'},
                   {'year':'2025','month':'Dekabr','org':'TRANSPARENT QUALITY TRADE MCHJ','wage':'2 272 727','pit':'272 727','other':'0','inps':'0'}]}),
 "employment": (None,
   {'works':[{'start':'01.01.2020','end':'01.06.2023','org':'ABC LLC','inn':'123','position':'Manager','dept':'IT'}],
    'issued_to':'PETROV I','pinfl':'555','app_no':'999'}),
}

# build mine
for t,(srcf,data) in cases.items():
    pdf, dn = APP.generate(t, data, 'uz')
    open(os.path.join(OUT, f"mine_{t}.pdf"),'wb').write(pdf)
    d = fitz.open(stream=pdf, filetype='pdf')
    d[0].get_pixmap(dpi=DPI).save(os.path.join(OUT, f"mine_{t}_p1.png"))
    if d.page_count>1: d[1].get_pixmap(dpi=DPI).save(os.path.join(OUT, f"mine_{t}_p2.png"))
print("BUILT")

# compare
for t,(srcf,data) in cases.items():
    if srcf is None:
        print(f"\n=== {t}: NO ORIGINAL -> skip compare ===")
        continue
    src, sp = spans(os.path.join(ATT, srcf))
    mine, mp = spans(os.path.join(OUT, f"mine_{t}.pdf"))
    print(f"\n=== {t}: pages SRC={sp} MINE={mp} ===")
    # timestamp x-fraction
    ss = find(src, "2026"); ms = find(mine, "2026")
    if ss and ms:
        sxf = ss[0]['x0']/595; mxf = ms[0]['x0']/595
        print(f"  TIMESTAMP xfrac: SRC={sxf:.2f} MINE={mxf:.2f} {'OK' if abs(sxf-mxf)<0.06 else '*** FAR (should be edge ~0.79)'}")
    keys = {
      "student": ["№","Hujjat berilgan","O'QISH JOYID","F.I.O.","JSH ShIR","Mazkur hujjat Vazirlar"],
      "qaydvarag": ["№","Hujjat berilgan","QAYD VARAG","STIR","Umumiy ma'lumot","Mazkur hujjat Vazirlar"],
      "salary": ["№","CERTIFICATE OF CALCULATED","Name:","Total estimated salary","Enterprise (Organization)","Accrued wage","Mazkur hujjat"],
    }.get(t, [])
    for k in keys:
        s = find(src,k); m = find(mine,k)
        if s and m:
            s0=s[0]; m0=m[0]
            dy = round(m0['yp']-s0['yp'],1); dymm = mm(abs(dy))
            flag = "OK" if abs(dy)<30 else "*** FAR"
            print(f"  {k[:24]:24} y:{s0['yp']:>6}->{m0['yp']:>6} dy={dy:>+6}px({dymm:>4}mm) sz:{s0['size']}/{m0['size']} {flag}")
        elif s: print(f"  {k[:24]:24} SRC only")
        elif m: print(f"  {k[:24]:24} MINE only")
print("\nDONE")
