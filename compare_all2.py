import fitz, os, json

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

def find(spans, key):
    res = [s for s in spans if key.lower() in s["t"].lower()]
    return res[0] if res else None

def compare(name, src_path, mine_path, keys):
    src, sp = spans(src_path)
    mine, mp = spans(mine_path)
    print(f"\n=== {name} ===  pages SRC={sp} MINE={mp}")
    print(f"  {'element':22} {'SRC_y':>7} {'MINE_y':>7} {'dy':>6} {'SRC_sz':>6} {'MINE_sz':>7}")
    for c in keys:
        s = find(src, c); m = find(mine, c)
        if s and m:
            dy = round(m['y0']-s['y0'],1)
            print(f"  {c[:22]:22} {s['y0']:>7} {m['y0']:>7} {dy:>+6} {s['size']:>6} {m['size']:>7}")
        elif s:
            print(f"  {c[:22]:22} {s['y0']:>7} {'—':>7} {'SRC':>6} {s['size']:>6} {'—':>7}")
        elif m:
            print(f"  {c[:22]:22} {'—':>7} {m['y0']:>7} {'MINE':>6} {'—':>6} {m['size']:>7}")

# 1. QAYDVARAG: original salary_B = qaydvarag
compare("QAYDVARAG",
    os.path.join(ATT, "4182-516a-6ac9-7013-7709-9470-8241-2.pdf"),
    os.path.join(OUT, "fix_qayd.pdf"),
    ["№", "Hujjat berilgan", "QAYD VARAG", "STIR", "Umumiy ma'lumot", "Yuridik shaxsning nomi", "Mazkur hujjat Vazirlar"])

# 2. STUDENT: original student_C
compare("STUDENT",
    os.path.join(ATT, "Камилов Мухаммадали ўқиш жойидан маълумотнома -3.pdf"),
    os.path.join(OUT, "fix6_student.pdf"),
    ["№", "Hujjat berilgan", "O'QISH JOYID", "F.I.O.", "JSH ShIR", "Mazkur hujjat Vazirlar"])

# 3. SALARY: original income_D (en) — compare page2 table + footer
compare("SALARY (p2 table/footer)",
    os.path.join(ATT, "income statement.pdf"),
    os.path.join(OUT, "fix_salary.pdf"),
    ["Enterprise (Organization)", "Accrued wage", "Mazkur hujjat", "Total estimated salary"])

# 4. SALARY_A (en, differently structured) for reference
compare("SALARY_A (ref)",
    os.path.join(ATT, "file (3) (2)-2.pdf"),
    os.path.join(OUT, "fix_salary.pdf"),
    ["№", "CERTIFICATE OF CALCULATED", "Name:", "Total estimated salary"])

print("\nDONE")
