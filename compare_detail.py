import fitz, os, json
from PIL import Image

DPI = 200
ATT = r"C:\Users\Asus\AppData\Local\hermes\attachments"
OUT = r"C:\Users\Asus\Projects\govpdf\compare"

def spans(path):
    d = fitz.open(path)
    out = []
    for pi in range(d.page_count):
        for b in d[pi].get_text("dict")["blocks"]:
            if "lines" not in b: continue
            for l in b["lines"]:
                for s in l["spans"]:
                    x0,y0,x1,y1 = s["bbox"]
                    out.append({
                        "page": pi+1, "t": s["text"],
                        "x0": round(x0*DPI/72,1), "y0": round(y0*DPI/72,1),
                        "x1": round(x1*DPI/72,1), "y1": round(y1*DPI/72,1),
                        "size": round(s["size"],1),
                    })
    return out, d.page_count

def find(spans, key, first=True):
    res = [s for s in spans if key.lower() in s["t"].lower()]
    return res[0] if res and first else (res if res else None)

# ---- QAYDVARAG comparison: original salary_B vs my fix_qayd ----
src, src_pages = spans(os.path.join(ATT, "4182-516a-6ac9-7013-7709-9470-8241-2.pdf"))
mine, mine_pages = spans(os.path.join(OUT, "fix_qayd.pdf"))

print("=== QAYDVARAG: ORIGINAL vs MINE (key elements) ===")
checks = ["№", "Hujjat berilgan", "QAYD VARAG", "STIR", "Umumiy ma'lumot", "Yuridik shaxsning nomi", "Mazkur hujjat"]
for c in checks:
    s = find(src, c); m = find(mine, c)
    if s and m:
        print(f"  [{c[:20]:20}] y: {s['y0']:>6} vs {m['y0']:>6} | size: {s['size']:>4} vs {m['size']:>4} | x0: {s['x0']:>6} vs {m['x0']:>6}")
    elif s:
        print(f"  [{c[:20]:20}] SRC only y={s['y0']} sz={s['size']}")
    elif m:
        print(f"  [{c[:20]:20}] MINE only y={m['y0']} sz={m['size']}")

# page count
print(f"  pages: SRC={src_pages} MINE={mine_pages}")

# ---- STUDENT comparison: original student_C vs my fix6 ----
src_s, sp = spans(os.path.join(ATT, "Камилов Мухаммадали ўқиш жойидан маълумотнома -3.pdf"))
mine_s, mp = spans(os.path.join(OUT, "fix6_student.pdf"))
print("\n=== STUDENT: ORIGINAL vs MINE ===")
checks2 = ["№", "Hujjat berilgan", "O'QISH JOYID", "F.I.O.", "JSH ShIR", "Mazkur hujjat"]
for c in checks2:
    s = find(src_s, c); m = find(mine_s, c)
    if s and m:
        print(f"  [{c[:20]:20}] y: {s['y0']:>6} vs {m['y0']:>6} | size: {s['size']:>4} vs {m['size']:>4}")
    elif s:
        print(f"  [{c[:20]:20}] SRC only y={s['y0']} sz={s['size']}")
    elif m:
        print(f"  [{c[:20]:20}] MINE only y={m['y0']} sz={m['size']}")
print(f"  pages: SRC={sp} MINE={mp}")

# ---- SALARY comparison: original income_D p2 table vs my fix_salary p2 ----
src_d, dp = spans(os.path.join(ATT, "income statement.pdf"))
mine_d, mdp = spans(os.path.join(OUT, "fix_salary.pdf"))
print("\n=== SALARY: ORIGINAL (income_D) vs MINE ===")
# find table header
sh = find(src_d, "Enterprise (Organization)"); mh = find(mine_d, "Enterprise (Organization)")
print(f"  table header 'Enterprise': SRC y={sh['y0'] if sh else 'NA'} | MINE y={mh['y0'] if mh else 'NA'}")
# big code
sc = find(src_d, None)
# find 4-digit code near bottom (size 22.5)
src_codes = [s for s in src_d if s["size"]>=22 and s["t"].isdigit()]
mine_codes = [s for s in mine_d if s["size"]>=22 and s["t"].isdigit()]
print(f"  big code SRC: {[s['t'] for s in src_codes]} | MINE: {[s['t'] for s in mine_codes]}")
print(f"  pages: SRC={dp} MINE={mdp}")

print("\nDONE")
