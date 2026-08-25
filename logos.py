# -*- coding: utf-8 -*-
"""Vector logos drawn with reportlab shapes (no external SVG renderer needed).
Draws: my.gov.uz badge (blue circle + white check) and Uzbekistan emblem.
Returns reportlab Drawing objects for direct placement in platypus flowables.
"""
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.graphics.shapes import (Drawing, Circle, Line, Path, Polygon,
                                         Rect, String)
from reportlab.graphics import renderPDF

BLUE = colors.HexColor('#1a6fb5')
BLUE_D = colors.HexColor('#155a95')
GOLD = colors.HexColor('#e8a200')

def mygov_logo(size=22*mm):
    d = Drawing(size, size)
    r = size/2
    d.add(Circle(r, r, r-2, fillColor=BLUE, strokeColor=BLUE_D, strokeWidth=2))
    # check mark
    c = size/2
    s = size*0.22
    d.add(Line(c-s, c+s*0.1, c-s*0.3, c+s*0.6, strokeColor=colors.white, strokeWidth=size*0.11, strokeLineCap=1))
    d.add(Line(c-s*0.3, c+s*0.6, c+s, c-s*0.5, strokeColor=colors.white, strokeWidth=size*0.11, strokeLineCap=1))
    return d

def uz_emblem(size=24*mm):
    d = Drawing(size, size)
    r = size/2
    cx = r; cy = r
    # outer circle
    d.add(Circle(cx, cy, r-1, fillColor=colors.white, strokeColor=BLUE_D, strokeWidth=2))
    # sun
    sr = size*0.13
    sc = cy - size*0.16
    d.add(Circle(cx, sc, sr, fillColor=GOLD))
    for ang in range(0, 360, 45):
        import math
        a = math.radians(ang)
        x1 = cx + math.cos(a)*(sr+2)
        y1 = sc + math.sin(a)*(sr+2)
        x2 = cx + math.cos(a)*(sr+7)
        y2 = sc + math.sin(a)*(sr+7)
        d.add(Line(x1, y1, x2, y2, strokeColor=GOLD, strokeWidth=1.5))
    # bird (simple stylized)
    d.add(Path(fillColor=BLUE, strokeColor=None,
               points=[cx, cy-2, cx-size*0.18, cy+size*0.06, cx-size*0.06, cy+size*0.06,
                       cx, cy+size*0.08, cx+size*0.06, cy+size*0.06, cx+size*0.18, cy+size*0.06]))
    # mountains
    d.add(Polygon(points=[cx-size*0.30, cy+size*0.20, cx-size*0.10, cy+size*0.05,
                          cx+size*0.05, cy+size*0.20, cx+size*0.22, cy+size*0.05,
                          cx+size*0.30, cy+size*0.20],
                   fillColor=BLUE_D, strokeColor=None))
    # wheat (left)
    d.add(Circle(cx-size*0.30, cy+size*0.02, size*0.07, fillColor=GOLD))
    d.add(Circle(cx-size*0.40, cy-0.04*size, size*0.05, fillColor=GOLD))
    d.add(Circle(cx-size*0.20, cy-0.04*size, size*0.05, fillColor=GOLD))
    # cotton (right)
    d.add(Circle(cx+size*0.30, cy+0.0*size, size*0.06, fillColor=colors.HexColor('#f4f4f4'), strokeColor=colors.HexColor('#cfcfcf'), strokeWidth=0.5))
    d.add(Circle(cx+size*0.22, cy+0.06*size, size*0.055, fillColor=colors.HexColor('#f4f4f4'), strokeColor=colors.HexColor('#cfcfcf'), strokeWidth=0.5))
    d.add(Circle(cx+size*0.38, cy+0.06*size, size*0.055, fillColor=colors.HexColor('#f4f4f4'), strokeColor=colors.HexColor('#cfcfcf'), strokeWidth=0.5))
    d.add(Circle(cx+size*0.30, cy+0.10*size, size*0.055, fillColor=colors.HexColor('#f4f4f4'), strokeColor=colors.HexColor('#cfcfcf'), strokeWidth=0.5))
    d.add(Circle(cx+size*0.30, cy+0.04*size, size*0.035, fillColor=GOLD))
    # ribbon
    d.add(Rect(cx-size*0.27, cy+size*0.27, size*0.54, size*0.06, fillColor=BLUE, strokeColor=None))
    return d
