"""Uçtan uca test: uydurma sınıf listesi + not şablonu + kitapçıklı anahtar kâğıtları + öğrenci kâğıtları
(farklı tarama bozulmalarıyla tek PDF) → komut satırı → Excel ve şablon çıktısı kontrolü.
Gerçek öğrenci isimleri KULLANILMAZ.
Kullanım: python3 testler/uctan_uca.py CALISMA_KLASORU
"""
import os, sys, random, subprocess, json
import numpy as np
import cv2
from PIL import Image

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK); sys.path.insert(0, os.path.dirname(__file__))
import simulasyon as S
from turnusol import yerlesim
from turnusol.puanlama import CevapAnahtari, PuanAyari, soru_puanlari, yuvarla

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
rng = random.Random(42)
S.rng = rng

ADLAR = ['ELA', 'KEREM', 'DEFNE', 'ARDA', 'MİRA', 'EGE', 'NİSAN', 'ATLAS', 'LİNA', 'ÇINAR', 'İPEK', 'ÖYKÜ',
         'TOPRAK', 'DURU', 'BORA', 'SELİN', 'ALP', 'GÜNEŞ', 'ŞEVVAL', 'UMUT', 'IŞIL', 'ÇAĞAN', 'ASYA', 'DORUK']
SOYADLAR = ['ÖRNEKOĞLU', 'DENEMECİ', 'TESTER', 'KAĞITÇI', 'KALEMCİ', 'SİLGİN', 'ŞIKLI', 'NOKTA',
            'ÇİZGİ', 'DAİRE', 'KUTUCU', 'İŞARET', 'OPTİKÇİ', 'TARAYICI', 'YAZICI', 'ÜÇGEN',
            'KARE', 'DÖRTGEN', 'BEŞGEN', 'ALTIGEN', 'YEDİGÜN', 'SEKİZLİ', 'DOKUZER', 'ONLU']
N = 24
nolar = sorted(rng.sample(range(1000, 9999), N))
ogrenciler = [(f'2630112{n}', ADLAR[i], SOYADLAR[i]) for i, n in enumerate(nolar)]
DISARIDA = ogrenciler[-1]          # kâğıdı var ama listede yok
GIRMEYEN = ogrenciler[-2]          # listede var, kâğıdı yok
SABLONDA_YOK = ogrenciler[-3]      # listede var, şablonda yok (devamsızlık)
liste = [o for o in ogrenciler if o != DISARIDA]
sablon_ogr = [o for o in liste if o != SABLONDA_YOK]
sinava_giren = [o for o in ogrenciler if o != GIRMEYEN]

# --- uydurma sınıf listesi (.XLS, OBS biçimine benzer) ---
import xlwt
wb = xlwt.Workbook(); ws = wb.add_sheet('rptSinifListesi')
ws.write(1, 3, 'DERS ÖĞRENCİ LİSTESİ'); ws.write(2, 0, '2026-2027 Yılı Güz Dönemi')
ws.write(7, 1, 'Ders Kodu ve Adı'); ws.write(7, 5, ':'); ws.write(7, 6, 'FTR999.1.0 - DENEME DERSİ')
ws.write(9, 1, 'Öğretim Üyesi / Görevlisi'); ws.write(9, 5, ':'); ws.write(9, 6, 'Öğr. Gör. DENEME HOCA')
for c, v in [(1, 'No'), (2, 'Öğrenci No'), (4, 'Adı'), (7, 'Soyadı'), (8, 'Açıklama')]:
    ws.write(13, c, v)
for i, (no, ad, soyad) in enumerate(liste):
    ws.write(14 + i, 1, i + 1); ws.write(14 + i, 2, no); ws.write(14 + i, 4, ad); ws.write(14 + i, 7, soyad)
liste_yol = os.path.join(OUT, 'Sınıf Listesi.XLS'); wb.save(liste_yol)

# --- uydurma not şablonu (.xlsx, OBS biçimi; S1 dolu) ---
import openpyxl
wb2 = openpyxl.Workbook(); w2 = wb2.active; w2.title = 'Ogrenciler'
w2.append(['OgrenciNo_StudentNo', 'Ad_Name', 'Soyad_Surname', 'S1', 'S2'])
for no, ad, soyad in sablon_ogr:
    w2.append([no, ad, soyad, rng.randint(30, 95), None])
sablon_yol = os.path.join(OUT, 'Sablon.xlsx'); wb2.save(sablon_yol)

# --- anahtar: 40 soru, A ve B kitapçığı ---
SORU = 40
anahtar = {k: {q: rng.choice('ABCDE') for q in range(1, SORU + 1)} for k in 'AB'}

L = yerlesim.yukle()
form = next(y for y in L.values() if y.form == '50q')
FORMS = os.path.join(KOK, 'formlar')
S.FORMS, S.OUT = FORMS, OUT
bos = S.render(50)
lay = form.veri


def doldur(img, no, ad, soyad, kit, cevaplar, kipler):
    def alan(key, text):
        cols = lay['fields'][key]['columns']
        for ci, ch in enumerate(text[:len(cols)]):
            if ch == ' ':
                continue
            for b in cols[ci]:
                if b['value'] == ch:
                    S.pencil(img, b, 'tam')
    alan('FIRST_NAME', ad); alan('LAST_NAME', soyad)
    cols = lay['fields']['STUDENT_ID']['columns']
    for k, d in enumerate(no[7:]):
        S.pencil(img, cols[7 + k][int(d)], 'tam')
    if kit:
        S.pencil(img, lay['fields']['TEST_FORM_CODE']['columns'][0]['ABCDEF'.index(kit)], 'tam')
    for q in lay['questions']:
        n = q['number']; v = cevaplar.get(n, ''); kip = kipler.get(n, 'tam')
        if not v:
            continue
        opts = {o['value']: o for o in q['options']}
        if '+' in v:
            for x in v.split('+'): S.pencil(img, opts[x], 'tam')
        elif kip == 'silinip':
            eski = rng.choice([c for c in 'ABCDE' if c != v])
            S.pencil(img, opts[eski], 'silik'); S.pencil(img, opts[v], 'tam')
        else:
            S.pencil(img, opts[v], kip)


BOZ = [f for _, f in S.SCENARIOS if f is not None and _ not in ('temiz_300dpi',)]
sayfalar, beklenen = [], {}
# anahtar kâğıtları
for kit in 'AB':
    img = bos.copy()
    doldur(img, '26301129999', '', '', kit, anahtar[kit], {})
    sayfalar.append(S.resample(img, 200))
for i, (no, ad, soyad) in enumerate(sinava_giren):
    kit = 'AB'[i % 2]
    cev, kip = {}, {}
    for q in range(1, SORU + 1):
        r = rng.random()
        dogru = anahtar[kit][q]
        if r < 0.62: cev[q] = dogru
        elif r < 0.86: cev[q] = rng.choice([c for c in 'ABCDE' if c != dogru])
        elif r < 0.95: cev[q] = ''
        else:
            a, b = rng.sample('ABCDE', 2); cev[q] = '+'.join(sorted([a, b]))
        if cev[q] and '+' not in cev[q]:
            kip[q] = rng.choice(['tam'] * 6 + ['kismi', 'silinip'])
    img = bos.copy()
    doldur(img, no, ad, soyad, kit, cev, kip)
    f = BOZ[i % len(BOZ)]
    sayfalar.append(f(img))
    beklenen[no] = (kit, cev)

pdf_yol = os.path.join(OUT, 'tarama.pdf')
pil = []
for s in sayfalar:
    im = Image.fromarray(s)
    pil.append(im)
pil[0].save(pdf_yol, save_all=True, append_images=pil[1:], resolution=200)
rng.shuffle(sayfalar)


def beklenen_puan(kit, cev, ayar, iptal=set()):
    a = anahtar[kit]
    sorular = sorted(a)
    P = soru_puanlari(sorular, iptal, ayar)
    t = 0.0
    for q in sorular:
        if q in iptal:
            t += P[q] if ayar.iptal_politikasi == 'herkese_dogru' else 0; continue
        v = cev.get(q, '')
        if not v: continue
        if v == a[q]: t += P[q]
        elif ayar.yanlis_goturur: t -= P[q] / ayar.yanlis_goturur
    return yuvarla(max(0, t))


def calistir(ad, args, ayar, iptal=set()):
    cikti = os.path.join(OUT, ad)
    cmd = [sys.executable, '-m', 'turnusol', pdf_yol, '--liste', liste_yol, '--sablon', sablon_yol,
           '--sutun', 'S2', '--cikti', cikti] + args
    r = subprocess.run(cmd, cwd=KOK, capture_output=True, text=True)
    print(r.stdout.strip());
    if r.returncode: print(r.stderr); raise SystemExit(1)
    wb = openpyxl.load_workbook(os.path.join(cikti, 'sonuclar.xlsx'))
    ws = wb['Sonuçlar']
    hd = [c.value for c in ws[1]]
    satir = {str(r[hd.index('Öğrenci No')]): r for r in ws.iter_rows(min_row=2, values_only=True)}
    hatalar = 0
    for no, (kit, cev) in beklenen.items():
        r = satir.get(no)
        bp = beklenen_puan(kit, cev, ayar, iptal)
        if r is None or r[hd.index('Puan')] != bp:
            hatalar += 1
            print('  FARK', no, 'beklenen', bp, 'okunan', None if r is None else r[hd.index('Puan')], r and r[hd.index('Açıklama')])
    # ad/soyad listeden mi?
    for no, ad_, soyad in liste:
        if no in satir and (satir[no][hd.index('Ad')], satir[no][hd.index('Soyad')]) != (ad_, soyad):
            hatalar += 1; print('  AD FARKI', no)
    # şablon
    sb = openpyxl.load_workbook(os.path.join(cikti, 'Sablon_S2_dolu.xlsx')).active
    for row in sb.iter_rows(min_row=2, values_only=True):
        no, s2 = str(row[0]), row[4]
        if no in beklenen:
            bp = beklenen_puan(*beklenen[no], ayar, iptal)
            if s2 != bp: hatalar += 1; print('  ŞABLON FARKI', no, s2, bp)
        elif s2 is not None:
            hatalar += 1; print('  ŞABLONDA GİRMEYENE NOT', no)
    lk = wb['Liste Karşılaştırma']
    durumlar = {(r[0], str(r[1])) for r in lk.iter_rows(min_row=2, values_only=True)}
    for d in [('Sınav kâğıdı yok', GIRMEYEN[0]), ('Listede var, not şablonunda yok', SABLONDA_YOK[0]),
              ('Kâğıt var, listede yok', DISARIDA[0])]:
        if d not in durumlar: hatalar += 1; print('  EKSİK DURUM', d)
    print(f'[{ad}] {len(beklenen)} öğrenci, hata: {hatalar}')
    return hatalar


toplam_hata = 0
toplam_hata += calistir('varsayilan', [], PuanAyari())
toplam_hata += calistir('ozel_yanlis_iptal', ['--ozel', '1-5:4; 6-40:2', '--yanlis', '4', '--iptal', '7',
                                               '--kontrol-goruntuleri'],
                        PuanAyari(ozel_puanlar='1-5:4; 6-40:2', yanlis_goturur=4), iptal={7})
toplam_hata += calistir('iptal_dagit', ['--toplam', '50', '--iptal', '3,9', '--iptal-politika', 'dagit'],
                        PuanAyari(toplam=50, iptal_politikasi='dagit'), iptal={3, 9})
print('TOPLAM HATA:', toplam_hata)
