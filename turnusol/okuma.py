"""Optik form okuma: ArUco işaretleri → homografi → daire koyulukları → karar.

Kararlar:
  tamam    : tek şık açıkça işaretli
  zayıf    : en koyu şık eşiğin altında ama boş değil (hafif işaret, tik vb.) → kontrol
  belirsiz : ikinci şık da kayda değer koyu (eksik silme vb.) → kontrol
  çift     : iki şık da işaretli → kontrol (puanlamada yanlış sayılır)
  boş      : işaret yok
"""
from dataclasses import dataclass, field
import numpy as np
import cv2

from . import yerlesim as _y

_SOZLUK = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_1000)
_PARAM = cv2.aruco.DetectorParameters()
_PARAM.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
_DEDEKTOR = cv2.aruco.ArucoDetector(_SOZLUK, _PARAM)


@dataclass
class Ayarlar:
    t_isaret: float = 0.28        # kontrast 0.80 iken işaretli sayılma eşiği
    t_zayif: float = 0.13         # bunun altı boş
    oran_cift: float = 0.55       # ikinci/birinci oranı bunun üstündeyse çift/belirsiz
    referans_kontrast: float = 0.80
    min_isaret: int = 4
    max_hizalama_mm: float = 0.8
    ornekleme_orani: float = 0.68  # dairenin iç kısmı (yarıçap oranı)


DURUM_KONTROL = ('zayıf', 'belirsiz', 'çift')


@dataclass
class Kagit:
    kaynak: str
    sayfa: int
    form: object = None                  # Yerlesim
    isaret_sayisi: int = 0
    hizalama_hatasi_mm: float = None
    kontrast: float = None
    okunamadi: bool = False
    uyarilar: list = field(default_factory=list)   # {'tur','hedef','mesaj'}
    alanlar: dict = field(default_factory=dict)    # FIRST_NAME, LAST_NAME, STUDENT_ID, TEST_FORM_CODE
    alan_durumlari: dict = field(default_factory=dict)
    alan_sutunlari: dict = field(default_factory=dict)   # ad → okunan karakterler (sütun sütun)
    cevaplar: dict = field(default_factory=dict)   # soru → 'A' | '' | 'A+C'
    durumlar: dict = field(default_factory=dict)   # soru → durum
    skorlar: dict = field(default_factory=dict)    # anahtar → [koyuluk farkı]
    konumlar: dict = field(default_factory=dict)   # anahtar → [(x,y) px]
    yaricap_px: float = 0.0
    H: list = None
    elle_cevaplar: dict = field(default_factory=dict)
    elle_alanlar: dict = field(default_factory=dict)     # ad → tam metin (elle yazılmış)
    elle_sutunlar: dict = field(default_factory=dict)    # (ad, sütun) → karakter ('' = boş)
    onaylandi: bool = False              # kontrol ekranında hoca onayladı

    # --- elle düzeltmelerle birlikte nihai değerler ---
    def cevap(self, soru):
        return self.elle_cevaplar.get(soru, self.cevaplar.get(soru, ''))

    def alan(self, ad):
        if ad in self.elle_alanlar:
            return self.elle_alanlar[ad]
        if any(k[0] == ad for k in self.elle_sutunlar) and ad in self.alan_sutunlari:
            harf = list(self.alan_sutunlari[ad])
            for (a, ci), v in self.elle_sutunlar.items():
                if a == ad:
                    harf[ci] = v if v else (' ' if self.form.alanlar[ad]['type'] == 'letter' else '?')
            s = ''.join(harf)
            return ' '.join(s.split()) if self.form.alanlar[ad]['type'] == 'letter' else _sayi(s, self.form.alanlar[ad])
        return self.alanlar.get(ad, '')

    def sutun_degeri(self, ad, ci):
        if (ad, ci) in self.elle_sutunlar:
            return self.elle_sutunlar[(ad, ci)]
        v = self.alan_sutunlari.get(ad, [''])[ci] if ad in self.alan_sutunlari else ''
        return '' if v in (' ', '?') else v

    @property
    def ogrenci_no(self):
        return self.alan('STUDENT_ID')

    @property
    def kitapcik(self):
        return self.alan('TEST_FORM_CODE').strip()

    @property
    def kontrol_listesi(self):
        """Elle düzeltilmemiş kontrol gerektiren maddeler."""
        out = []
        for u in self.uyarilar:
            if u['tur'] == 'soru' and u['hedef'] in self.elle_cevaplar:
                continue
            if u['tur'] == 'alan' and (u['hedef'][0] in self.elle_alanlar or u['hedef'] in self.elle_sutunlar):
                continue
            if u['tur'] == 'alan' and u['hedef'][1] is None and u['hedef'][0] == 'STUDENT_ID':
                no = self.ogrenci_no
                if no and '?' not in no and '*' not in no:
                    continue
            out.append(u)
        return out


def normalize(gri):
    """Gölge/arka plan düzeltme: görüntüyü kendi bulanık arka planına böl."""
    h, w = gri.shape
    k = max(31, (min(h, w) // 25) | 1)
    k = min(k, 255)
    kk = max(3, (k // 3) | 1)
    bg = cv2.morphologyEx(gri, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kk, kk)))
    bg = cv2.medianBlur(bg, k)
    return cv2.divide(gri, bg, scale=255)


def isaretleri_bul(gri, kayit):
    bulunan = {}
    for img in (gri, cv2.equalizeHist(gri), normalize(gri)):
        koseler, ids, _ = _DEDEKTOR.detectMarkers(img)
        if ids is not None:
            for c, i in zip(koseler, ids.flatten()):
                bulunan.setdefault(int(i), c[0])
    oylar = {}
    for i in bulunan:
        if i in kayit:
            y = kayit[i]
            oylar[id(y)] = (oylar.get(id(y), (0, y))[0] + 1, y)
    if not oylar:
        return None, {}
    _, form = max(oylar.values(), key=lambda t: t[0])
    return form, {i: c for i, c in bulunan.items() if kayit.get(i) is form}


def _homografi(form, bulunan):
    mm = form.isaretler
    src, dst = [], []
    for i, c in bulunan.items():
        src += mm[i]['corners']; dst += c.tolist()
    src, dst = np.float32(src), np.float32(dst)
    H, _ = cv2.findHomography(src, dst, cv2.RANSAC, 6.0)
    if H is None:
        return None, 99.0, 1.0
    proj = cv2.perspectiveTransform(src[None], H)[0]
    ppm = float(np.sqrt(abs(np.linalg.det(H[:2, :2]))))
    hata = float(np.median(np.linalg.norm(proj - dst, axis=1)) / max(ppm, 1e-6))
    return H, hata, ppm


def _sayi(s, alan):
    """Sayı alanının metni. Uzunluğu değişken alanlarda (genel form) sağdaki boş sütunlar atılır."""
    return s.rstrip('?') if alan.get('variable_length') else s


def _koyuluklar(norm, H, daireler, ppm, oran):
    pts = np.float32([[b['x'], b['y']] for b in daireler])[None]
    P = cv2.perspectiveTransform(pts, H)[0]
    out = []
    h, w = norm.shape
    for (x, y), b in zip(P, daireler):
        rr = max(2, int(b['r'] * ppm * oran))
        xi, yi = int(round(x)), int(round(y))
        if xi - rr < 0 or yi - rr < 0 or xi + rr >= w or yi + rr >= h:
            out.append(0.0); continue
        patch = norm[yi - rr:yi + rr + 1, xi - rr:xi + rr + 1]
        yy, xx = np.mgrid[-rr:rr + 1, -rr:rr + 1]
        mask = xx * xx + yy * yy <= rr * rr
        out.append(1.0 - float(patch[mask].mean()) / 255.0)
    return out, [(float(a), float(b)) for a, b in P]


def karar(skorlar, t_isaret, t_zayif, oran):
    sira = np.argsort(skorlar)[::-1]
    s1 = skorlar[sira[0]]
    s2 = skorlar[sira[1]] if len(skorlar) > 1 else 0.0
    if s1 < t_zayif:
        return None, 'boş'
    if s1 < t_isaret:
        return [int(sira[0])], 'zayıf'
    if s2 >= t_isaret and s2 >= oran * s1:
        return sorted([int(sira[0]), int(sira[1])]), 'çift'
    if s2 >= t_zayif and s2 >= oran * s1:
        return [int(sira[0])], 'belirsiz'
    return [int(sira[0])], 'tamam'


def oku(gri, kayit, kaynak='', sayfa=1, ayar=None):
    ayar = ayar or Ayarlar()
    k = Kagit(kaynak=kaynak, sayfa=sayfa)
    form, bulunan = isaretleri_bul(gri, kayit)
    if form is None:
        k.okunamadi = True
        k.uyarilar.append({'tur': 'kagit', 'hedef': None, 'mesaj': 'Program kâğıttaki hizalama işaretlerini bulamadığı için formu tanıyamadı.'})
        return k
    k.form = form
    k.isaret_sayisi = len(bulunan)
    if len(bulunan) < 2:
        k.okunamadi = True
        k.uyarilar.append({'tur': 'kagit', 'hedef': None, 'mesaj': f'Program yalnızca {len(bulunan)} hizalama işareti bulduğu için kâğıdı okuyamadı.'})
        return k
    if len(bulunan) < ayar.min_isaret:
        k.uyarilar.append({'tur': 'kagit', 'hedef': None, 'mesaj': f'Program yalnızca {len(bulunan)} hizalama işareti buldu. Okunan şıkların doğru yerde olup olmadığını kontrol edin.'})
    H, hata, ppm = _homografi(form, bulunan)
    if H is None:
        k.okunamadi = True
        k.uyarilar.append({'tur': 'kagit', 'hedef': None, 'mesaj': 'Program sayfayı hizalayamadı.'})
        return k
    k.H = H.tolist(); k.hizalama_hatasi_mm = round(hata, 3); k.yaricap_px = ppm
    if hata > ayar.max_hizalama_mm:
        k.uyarilar.append({'tur': 'kagit', 'hedef': None, 'mesaj': f'Sayfa tam olarak hizalanamadı ({hata:.2f} mm sapma var). Okunan şıkları kontrol edin.'})

    norm = normalize(gri)
    ham = {}
    for ad, f in form.alanlar.items():
        for ci, sutun in enumerate(f['columns']):
            ham[('alan', ad, ci)] = _koyuluklar(norm, H, sutun, ppm, ayar.ornekleme_orani)
    for q in form.sorular:
        ham[('soru', q['number'])] = _koyuluklar(norm, H, q['options'], ppm, ayar.ornekleme_orani)
    tum = [v for d, _ in ham.values() for v in d]
    taban = float(np.percentile(tum, 40))

    # kontrast referansı: önbasılı dolu daireler
    onek = form.onek
    refs = [ham[('alan', 'STUDENT_ID', i)][0][int(d)] for i, d in enumerate(onek)]
    if not refs and form.veri.get('contrast_refs'):
        # genel formda önbasılı numara yok; açıklamalardaki dolu örnek daire kullanılır
        refs = _koyuluklar(norm, H, form.veri['contrast_refs'], ppm, ayar.ornekleme_orani)[0]
    kontrast = (float(np.median(refs)) - taban) if refs else ayar.referans_kontrast
    k.kontrast = round(kontrast, 3)
    olcek = float(np.clip(kontrast / ayar.referans_kontrast, 0.45, 1.15))
    t_is, t_za = ayar.t_isaret * olcek, ayar.t_zayif * olcek
    if kontrast < 0.45:
        k.uyarilar.append({'tur': 'kagit', 'hedef': None, 'mesaj': 'Tarama çok soluk olduğu için hafif işaretler gözden kaçmış olabilir.'})

    # alanlar
    for ad, f in form.alanlar.items():
        karakterler, durumlar = [], []
        for ci, sutun in enumerate(f['columns']):
            d, P = ham[('alan', ad, ci)]
            tb = taban
            if len(d) >= 8:
                med = float(np.median(d))
                if med - taban > t_za * 0.5:
                    k.uyarilar.append({'tur': 'alan', 'hedef': (ad, ci), 'mesaj': f'{_ALAN_IN[ad]} {ci + 1}. sütununda bir çizgi ya da leke olabilir.'})
                tb = max(taban, med)
            sk = [x - tb for x in d]
            k.skorlar[('alan', ad, ci)] = sk; k.konumlar[('alan', ad, ci)] = P
            v, st = karar(sk, t_is, t_za, ayar.oran_cift)
            durumlar.append(st)
            if st == 'boş':
                karakterler.append(' ' if f['type'] == 'letter' else '?')
            elif st == 'çift':
                karakterler.append('*')
            else:
                karakterler.append(sutun[v[0]]['value'])
            if st in DURUM_KONTROL:
                k.uyarilar.append({'tur': 'alan', 'hedef': (ad, ci), 'mesaj': _alan_mesaji(ad, ci, st)})
        s = ''.join(karakterler)
        k.alan_sutunlari[ad] = karakterler
        k.alanlar[ad] = ' '.join(s.split()) if f['type'] == 'letter' else _sayi(s, f)
        k.alan_durumlari[ad] = durumlar
    sid = k.alanlar.get('STUDENT_ID', '')
    if '?' in sid or '*' in sid:
        k.uyarilar.append({'tur': 'alan', 'hedef': ('STUDENT_ID', None), 'mesaj': f'Öğrenci numarası eksik ya da hatalı okundu ({sid}).'})

    # sorular
    for q in form.sorular:
        n = q['number']
        d, P = ham[('soru', n)]
        sk = [x - taban for x in d]
        k.skorlar[('soru', n)] = sk; k.konumlar[('soru', n)] = P
        v, st = karar(sk, t_is, t_za, ayar.oran_cift)
        if st == 'boş':
            k.cevaplar[n] = ''
        else:
            k.cevaplar[n] = '+'.join(q['options'][i]['value'] for i in v)
        k.durumlar[n] = st
        if st in DURUM_KONTROL:
            k.uyarilar.append({'tur': 'soru', 'hedef': n, 'mesaj': _soru_mesaji(n, st, k.cevaplar[n])})
    return k


_ALAN_AD = {'FIRST_NAME': 'Ad', 'LAST_NAME': 'Soyad', 'STUDENT_ID': 'Öğrenci numarası', 'TEST_FORM_CODE': 'Kitapçık türü'}
_ALAN_IN = {'FIRST_NAME': 'Adın', 'LAST_NAME': 'Soyadın', 'STUDENT_ID': 'Öğrenci numarasının', 'TEST_FORM_CODE': 'Kitapçık türünün'}


def _ve(degerler):
    d = [x for x in degerler if x]
    return ' ve '.join(d) if len(d) <= 2 else ', '.join(d[:-1]) + ' ve ' + d[-1]


def _alan_mesaji(ad, ci, st):
    yer = f'{_ALAN_IN[ad]} {ci + 1}. sütunu'
    if st == 'zayıf':
        return f'{_ALAN_IN[ad]} {ci + 1}. sütunundaki işaret çok hafif.'
    if st == 'belirsiz':
        return f'{_ALAN_IN[ad]} {ci + 1}. sütununda ikinci bir şık da koyu görünüyor.'
    return f'{_ALAN_IN[ad]} {ci + 1}. sütununda iki şık işaretlenmiş.'


def _soru_mesaji(n, st, cevap):
    if st == 'zayıf':
        return f'{n}. sorudaki işaret çok hafif ({cevap} şıkkı).'
    if st == 'belirsiz':
        return f'{n}. soruda {cevap} şıkkının yanında başka bir şık da koyu görünüyor.'
    return f'{n}. soruda iki şık işaretlenmiş ({_ve(cevap.split("+"))}).'


def duzlestirme(k, ppm=None):
    """Taranmış görüntüyü formun düz (A4, dik) hâline çeviren dönüşüm.
    Dönüş: (M 3x3 görüntü→düz piksel, (genişlik, yükseklik), düz görüntüde mm başına piksel) ya da None."""
    if k.okunamadi or k.form is None or k.H is None:
        return None
    ppm = ppm or min(max(k.yaricap_px, 4.0), 10.0)
    gw, gy = k.form.veri['page_mm']
    S = np.array([[ppm, 0, 0], [0, ppm, 0], [0, 0, 1]], dtype=np.float64)
    M = S @ np.linalg.inv(np.array(k.H, dtype=np.float64))
    return M, (int(round(gw * ppm)), int(round(gy * ppm))), ppm


def duz_goruntu(gri, k, ppm=None):
    """(düz gri görüntü, düz konumlar sözlüğü, mm başına piksel). Düzleştirilemezse özgün hâli döner."""
    d = duzlestirme(k, ppm)
    if d is None:
        return gri, dict(k.konumlar), (k.yaricap_px or 4.0)
    M, (w, h), p = d
    img = cv2.warpPerspective(gri, M, (w, h), flags=cv2.INTER_AREA, borderValue=255)
    konum = {}
    for anahtar, P in k.konumlar.items():
        Q = cv2.perspectiveTransform(np.float32(P)[None], M)[0]
        konum[anahtar] = [(float(x), float(y)) for x, y in Q]
    return img, konum, p


def kontrol_goruntusu(gri, k, duz=True):
    """Okunanların renkli işaretlendiği BGR görüntü. duz=True ise kâğıt dik ve düz hâle getirilir.
    yeşil: okunan, turuncu: şüpheli, kırmızı: çift, mor: elle düzeltilmiş."""
    if k.okunamadi or k.form is None:
        return cv2.cvtColor(gri, cv2.COLOR_GRAY2BGR)
    if duz:
        gri, konumlar, ppm = duz_goruntu(gri, k)
    else:
        konumlar, ppm = k.konumlar, k.yaricap_px
    img = cv2.cvtColor(gri, cv2.COLOR_GRAY2BGR)
    kal = max(2, int(ppm * 0.35))
    def halka(p, renk):
        cv2.circle(img, (int(p[0]), int(p[1])), int(2.3 * ppm), renk, kal)
    renk = {'tamam': (0, 160, 0), 'zayıf': (0, 140, 255), 'belirsiz': (0, 140, 255), 'çift': (0, 0, 255)}
    for q in k.form.sorular:
        n = q['number']; P = konumlar[('soru', n)]
        degerler = [o['value'] for o in q['options']]
        if n in k.elle_cevaplar:
            for v in k.elle_cevaplar[n].split('+'):
                if v in degerler: halka(P[degerler.index(v)], (200, 0, 200))
            continue
        st = k.durumlar[n]
        if st == 'boş': continue
        for v in k.cevaplar[n].split('+'):
            halka(P[degerler.index(v)], renk[st])
    for ad, f in k.form.alanlar.items():
        for ci, sutun in enumerate(f['columns']):
            if (ad, ci) in k.elle_sutunlar:
                v = k.elle_sutunlar[(ad, ci)]; vals = [b['value'] for b in sutun]
                if v in vals: halka(konumlar[('alan', ad, ci)][vals.index(v)], (200, 0, 200))
                continue
            st = k.alan_durumlari[ad][ci]
            if st == 'boş': continue
            sk = k.skorlar[('alan', ad, ci)]; P = konumlar[('alan', ad, ci)]
            sira = np.argsort(sk)[::-1][:2 if st == 'çift' else 1]
            for i in sira:
                halka(P[i], renk[st])
    return img
    ppm = k.yaricap_px
    kal = max(2, int(ppm * 0.35))
    def halka(p, renk):
        cv2.circle(img, (int(p[0]), int(p[1])), int(2.3 * ppm), renk, kal)
    renk = {'tamam': (0, 160, 0), 'zayıf': (0, 140, 255), 'belirsiz': (0, 140, 255), 'çift': (0, 0, 255)}
    for q in k.form.sorular:
        n = q['number']; P = k.konumlar[('soru', n)]
        degerler = [o['value'] for o in q['options']]
        if n in k.elle_cevaplar:
            for v in k.elle_cevaplar[n].split('+'):
                if v in degerler: halka(P[degerler.index(v)], (200, 0, 200))
            continue
        st = k.durumlar[n]
        if st == 'boş': continue
        for v in k.cevaplar[n].split('+'):
            halka(P[degerler.index(v)], renk[st])
    for ad, f in k.form.alanlar.items():
        for ci, sutun in enumerate(f['columns']):
            st = k.alan_durumlari[ad][ci]
            if st == 'boş': continue
            sk = k.skorlar[('alan', ad, ci)]; P = k.konumlar[('alan', ad, ci)]
            sira = np.argsort(sk)[::-1][:2 if st == 'çift' else 1]
            for i in sira:
                halka(P[i], renk[st])
    return img
