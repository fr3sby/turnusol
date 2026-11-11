"""Formları öğrenci gibi doldurur, kötü tarama koşulları uygular, okuyucuyla okur ve karşılaştırır."""
import json, os, subprocess, random, sys
import numpy as np
import cv2
sys.path.insert(0, os.path.dirname(__file__))
FORMS = sys.argv[1] if __name__ == '__main__' else None
OUT = sys.argv[2] if __name__ == '__main__' else None
if OUT: os.makedirs(OUT, exist_ok=True)
DPI = 300
MM = DPI / 25.4
rng = random.Random(7)
nrng = np.random.default_rng(7)


def render(nq):
    p = os.path.join(OUT, f'bos_{nq}')
    subprocess.run(['pdftoppm', '-gray', '-png', '-r', str(DPI), '-singlefile',
                    os.path.join(FORMS, f'optik_form_{nq}_soru.pdf'), p], check=True)
    return cv2.imread(p + '.png', cv2.IMREAD_GRAYSCALE)


def pencil(img, b, kind):
    x, y, r = b['x'] * MM, b['y'] * MM, b['r'] * MM
    x += rng.uniform(-0.15, 0.15) * r; y += rng.uniform(-0.15, 0.15) * r
    m = np.zeros_like(img, dtype=np.uint8)
    if kind == 'tam':
        cv2.ellipse(m, (int(x), int(y)), (int(r * rng.uniform(0.95, 1.12)), int(r * rng.uniform(0.95, 1.12))),
                    rng.uniform(0, 180), 0, 360, 255, -1)
        tone = rng.uniform(35, 85)
    elif kind == 'kismi':      # daireyi tam doldurmamış: ~%55-70
        cv2.ellipse(m, (int(x - 0.2 * r), int(y + 0.1 * r)), (int(r * 0.78), int(r * 0.62)),
                    rng.uniform(0, 180), 0, 360, 255, -1)
        tone = rng.uniform(40, 90)
    elif kind == 'acik':       # hafif bastırılmış kalem
        cv2.ellipse(m, (int(x), int(y)), (int(r), int(r)), 0, 0, 360, 255, -1)
        tone = rng.uniform(135, 155)
    elif kind == 'silik':      # silinmiş işaretin kalıntısı
        cv2.ellipse(m, (int(x), int(y)), (int(r * 1.1), int(r)), 20, 0, 360, 255, -1)
        tone = rng.uniform(200, 218)
    elif kind == 'tik':
        pts = np.int32([[x - 0.8 * r, y], [x - 0.2 * r, y + 0.8 * r], [x + 1.1 * r, y - 1.1 * r]])
        cv2.polylines(m, [pts], False, 255, max(2, int(0.25 * r)))
        tone = 60
    tex = nrng.normal(0, 18, img.shape[:2]).astype(np.float32) if kind != 'silik' else 0
    sel = m > 0
    val = np.clip(tone + (tex[sel] if not np.isscalar(tex) else 0), 0, 255)
    img[sel] = np.minimum(img[sel], val.astype(np.uint8))


def fill_sheet(img, L, with_booklet=True):
    truth = {}
    plan = (['tam'] * 62 + ['kismi'] * 12 + ['acik'] * 6 + ['silinip'] * 8 + ['bos'] * 5 + ['cift'] * 4 + ['tik'] * 3)
    for q in L['questions']:
        kind = rng.choice(plan)
        opts = q['options']
        a = rng.randrange(5)
        if kind == 'bos':
            truth[q['number']] = ('', kind)
        elif kind == 'cift':
            b2 = (a + rng.randrange(1, 5)) % 5
            pencil(img, opts[a], 'tam'); pencil(img, opts[b2], 'tam')
            truth[q['number']] = ('*', kind)
        elif kind == 'silinip':
            old = (a + rng.randrange(1, 5)) % 5
            pencil(img, opts[old], 'silik'); pencil(img, opts[a], 'tam')
            truth[q['number']] = (opts[a]['value'], kind)
        else:
            pencil(img, opts[a], kind)
            truth[q['number']] = (opts[a]['value'], kind)
    def write_field(key, text):
        cols = L['fields'][key]['columns']
        for ci, ch in enumerate(text):
            for b in cols[ci]:
                if b['value'] == ch:
                    pencil(img, b, rng.choice(['tam', 'tam', 'kismi']))
    write_field('FIRST_NAME', 'AYŞE')
    write_field('LAST_NAME', 'GÜLTEKİN')
    cols = L['fields']['STUDENT_ID']['columns']
    last4 = '0457'
    for k, d in enumerate(last4):
        pencil(img, cols[7 + k][int(d)], 'tam')
    if with_booklet:
        pencil(img, L['fields']['TEST_FORM_CODE']['columns'][0][1], 'tam')
    return truth, {'FIRST_NAME': 'AYŞE', 'LAST_NAME': 'GÜLTEKİN', 'STUDENT_ID': '2630112' + last4,
                   'TEST_FORM_CODE': 'B' if with_booklet else ''}


def resample(img, dpi):
    f = dpi / DPI
    return cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)


def rotate(img, ang, scale=1.0, fill=235):
    h, w = img.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, scale)
    c, s = abs(M[0, 0]), abs(M[0, 1])
    W, Hh = int(h * s + w * c) + 30, int(h * c + w * s) + 30
    M[0, 2] += W / 2 - w / 2; M[1, 2] += Hh / 2 - h / 2
    return cv2.warpAffine(img, M, (W, Hh), borderValue=fill)


def perspective(img, k=0.03):
    h, w = img.shape
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[w * k, 0], [w * (1 - k / 2), h * k], [w, h], [0, h * (1 - k)]])
    return cv2.warpPerspective(img, cv2.getPerspectiveTransform(src, dst), (w, h), borderValue=235)


def shadow(img, strength=0.5):
    h, w = img.shape
    xx = np.linspace(0, 1, w)[None, :]
    yy = np.linspace(0, 1, h)[:, None]
    g = 1 - strength * np.clip(1 - (xx * 1.6 + yy * 0.4), 0, 1)
    return np.clip(img * g, 0, 255).astype(np.uint8)


def jpeg(img, q):
    ok, enc = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q])
    return cv2.imdecode(enc, cv2.IMREAD_GRAYSCALE)


def streaks(img):
    out = img.copy(); h, w = out.shape
    for _ in range(3):
        x = rng.randrange(int(w * 0.1), int(w * 0.9))
        out[:, x:x + rng.randrange(2, 4)] = rng.randrange(60, 130)
    noise = nrng.random(out.shape) < 0.0015
    out[noise] = 30
    return out


def noise(img, s=12):
    return np.clip(img + nrng.normal(0, s, img.shape), 0, 255).astype(np.uint8)


SCENARIOS = [
    ('temiz_300dpi', lambda im: im),
    ('200dpi_2derece_%98', lambda im: rotate(resample(im, 200), 2.0, 0.98)),
    ('150dpi_bulanik_jpeg35', lambda im: jpeg(cv2.GaussianBlur(resample(im, 150), (3, 3), 0.9), 35)),
    ('golge_%55_200dpi', lambda im: shadow(resample(im, 200), 0.55)),
    ('ters_perspektif', lambda im: perspective(rotate(resample(im, 200), 181.5, 0.96), 0.035)),
    ('tarayici_cizgileri_gurultu', lambda im: noise(streaks(resample(im, 200)), 10)),
    ('siyah_beyaz_tarama', lambda im: cv2.threshold(resample(im, 200), 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]),
    ('kose_isareti_karalanmis', None),
    ('soluk_dusuk_kontrast', lambda im: np.clip(110 + resample(im, 200) * 0.55, 0, 255).astype(np.uint8)),
    ('fotokopi_gri_zemin', lambda im: noise(np.clip(resample(im, 200) * 0.82 + 15, 0, 255).astype(np.uint8), 14)),
]


def scratch_marker(im, L):
    out = resample(im, 200)
    k = 200 / 25.4
    for pos in ('TR', 'BL'):
        c = next(m for m in L['markers'] if m['position'] == pos)['corners']
        x0, y0 = int(c[0][0] * k), int(c[0][1] * k)
        x1, y1 = int(c[2][0] * k), int(c[2][1] * k)
        cv2.line(out, (x0 - 10, y0 + 5), (x1 + 10, y1 - 5), 0, 5)
        cv2.line(out, (x0, y1), (x1, y0), 0, 4)
    return rotate(out, -1.2)


def evaluate(res, truth, ftruth):
    stats = {'dogru': 0, 'yanlis': 0, 'isaretlendi': 0, 'kacan_cift': 0}
    wrongs = []
    if not res.get('cevaplar'):
        return None, ['OKUNAMADI: ' + '; '.join(res['uyarilar'])], {}
    for qn, (exp, kind) in truth.items():
        got, st = res['cevaplar'][qn], res['durumlar'][qn]
        if kind == 'cift':
            if st == 'çift': stats['dogru'] += 1
            else: stats['kacan_cift'] += 1; wrongs.append(f'S{qn} çift bekleniyordu, okunan {got} ({st})')
        elif kind == 'tik':
            if st in ('zayıf', 'belirsiz', 'boş'):
                stats['isaretlendi'] += 1; stats.setdefault('tur', {}); stats['tur']['tik'] = stats['tur'].get('tik', 0) + 1
            elif got == exp: stats['dogru'] += 1
            else: stats['yanlis'] += 1; wrongs.append(f'S{qn} tik: {exp} → {got}')
        elif got == exp and st in ('tamam', 'boş'):
            stats['dogru'] += 1
        elif got == exp:
            stats['isaretlendi'] += 1          # doğru ama kontrol listesine düştü
            stats.setdefault('tur', {}); stats['tur'][kind] = stats['tur'].get(kind, 0) + 1
        elif st in ('zayıf', 'belirsiz', 'çift'):
            stats['isaretlendi'] += 1; wrongs.append(f'S{qn} {kind}: {exp} → {got} ({st}, işaretlendi)')
        else:
            stats['yanlis'] += 1; wrongs.append(f'S{qn} {kind}: {exp} → {got} ({st})')
    fok = {k: res['alanlar'].get(k, '') == v for k, v in ftruth.items()}
    return stats, wrongs, fok


if __name__ == '__main__':
    import okuyucu
    layouts = okuyucu.load_layouts(FORMS)
    summary = []
    for nq in (50, 75, 100):
        L = json.load(open(os.path.join(FORMS, f'optik_form_{nq}_soru.json'), encoding='utf-8'))
        base = render(nq)
        filled = base.copy()
        truth, ftruth = fill_sheet(filled, L)
        cv2.imwrite(os.path.join(OUT, f'dolu_{nq}.png'), filled)
        for name, fn in SCENARIOS:
            im = scratch_marker(filled, L) if fn is None else fn(filled.copy())
            img_path = os.path.join(OUT, f'tarama_{nq}_{name}.jpg')
            cv2.imwrite(img_path, im, [cv2.IMWRITE_JPEG_QUALITY, 92])
            res = okuyucu.read_sheet(im, layouts, control_path=os.path.join(OUT, f'kontrol_{nq}_{name}.jpg'))
            st, wr, fok = evaluate(res, truth, ftruth)
            summary.append((nq, name, res.get('isaret_sayisi'), res.get('hizalama_hatasi_mm'), st, fok, wr, res.get('alanlar')))
            print(nq, name, res.get('isaret_sayisi'), st, fok, wr[:4])
    json.dump([list(map(lambda x: x if not isinstance(x, dict) else x, s)) for s in summary],
              open(os.path.join(OUT, 'ozet.json'), 'w'), ensure_ascii=False, indent=1, default=str)
