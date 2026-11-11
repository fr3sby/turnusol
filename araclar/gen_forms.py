"""Turnusol optik form üreteci (A4, ArUco işaretli).
Her form için SVG + yerleşim JSON'u üretir (kod bu JSON'dan daire konumlarını okur).
Kullanım: python3 gen_forms.py cikti_klasoru

Form setleri (işaret numaraları sabittir, değiştirilmez):
  v1    Bozok (numaranın ilk 7 hanesi 2630112 olarak basılı): 50 → 0–7, 75 → 8–15, 100 → 16–23
  genel ön baskısız numara alanı:                           50 → 24–31, 75 → 32–39, 100 → 40–47
"""
import json, sys, os
import cv2
from PIL import ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(OUT, exist_ok=True)

PAGE_W, PAGE_H = 210.0, 297.0
S = 5.2916667                     # grid hücresi (mm)
X0 = (PAGE_W - 36 * S) / 2        # 9.75
Y0 = (PAGE_H - 52 * S) / 2        # ~10.92
def cx(c): return X0 + (c + 0.5) * S
def cy(r): return Y0 + (r + 0.5) * S
def cl(c): return X0 + c * S       # hücre sol kenarı
def rt(r): return Y0 + r * S       # hücre üst kenarı

TR_ALPHA = list('ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ')
STUDENT_PREFIX = '2630112'
ID_DIGITS = 11
KEY_STUDENT_ID = STUDENT_PREFIX + '9' * (ID_DIGITS - len(STUDENT_PREFIX))

FONT_SLAB = "'IBM Plex Sans'"
FONT_SANS = "'IBM Plex Sans'"
LETTER_GRAY = '#555555'
STRIPE = '#f0f0f0'
R_SMALL = 1.40                    # ad/soyad/numara daireleri
STROKE = 0.18

_pil = ImageFont.truetype(os.path.expanduser('~/.fonts/PlexVar.ttf'), 1000)
try: _pil.set_variation_by_name('Regular')
except Exception: pass
def textw(s, fs): return _pil.getlength(s) / 1000 * fs

ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
MARK = 7.5
MARK_POS = {  # (merkez x, merkez y)
    'TL': (9.75, 10.5), 'TM': (105.0, 10.5), 'TR': (200.25, 10.5),
    'BL': (9.75, 286.5), 'BM': (105.0, 286.5), 'BR': (200.25, 286.5),
}
MARK_POS['ML'] = (9.0, cy(32) - 0.4)        # sol kenar, ad-soyad ile sorular arası
MARK_POS['MR'] = (144.5, 165.0)             # sağ-iç: öğrenci no sütunu altındaki boşluk
MARK_ORDER = ['TL', 'TM', 'TR', 'ML', 'MR', 'BL', 'BM', 'BR']


class Svg:
    def __init__(self):
        self.parts = []
    def add(self, s): self.parts.append(s)
    def rect(self, x, y, w, h, fill='none', stroke=None, sw=0.35):
        st = f'fill:{fill};' + (f'stroke:{stroke};stroke-width:{sw}' if stroke else 'stroke:none')
        self.add(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" style="{st}"/>')
    def line(self, x1, y1, x2, y2, sw=0.26, color='#000'):
        self.add(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" style="stroke:{color};stroke-width:{sw};stroke-linecap:round"/>')
    def circle(self, x, y, r, fill='none', stroke='#000', sw=STROKE):
        self.add(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r:.3f}" style="fill:{fill};stroke:{stroke};stroke-width:{sw}"/>')
    def text(self, x, y, s, fs, anchor='start', bold=False, family=FONT_SLAB, color='#000'):
        s = s.replace('&', '&amp;').replace('<', '&lt;')
        w = 'bold' if bold else 'normal'
        self.add(f'<text x="{x:.3f}" y="{y:.3f}" style="font-family:{family};font-size:{fs:.3f}px;'
                 f'font-weight:{w};text-anchor:{anchor};fill:{color}" xml:space="preserve">{s}</text>')
    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" '
                    f'width="{PAGE_W}mm" height="{PAGE_H}mm" viewBox="0 0 {PAGE_W} {PAGE_H}">\n'
                    f'<rect x="0" y="0" width="{PAGE_W}" height="{PAGE_H}" fill="#fff"/>\n')
            f.write('\n'.join(self.parts))
            f.write('\n</svg>\n')


def bubble(svg, x, y, r, label, filled=False):
    if filled:
        svg.circle(x, y, r, fill='#000')
    else:
        svg.circle(x, y, r)
        fs = r * 1.43
        svg.text(x, y + fs * 0.355, label, fs, anchor='middle', family=FONT_SANS, color=LETTER_GRAY)


FRAME_SW = 0.28
def frame(svg, x0, y0, x1, y1, rx=1.6):
    svg.add(f'<rect x="{x0:.3f}" y="{y0:.3f}" width="{x1 - x0:.3f}" height="{y1 - y0:.3f}" '
            f'rx="{rx}" ry="{rx}" style="fill:none;stroke:#000;stroke-width:{FRAME_SW}"/>')

def section_frame(svg, c0, n, r0, r1):
    """c0..c0+n-1 sütunları, r0..r1 satırlarını saran yuvarlak çerçeve."""
    frame(svg, cl(c0) - 0.9, rt(r0) - 0.5, cl(c0 + n) + 0.9, rt(r1 + 1) + 0.5)

def header_boxes(svg, c0, n, row=2, digits=None):
    x, y = cl(c0), rt(row)
    ins = 0.3
    for k in range(n):
        svg.add(f'<rect x="{x + k * S + ins:.3f}" y="{y + ins:.3f}" width="{S - 2 * ins:.3f}" height="{S - 2 * ins:.3f}" '
                f'rx="0.8" ry="0.8" style="fill:#fff;stroke:#000;stroke-width:{FRAME_SW}"/>')
    if digits:
        for k, d in enumerate(digits):
            svg.text(cx(c0 + k), y + S / 2 + 1.25, d, 3.5, anchor='middle')


def letter_field(svg, c0, n, label, layout_key, layout):
    # şeritler (çift sıradaki sütunlar)
    for k in range(n):
        if k % 2 == 1:
            svg.rect(cl(c0 + k), rt(2), S, (3 + len(TR_ALPHA) - 2) * S, fill=STRIPE)
    section_frame(svg, c0, n, 1, 2 + len(TR_ALPHA))
    svg.text(cl(c0) + n * S / 2, rt(1) + S - 1.3, label, 3.17, anchor='middle', bold=True)
    header_boxes(svg, c0, n)
    cols = []
    for k in range(n):
        col = []
        for j, ch in enumerate(TR_ALPHA):
            x, y = cx(c0 + k), cy(3 + j)
            bubble(svg, x, y, R_SMALL, ch)
            col.append({'value': ch, 'x': round(x, 3), 'y': round(y, 3), 'r': R_SMALL})
        cols.append(col)
    layout['fields'][layout_key] = {'type': 'letter', 'columns': cols}


def student_id(svg, layout):
    c0, n = 24, ID_DIGITS
    STUDENT_PREFIX = layout['fields'].get('_prefix', '')
    for k in range(n):
        if k % 2 == 1:
            svg.rect(cl(c0 + k), rt(2), S, 11 * S, fill=STRIPE)
    section_frame(svg, c0, n, 1, 12)
    svg.text(cl(c0) + n * S / 2, rt(1) + S - 1.3, 'ÖĞRENCİ NUMARASI', 3.17, anchor='middle', bold=True)
    header_boxes(svg, c0, n, digits=STUDENT_PREFIX)
    cols = []
    for k in range(n):
        col = []
        pre = STUDENT_PREFIX[k] if k < len(STUDENT_PREFIX) else None
        for d in range(10):
            x, y = cx(c0 + k), cy(3 + d)
            bubble(svg, x, y, R_SMALL, str(d), filled=(pre == str(d)))
            col.append({'value': str(d), 'x': round(x, 3), 'y': round(y, 3), 'r': R_SMALL})
        cols.append(col)
    layout['fields'].pop('_prefix', None)
    layout['fields']['STUDENT_ID'] = {'type': 'number', 'columns': cols,
                                      'preprinted_prefix': STUDENT_PREFIX}
    if not STUDENT_PREFIX:
        layout['fields']['STUDENT_ID']['variable_length'] = True


def test_form_code(svg, layout):
    section_frame(svg, 24, 11, 14, 15)
    svg.text(cl(24) + 11 * S / 2, rt(14) + S - 1.3, 'KİTAPÇIK TÜRÜ (varsa)', 3.17, anchor='middle', bold=True)
    opts = []
    for k, ch in enumerate('ABCDEF'):
        x, y = cx(27 + k), cy(15)
        bubble(svg, x, y, R_SMALL, ch)
        opts.append({'value': ch, 'x': round(x, 3), 'y': round(y, 3), 'r': R_SMALL})
    layout['fields']['TEST_FORM_CODE'] = {'type': 'letter', 'columns': [opts], 'orientation': 'horizontal'}


EXAMPLE_REFS = []


def instructions(svg, x, y, w, h, items, fs_fixed=None, fit=False):
    pad = 2.0
    def layout_lines(fs):
        lh = fs * 1.45
        nw = textw('8. ', fs)
        avail = w - 2 * pad - nw
        lines = []
        for n, it in enumerate(items):
            if it == '__EXAMPLE__':
                lines.append(('ex', None, None)); continue
            cur, first = '', True
            for word in it.split():
                t = (cur + ' ' + word).strip()
                if textw(t, fs) <= avail: cur = t
                else:
                    lines.append(('t', cur, f'{n + 1 - (1 if n > items.index("__EXAMPLE__") else 0)}.' if first else None))
                    first, cur = False, word
            lines.append(('t', cur, f'{n + 1 - (1 if n > items.index("__EXAMPLE__") else 0)}.' if first else None))
        total = fs * 1.9 + lh * len(lines)
        return lines, lh, total, nw
    fs = fs_fixed or 3.3
    while True:
        if fs_fixed:
            lines, lh, total, nw = layout_lines(fs); break
        lines, lh, total, nw = layout_lines(fs)
        if total <= h - 2 * pad or fs <= 2.0: break
        fs -= 0.05
    if fit:
        h = total + 2 * pad
    frame(svg, x - 0.9, y, x + w + 0.9, y + h)
    yy = y + (h - total) / 2 + fs * 1.1
    svg.text(x + w / 2, yy, 'AÇIKLAMALAR', fs, anchor='middle', bold=True)
    yy += fs * 0.6
    for kind, s, num in lines:
        yy += lh
        if kind == 't':
            if num: svg.text(x + pad, yy, num, fs)
            svg.text(x + pad + nw, yy, s, fs)
        else:
            r = 1.45
            ccy = yy - fs * 0.35
            xx = x + pad + nw
            svg.text(xx, yy, 'Doğru:', fs); xx += textw('Doğru: ', fs) + r
            svg.circle(xx, ccy, r, fill='#000'); EXAMPLE_REFS.append({'x': round(xx, 3), 'y': round(ccy, 3), 'r': r}); xx += r + 4.5
            svg.text(xx, yy, 'Yanlış:', fs); xx += textw('Yanlış: ', fs) + r
            # çarpı
            svg.circle(xx, ccy, r); d = r * 1.05
            svg.line(xx - d, ccy - d, xx + d, ccy + d, sw=0.35); svg.line(xx - d, ccy + d, xx + d, ccy - d, sw=0.35)
            xx += 2 * r + 1.6
            # tik
            svg.circle(xx, ccy, r)
            svg.add(f'<polyline points="{xx - r * 0.9:.3f},{ccy:.3f} {xx - r * 0.2:.3f},{ccy + r * 0.8:.3f} {xx + r * 1.2:.3f},{ccy - r * 1.2:.3f}" style="fill:none;stroke:#000;stroke-width:0.4"/>')
            xx += 2 * r + 1.6
            # yarım dolu
            svg.circle(xx, ccy, r)
            svg.add(f'<ellipse cx="{xx - r * 0.25:.3f}" cy="{ccy + r * 0.2:.3f}" rx="{r * 0.55:.3f}" ry="{r * 0.4:.3f}" style="fill:#000"/>')


def question_block(svg, layout, first_q, n_rows, x_left, block_w, y_top, pitch, r, num_fs):
    """x_left: blok sol kenarı; numara sağa dayalı, ardından 5 şık."""
    num_zone = num_fs * (1.9 if r >= 2 else 2.3)
    bubble_pitch = S if r < 2 else (block_w - num_zone - 1.5) / 5
    bx0 = x_left + num_zone + 0.9 + r
    fx0, fx1 = x_left - 0.4, bx0 + 4 * bubble_pitch + r + 1.4
    frame(svg, fx0, y_top - 0.6, fx1, y_top + pitch * n_rows + 0.6)
    for i in range(n_rows):
        q = first_q + i
        y = y_top + pitch * (i + 0.5)
        svg.text(bx0 - r - 0.9, y + num_fs * 0.36, f'{q}.', num_fs, anchor='end', bold=True)
        opts = []
        for k, ch in enumerate('ABCDE'):
            x = bx0 + k * bubble_pitch
            bubble(svg, x, y, r, ch)
            opts.append({'value': ch, 'x': round(x, 3), 'y': round(y, 3), 'r': r})
        layout['questions'].append({'number': q, 'options': opts})


def aruco(svg, layout, form_index):
    marks = []
    for k, pos in enumerate(MARK_ORDER):
        mid = form_index * 8 + k
        img = cv2.aruco.generateImageMarker(ARUCO_DICT, mid, 6)
        mx, my = MARK_POS[pos]
        m = MARK / 6
        x0, y0 = mx - MARK / 2, my - MARK / 2
        for j in range(6):
            for i in range(6):
                if img[j, i] < 128:
                    svg.rect(x0 + i * m - 0.01, y0 + j * m - 0.01, m + 0.02, m + 0.02, fill='#000')
        marks.append({'id': mid, 'position': pos,
                      'corners': [[x0, y0], [x0 + MARK, y0], [x0 + MARK, y0 + MARK], [x0, y0 + MARK]]})
    layout['markers'] = marks


ITEMS = [
    'Yumuşak uçlu kurşun kalem kullanınız.',
    'Daireleri tamamen doldurunuz.',
    '__EXAMPLE__',
    'Düzeltmek için tamamen siliniz.',
    'Adınızı ve soyadınızı kutulara yazıp altındaki harfleri kodlayınız.',
    'Öğrenci numaranızın son 4 hanesini kodlayınız.',
    'Kitapçık türünü kodlayınız (varsa).',
    'Kâğıdı katlamayınız, buruşturmayınız.',
]


ITEMS_GENEL = [it.replace('Öğrenci numaranızın son 4 hanesini kodlayınız.',
                          'Öğrenci numaranızı en soldaki kutudan başlayarak yazıp kodlayınız.') for it in ITEMS]


def make_form(nq, form_index, genel=False):
    svg = Svg()
    EXAMPLE_REFS.clear()
    layout = {'form': f'{nq}q', 'num_questions': nq, 'page_mm': [PAGE_W, PAGE_H],
              'aruco_dict': 'DICT_4X4_50', 'key_student_id': '9' * ID_DIGITS if genel else KEY_STUDENT_ID,
              'alphabet': ''.join(TR_ALPHA), 'fields': {'_prefix': '' if genel else STUDENT_PREFIX}, 'questions': []}
    items = ITEMS_GENEL if genel else ITEMS
    aruco(svg, layout, form_index)
    svg.text(MARK_POS['TM'][0] + MARK / 2 + 2.0, MARK_POS['TM'][1] + 1.0, f'{nq} SORU', 3.0, bold=True, color='#333')
    letter_field(svg, 1, 12, 'ADI', 'FIRST_NAME', layout)
    letter_field(svg, 14, 9, 'SOYADI', 'LAST_NAME', layout)
    student_id(svg, layout)
    test_form_code(svg, layout)

    y_top, y_bot = rt(33), rt(51)
    H = y_bot - y_top
    block_w = 7 * S
    if nq == 50:
        rows, r, fs = 10, 1.75, 3.1
        pitch = H / 15
        for b in range(5):
            question_block(svg, layout, 1 + b * rows, rows, cl(1 + 7 * b) - 0.6, block_w, y_top, pitch, r, fs)
        instructions(svg, cl(24), rt(17) + 0.6, 11 * S, 15 * S, items, fs_fixed=2.75, fit=True)
    elif nq == 75:
        rows, r, fs = 15, 1.75, 3.1
        pitch = H / rows
        for b in range(5):
            question_block(svg, layout, 1 + b * rows, rows, cl(1 + 7 * b) - 0.6, block_w, y_top, pitch, r, fs)
        instructions(svg, cl(24), rt(17) + 0.6, 11 * S, 15 * S, items, fs_fixed=2.75, fit=True)
    elif nq == 100:
        rows, r, fs = 18, 1.6, 3.0
        pitch = H / rows
        for b in range(4):
            question_block(svg, layout, 1 + b * rows, rows, cl(1 + 7 * b) - 0.6, block_w, y_top, pitch, r, fs)
        # 73-100: sağ üstten aşağı kesintisiz 5. sütun (alt kısım diğer sütunlarla hizalı)
        question_block(svg, layout, 73, 28, cl(29) - 0.6, block_w, rt(23), S, r, fs)
        short = [
            'Kurşun kalemle daireleri tam doldurunuz.',
            '__EXAMPLE__',
            'Düzeltmek için tamamen siliniz.',
            ('Numaranızı soldan başlayarak ve kitapçık türünü (varsa) kodlayınız.' if genel else
             'Numaranın son 4 hanesini ve kitapçık türünü (varsa) kodlayınız.'),
        ]
        instructions(svg, cl(24), rt(17) + 0.6, 11 * S, 6 * S, short, fs_fixed=2.6, fit=True)
    layout['questions'].sort(key=lambda q: q['number'])
    if genel:
        layout['contrast_refs'] = list(EXAMPLE_REFS)
    name = f'optik_form_{nq}_soru' + ('_genel' if genel else '')
    svg.save(os.path.join(OUT, name + '.svg'))
    with open(os.path.join(OUT, name + '.json'), 'w', encoding='utf-8') as f:
        json.dump(layout, f, ensure_ascii=False, indent=1)
    return name


if __name__ == '__main__':
    for idx, nq in enumerate((50, 75, 100)):
        print(make_form(nq, idx))
    for idx, nq in enumerate((50, 75, 100)):
        print(make_form(nq, 3 + idx, genel=True))
