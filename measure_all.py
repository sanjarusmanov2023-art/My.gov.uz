import fitz, os, json
from PIL import Image

DPI = 200
ATT = r"C:\Users\Asus\AppData\Local\hermes\attachments"
OUT = r"C:\Users\Asus\Projects\govpdf\compare"
files = {
    "salary_A": "file (3) (2)-2.pdf",
    "salary_B": "4182-516a-6ac9-7013-7709-9470-8241-2.pdf",
    "student_C": "Камилов Мухаммадали ўқиш жойидан маълумотнома -3.pdf",
    "income_D": "income statement.pdf",
}

def render(path, name):
    full = os.path.join(ATT, path)
    d = fitz.open(full)
    print(f"\n===== {name} | pages={d.page_count} | size={round(d[0].rect.width,1)}x{round(d[0].rect.height,1)} =====")
    for pi in range(d.page_count):
        pix = d[pi].get_pixmap(dpi=DPI)
        img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        img.save(os.path.join(OUT, f"{name}_p{pi+1}.png"))
        blocks = []
        for b in d[pi].get_text("dict")["blocks"]:
            if "lines" not in b:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    x0,y0,x1,y1 = s["bbox"]
                    blocks.append({
                        "t": s["text"],
                        "x0": round(x0*DPI/72,1), "y0": round(y0*DPI/72,1),
                        "x1": round(x1*DPI/72,1), "y1": round(y1*DPI/72,1),
                        "size": round(s["size"],1),
                    })
        print(f"  --- page {pi+1}: {len(blocks)} text spans ---")
        # Print a representative sample: first 25 spans and any containing digits/table
        for b in blocks[:25]:
            print(f"    y0={b['y0']:>6} x0={b['x0']:>6} sz={b['size']:>4} {b['t'][:55]}")

for name, fn in files.items():
    render(fn, name)
print("\nALL RENDERED")
