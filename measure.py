import fitz, os, json
from PIL import Image

DPI = 200
SRC = r"C:\Users\Asus\AppData\Local\hermes\attachments\Камилов Мухаммадали ўқиш жойидан маълумотнома .pdf"
MINE = r"C:\Users\Asus\Downloads\student_1210-4351-1434-2021-4512-0014.pdf"
OUT = r"C:\Users\Asus\Projects\govpdf\compare"

def render(path, name):
    d = fitz.open(path)
    pix = d[0].get_pixmap(dpi=DPI)
    img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    img.save(os.path.join(OUT, name + ".png"))
    # extract text with bounding boxes (in pixels at DPI)
    blocks = []
    for b in d[0].get_text("dict")["blocks"]:
        if "lines" not in b:
            continue
        for l in b["lines"]:
            for s in l["spans"]:
                x0, y0, x1, y1 = s["bbox"]
                blocks.append({
                    "text": s["text"],
                    "x0": round(x0 * DPI / 72, 1),
                    "y0": round(y0 * DPI / 72, 1),
                    "x1": round(x1 * DPI / 72, 1),
                    "y1": round(y1 * DPI / 72, 1),
                    "size": round(s["size"], 1),
                    "color": s["color"],
                })
    return img.size, blocks, d[0].rect.width, d[0].rect.height

def images_info(path, name):
    d = fitz.open(path)
    imgs = []
    for i in d[0].get_images(full=True):
        xref = i[0]
        try:
            info = d[0].extract_image(xref)
            imgs.append({"w": info["width"], "h": info["height"]})
        except Exception as e:
            imgs.append({"err": str(e)})
    return imgs

src_size, src_blocks, src_w, src_h = render(SRC, "src_student_meas")
mine_size, mine_blocks, mine_w, mine_h = render(MINE, "mine_student_meas")

print("=== PAGE SIZE (pt) ===")
print("SRC:", round(src_w,1), "x", round(src_h,1))
print("MINE:", round(mine_w,1), "x", round(mine_h,1), "(A4 = 595.27 x 841.89)")
print()
print("=== IMAGE COUNT & SIZE (embedded) ===")
print("SRC imgs:", images_info(SRC, "src"))
print("MINE imgs:", images_info(MINE, "mine"))
print()
print("=== SRC TEXT BLOCKS (first 40) ===")
for b in src_blocks[:40]:
    print(f"  y0={b['y0']:>5}  x0={b['x0']:>5}  size={b['size']:>4}  {b['text'][:50]}")
print()
print("=== MINE TEXT BLOCKS (first 40) ===")
for b in mine_blocks[:40]:
    print(f"  y0={b['y0']:>5}  x0={b['x0']:>5}  size={b['size']:>4}  {b['text'][:50]}")
print()
print("DONE")
