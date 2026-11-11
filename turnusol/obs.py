"""OBS dosyaları: sınıf listesi (.XLS/.xlsx) okuma ve not şablonu (.xlsx) doldurma."""
import os
import re
from dataclasses import dataclass, field


def _norm(s):
    s = str(s or '').strip()
    tablo = str.maketrans('İIıŞşĞğÜüÖöÇç', 'iiissgguuoocc')
    return re.sub(r'\s+', ' ', s.translate(tablo).lower())


def _no(v):
    """Öğrenci numarasını metne çevirir (sayı olarak gelmiş olabilir: 26301121068.0)."""
    if v is None:
        return ''
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return re.sub(r'\D', '', str(v).strip())


def _satirlar(yol):
    """Dosyadaki ilk sayfanın satırlarını değer listeleri olarak döndürür."""
    uz = os.path.splitext(yol)[1].lower()
    if uz == '.xls':
        import xlrd
        sh = xlrd.open_workbook(yol, logfile=open(os.devnull, 'w')).sheet_by_index(0)
        return [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]
    import openpyxl
    wb = openpyxl.load_workbook(yol, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    return rows


@dataclass
class Ogrenci:
    no: str
    ad: str
    soyad: str
    aciklama: str = ''


@dataclass
class SinifListesi:
    ders: str = ''
    ogretim_elemani: str = ''
    ogrenciler: list = field(default_factory=list)

    def sozluk(self):
        return {o.no: o for o in self.ogrenciler}


_BASLIK_NO = ('ogrenci no', 'ogrencino_studentno', 'ogrenci numarasi', 'numara', 'student no')
_BASLIK_AD = ('adi', 'ad', 'ad_name', 'name')
_BASLIK_SOYAD = ('soyadi', 'soyad', 'soyad_surname', 'surname')


def sinif_listesi_oku(yol):
    """OBS 'Sınıf Listesi' (.XLS) ya da benzeri bir tabloyu okur. Not şablonu da sınıf listesi olarak verilebilir."""
    rows = _satirlar(yol)
    obs_listesi = os.path.splitext(yol)[1].lower() == '.xls'
    sl = SinifListesi()
    baslik = None
    for i, r in enumerate(rows):
        hucreler = [_norm(c) for c in r]
        if any(h in _BASLIK_NO for h in hucreler):
            baslik = i
            break
        # üst bilgi satırları
        dolu = [str(c).strip() for c in r if str(c or '').strip()]
        if dolu and _norm(dolu[0]).startswith('ders kodu'):
            sl.ders = dolu[-1]
        if dolu and _norm(dolu[0]).startswith('ogretim uyesi'):
            sl.ogretim_elemani = dolu[-1]
    if baslik is None:
        raise ValueError('Dosyada "Öğrenci No" başlığı bulunamadı. OBS\'den indirilen sınıf listesini ya da programın Excel şablonunu seçin.')
    h = [_norm(c) for c in rows[baslik]]
    def sutun(adlar):
        for j, x in enumerate(h):
            if x in adlar:
                return j
        return None
    c_no, c_ad, c_soyad = sutun(_BASLIK_NO), sutun(_BASLIK_AD), sutun(_BASLIK_SOYAD)
    c_ac = sutun(('aciklama',))
    for r in rows[baslik + 1:]:
        if c_no is None or c_no >= len(r):
            continue
        no = _no(r[c_no])
        # OBS listesinin altındaki sayfa ve toplam satırları kısa sayılar içerir; Excel şablonunda her numara geçerlidir
        if not no or (obs_listesi and len(no) < 5):
            continue
        g = lambda c: str(r[c]).strip() if c is not None and c < len(r) and r[c] is not None else ''
        sl.ogrenciler.append(Ogrenci(no=no, ad=g(c_ad), soyad=g(c_soyad), aciklama=g(c_ac)))
    return sl


@dataclass
class NotSablonu:
    yol: str
    sayfa: str
    baslik_satiri: int
    sutun_no: int
    sinav_sutunlari: dict          # başlık → sütun (1 tabanlı), ör. {'S1': 4, 'S2': 5}
    satirlar: dict                 # öğrenci no → satır (1 tabanlı)
    mevcut: dict                   # (no, başlık) → mevcut değer
    ogrenciler: list               # Ogrenci listesi (şablondaki sırayla)


def sablon_oku(yol):
    import openpyxl
    wb = openpyxl.load_workbook(yol)
    ws = wb.worksheets[0]
    baslik = None
    for r in range(1, min(ws.max_row, 30) + 1):
        degerler = [_norm(ws.cell(r, c).value) for c in range(1, ws.max_column + 1)]
        if any(v in _BASLIK_NO for v in degerler):
            baslik = r
            break
    if baslik is None:
        raise ValueError('Not şablonunda öğrenci numarası başlığı bulunamadı. OBS şablonunda bu başlık OgrenciNo_StudentNo, programın Excel şablonunda ise Öğrenci No olarak yazılır.')
    basliklar = {c: ws.cell(baslik, c).value for c in range(1, ws.max_column + 1)}
    nb = {c: _norm(v) for c, v in basliklar.items()}
    c_no = next(c for c, v in nb.items() if v in _BASLIK_NO)
    c_ad = next((c for c, v in nb.items() if v in _BASLIK_AD), None)
    c_soyad = next((c for c, v in nb.items() if v in _BASLIK_SOYAD), None)
    sinav = {str(basliklar[c]).strip(): c for c in basliklar
             if c not in (c_no, c_ad, c_soyad) and basliklar[c] not in (None, '')}
    satirlar, mevcut, ogr = {}, {}, []
    for r in range(baslik + 1, ws.max_row + 1):
        no = _no(ws.cell(r, c_no).value)
        if not no:
            continue
        satirlar[no] = r
        ogr.append(Ogrenci(no=no, ad=str(ws.cell(r, c_ad).value or '') if c_ad else '',
                           soyad=str(ws.cell(r, c_soyad).value or '') if c_soyad else ''))
        for b, c in sinav.items():
            mevcut[(no, b)] = ws.cell(r, c).value
    return NotSablonu(yol=yol, sayfa=ws.title, baslik_satiri=baslik, sutun_no=c_no,
                      sinav_sutunlari=sinav, satirlar=satirlar, mevcut=mevcut, ogrenciler=ogr)


def sablon_doldur(sablon: NotSablonu, sinav_sutunu, notlar, cikti_yolu, ustune_yaz=False):
    """Şablonu kopyalayıp seçilen sınav sütununa notları yazar.
    notlar: {öğrenci no: tam sayı}. Şablonda olmayan numaralar yazılmaz, raporda döner.
    Dönüş: {'yazilan': n, 'sablonda_yok': [...], 'notu_olmayan': [...], 'dolu_atlanan': [...]}"""
    import openpyxl
    if sinav_sutunu not in sablon.sinav_sutunlari:
        raise ValueError(f'Şablonda "{sinav_sutunu}" sütunu yok. Mevcut: {", ".join(sablon.sinav_sutunlari)}')
    c = sablon.sinav_sutunlari[sinav_sutunu]
    wb = openpyxl.load_workbook(sablon.yol)
    ws = wb[sablon.sayfa]
    rapor = {'yazilan': 0, 'sablonda_yok': [], 'notu_olmayan': [], 'dolu_atlanan': []}
    for no, puan in notlar.items():
        r = sablon.satirlar.get(no)
        if r is None:
            rapor['sablonda_yok'].append(no); continue
        eski = ws.cell(r, c).value
        if eski not in (None, '') and not ustune_yaz:
            rapor['dolu_atlanan'].append(no); continue
        ws.cell(r, c).value = puan
        rapor['yazilan'] += 1
    for no in sablon.satirlar:
        if no not in notlar:
            rapor['notu_olmayan'].append(no)
    wb.save(cikti_yolu)
    return rapor
