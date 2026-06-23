#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de PDF en Python puro (sin dependencias externas).
Convierte un subconjunto de Markdown a PDF con paginacion, titulos,
negritas, vinetas, listas numeradas, reglas horizontales y tablas simples.
"""
import sys

# --------- Metricas de fuente (Helvetica, unidades/1000) ---------
HELV = {
    ' ':278,'!':278,'"':355,'#':556,'$':556,'%':889,'&':667,"'":191,'(':333,')':333,
    '*':389,'+':584,',':278,'-':333,'.':278,'/':278,'0':556,'1':556,'2':556,'3':556,
    '4':556,'5':556,'6':556,'7':556,'8':556,'9':556,':':278,';':278,'<':584,'=':584,
    '>':584,'?':556,'@':1015,'A':667,'B':667,'C':722,'D':722,'E':667,'F':611,'G':778,
    'H':722,'I':278,'J':500,'K':667,'L':556,'M':833,'N':722,'O':778,'P':667,'Q':778,
    'R':722,'S':667,'T':611,'U':722,'V':667,'W':944,'X':667,'Y':667,'Z':611,'[':278,
    '\\':278,']':278,'^':469,'_':556,'`':333,'a':556,'b':556,'c':500,'d':556,'e':556,
    'f':278,'g':556,'h':556,'i':222,'j':222,'k':500,'l':222,'m':833,'n':556,'o':556,
    'p':556,'q':556,'r':333,'s':500,'t':278,'u':556,'v':500,'w':722,'x':500,'y':500,
    'z':500,'{':334,'|':260,'}':334,'~':584,
}
# Acentos espanoles: misma anchura que su letra base
for acc, base in [('\u00e1','a'),('\u00e9','e'),('\u00ed','i'),('\u00f3','o'),('\u00fa','u'),
                  ('\u00f1','n'),('\u00fc','u'),('\u00c1','A'),('\u00c9','E'),('\u00cd','I'),
                  ('\u00d3','O'),('\u00da','U'),('\u00d1','N'),('\u00bf','?'),('\u00a1','!')]:
    HELV[acc] = HELV.get(base, 556)

def char_width(c):
    return HELV.get(c, 556)

def text_width(s, size, bold=False):
    w = sum(char_width(c) for c in s)
    if bold:
        w *= 1.06  # margen de seguridad para negrita
    return w * size / 1000.0

# --------- Pagina ---------
PAGE_W, PAGE_H = 595.28, 841.89  # A4 en puntos
MARGIN = 56
CONTENT_W = PAGE_W - 2 * MARGIN
TOP = PAGE_H - MARGIN
BOTTOM = MARGIN

class PDF:
    def __init__(self):
        self.pages = []      # cada pagina: lista de fragmentos de stream (bytes)
        self.cur = []
        self.y = TOP
        self.new_page_started = True

    def _newpage(self):
        if self.cur:
            self.pages.append(self.cur)
        self.cur = []
        self.y = TOP

    def ensure(self, h):
        if self.y - h < BOTTOM:
            self._newpage()

    def add_line_runs(self, runs, size, x, leading, color=(0,0,0)):
        # runs: lista de (texto, bold)
        self.ensure(leading)
        self.y -= size  # baseline
        parts = []
        r, g, b = color
        parts.append(b"%.3f %.3f %.3f rg" % (r, g, b))
        parts.append(b"BT")
        parts.append(b"1 0 0 1 %.2f %.2f Tm" % (x, self.y))
        for txt, bold in runs:
            font = b"/F2" if bold else b"/F1"
            parts.append(b"%s %.2f Tf" % (font, size))
            parts.append(b"(%s) Tj" % esc(txt))
        parts.append(b"ET")
        self.cur.append(b"\n".join(parts))
        self.y -= (leading - size)

    def hrule(self):
        self.ensure(10)
        self.y -= 6
        self.cur.append(b"0.6 0.6 0.6 RG\n0.5 w\n%.2f %.2f m %.2f %.2f l S" %
                        (MARGIN, self.y, PAGE_W - MARGIN, self.y))
        self.y -= 8

    def space(self, h):
        self.ensure(h)
        self.y -= h

    def build(self):
        if self.cur:
            self.pages.append(self.cur)
        return assemble(self.pages)

def esc(s):
    b = s.encode('cp1252', 'replace')
    return b.replace(b'\\', b'\\\\').replace(b'(', b'\\(').replace(b')', b'\\)')

# --------- Wrapping de texto con runs ---------
def wrap_runs(runs, size, max_w, bold_default=False):
    """runs: lista de (texto, bold). Devuelve lista de lineas (cada una lista de runs)."""
    # tokenizar en palabras manteniendo bold
    words = []  # (palabra, bold)
    for txt, bold in runs:
        for i, w in enumerate(txt.split(' ')):
            if w == '' and i == 0:
                continue
            words.append((w, bold))
    lines = []
    cur = []
    cur_w = 0.0
    space_w = text_width(' ', size)
    for w, bold in words:
        ww = text_width(w, size, bold)
        add = ww if not cur else ww + space_w
        if cur and cur_w + add > max_w:
            lines.append(cur)
            cur = [(w, bold)]
            cur_w = ww
        else:
            if cur:
                cur.append((' ' + w, bold))
            else:
                cur.append((w, bold))
            cur_w += add
    if cur:
        lines.append(cur)
    return lines if lines else [[('', bold_default)]]

def parse_inline(text):
    """Divide en runs segun **negrita**."""
    runs = []
    i = 0
    bold = False
    buf = ''
    while i < len(text):
        if text[i:i+2] == '**':
            if buf:
                runs.append((buf, bold))
                buf = ''
            bold = not bold
            i += 2
        else:
            buf += text[i]
            i += 1
    if buf:
        runs.append((buf, bold))
    return runs if runs else [('', False)]

# --------- Conversion Markdown -> PDF ---------
def render(md, pdf):
    lines = md.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        if line.strip() == '':
            pdf.space(4)
            continue
        if line.strip() == '---':
            pdf.hrule()
            continue
        # Tabla
        if line.lstrip().startswith('|'):
            table = [line]
            while i < len(lines) and lines[i].lstrip().startswith('|'):
                table.append(lines[i])
                i += 1
            render_table(table, pdf)
            continue
        # Encabezados
        if line.startswith('### '):
            pdf.space(4)
            pdf.add_line_runs([(line[4:], True)], 12, MARGIN, 16, color=(0.16,0.16,0.45))
            continue
        if line.startswith('## '):
            pdf.space(6)
            pdf.add_line_runs([(line[3:], True)], 14.5, MARGIN, 19, color=(0.10,0.10,0.55))
            continue
        if line.startswith('# '):
            pdf.space(8)
            for ln in wrap_runs([(line[2:], True)], 18, CONTENT_W):
                pdf.add_line_runs(ln, 18, MARGIN, 23, color=(0.05,0.05,0.5))
            pdf.space(2)
            continue
        # Vineta
        if line.lstrip().startswith('- '):
            indent = len(line) - len(line.lstrip())
            x = MARGIN + 12 + (14 if indent >= 2 else 0)
            content = line.lstrip()[2:]
            runs = parse_inline(content)
            render_bullet(pdf, runs, x)
            continue
        # Lista numerada
        stripped = line.lstrip()
        if len(stripped) > 2 and stripped[0].isdigit() and stripped[1:3] == '. ':
            num = stripped.split('.')[0]
            content = stripped[len(num)+2:]
            render_numbered(pdf, num, parse_inline(content))
            continue
        # Parrafo normal
        runs = parse_inline(line)
        for ln in wrap_runs(runs, 10.5, CONTENT_W):
            pdf.add_line_runs(ln, 10.5, MARGIN, 14)

def render_bullet(pdf, runs, x):
    avail = CONTENT_W - (x - MARGIN)
    wrapped = wrap_runs(runs, 10.5, avail)
    for idx, ln in enumerate(wrapped):
        if idx == 0:
            pdf.add_line_runs([('-  ', False)] + ln, 10.5, x - 12, 14)
        else:
            pdf.add_line_runs(ln, 10.5, x, 14)

def render_numbered(pdf, num, runs):
    x = MARGIN + 18
    avail = CONTENT_W - 18
    wrapped = wrap_runs(runs, 10.5, avail)
    for idx, ln in enumerate(wrapped):
        if idx == 0:
            pdf.add_line_runs([(num + '. ', True)] + ln, 10.5, MARGIN, 14)
        else:
            pdf.add_line_runs(ln, 10.5, x, 14)

def render_table(rows, pdf):
    parsed = []
    for r in rows:
        cells = [c.strip() for c in r.strip().strip('|').split('|')]
        if all(set(c) <= set('-: ') and c for c in cells):
            continue  # fila separadora
        parsed.append(cells)
    if not parsed:
        return
    ncol = max(len(r) for r in parsed)
    colw = (CONTENT_W) / ncol
    pdf.space(3)
    for ri, cells in enumerate(parsed):
        header = (ri == 0)
        # altura de fila: calcular lineas por celda
        cell_lines = []
        maxlines = 1
        for c in cells:
            runs = parse_inline(c)
            wl = wrap_runs(runs, 9.5, colw - 8, bold_default=header)
            if header:
                wl = [[(t, True) for (t, _b) in ln] for ln in wl]
            cell_lines.append(wl)
            maxlines = max(maxlines, len(wl))
        rowh = maxlines * 12 + 4
        pdf.ensure(rowh)
        ytop = pdf.y
        # texto de cada celda
        for ci in range(len(cells)):
            cx = MARGIN + ci * colw + 4
            yy = ytop
            for ln in cell_lines[ci]:
                pdf.y = yy
                pdf.add_line_runs(ln, 9.5, cx, 12)
                yy -= 12
        pdf.y = ytop - rowh
    pdf.space(4)

# --------- Ensamblado del PDF ---------
def assemble(pages):
    objs = []
    def add(b):
        objs.append(b)
        return len(objs)  # numero de objeto (1-indexado)

    font1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    font2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")

    page_obj_ids = []
    content_ids = []
    # reservaremos: necesitamos pages root id; lo calculamos despues
    # primero creamos contenidos
    for frags in pages:
        stream = b"\n".join(frags)
        cid = add(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
        content_ids.append(cid)

    pages_root_placeholder = None
    # crear objetos de pagina (necesitan id del Pages root)
    # Reservamos el id del Pages root ahora:
    pages_root_id = len(objs) + len(pages) + 1  # paginas + luego root
    for idx, cid in enumerate(content_ids):
        pobj = (b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] "
                b"/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> "
                b"/Contents %d 0 R >>" % (pages_root_id, PAGE_W, PAGE_H, font1, font2, cid))
        pid = add(pobj)
        page_obj_ids.append(pid)

    kids = b" ".join(b"%d 0 R" % pid for pid in page_obj_ids)
    pages_root = add(b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, len(page_obj_ids)))
    assert pages_root == pages_root_id, (pages_root, pages_root_id)
    catalog = add(b"<< /Type /Catalog /Pages %d 0 R >>" % pages_root)

    # escribir
    out = bytearray()
    out += b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = [0] * (len(objs) + 1)
    for n, body in enumerate(objs, start=1):
        offsets[n] = len(out)
        out += b"%d 0 obj\n" % n
        out += body
        out += b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(objs) + 1)
    out += b"0000000000 65535 f \n"
    for n in range(1, len(objs) + 1):
        out += b"%010d 00000 n \n" % offsets[n]
    out += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objs) + 1, catalog, xref_pos)
    return bytes(out)

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else 'apuntes_bbdd.md'
    dst = sys.argv[2] if len(sys.argv) > 2 else 'apuntes_bbdd.pdf'
    with open(src, 'r', encoding='utf-8') as f:
        md = f.read()
    pdf = PDF()
    render(md, pdf)
    data = pdf.build()
    with open(dst, 'wb') as f:
        f.write(data)
    print("PDF generado: %s (%d bytes, %d paginas)" % (dst, len(data), len(pdf.pages)))

if __name__ == '__main__':
    main()
