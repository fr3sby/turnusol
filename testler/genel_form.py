"""Ön baskısız (genel) formları uydurma öğrencilerle doldurur, bozar ve okur."""
import os, sys, random, subprocess
import cv2
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK); sys.path.insert(0, os.path.dirname(__file__))
import simulasyon as S
from turnusol import yerlesim, okuma

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
rng = random.Random(3); S.rng = rng
L = yerlesim.yukle()
BOZ = [f for _, f in S.SCENARIOS if f is not None]
hata = toplam = 0
for nq in (50, 75, 100):
    form = next(y for y in L.values() if y.form == f'{nq}q' and y.surum == 'genel')
    lay = form.veri
    p = os.path.join(OUT, f'bos_{nq}')
    subprocess.run(['pdftoppm', '-gray', '-png', '-r', '300', '-singlefile',
                    os.path.join(KOK, 'turnusol', 'formlar', f'optik_form_{nq}_soru_genel.pdf'), p], check=True)
    bos = cv2.imread(p + '.png', cv2.IMREAD_GRAYSCALE)
    for i in range(12):
        no = '99999999999' if i == 0 else str(rng.randint(10 ** (rng.choice([5, 8, 9, 10]) - 1), 10 ** 10))
        cev = {q: rng.choice('ABCDE') for q in range(1, nq + 1) if rng.random() < 0.9}
        img = bos.copy()
        cols = lay['fields']['STUDENT_ID']['columns']
        for k, d in enumerate(no):
            S.pencil(img, cols[k][int(d)], 'tam')
        for q in lay['questions']:
            if q['number'] in cev:
                S.pencil(img, {o['value']: o for o in q['options']}[cev[q['number']]], 'tam')
        img = BOZ[i % len(BOZ)](img)
        k = okuma.oku(img, L)
        toplam += 1
        sorun = []
        if k.form is not form: sorun.append(f'form {k.form}')
        if k.ogrenci_no != no: sorun.append(f'no {k.ogrenci_no} != {no}')
        yanlis = [q for q in range(1, nq + 1) if k.cevap(q) != cev.get(q, '')]
        if yanlis: sorun.append(f'{len(yanlis)} soru hatalı')
        if sorun:
            hata += 1
        print(nq, i, no, 'anahtar' if no == form.anahtar_numarasi else '', f'kontrast={k.kontrast}', 'uyarı=%d' % len(k.kontrol_listesi), sorun or 'tamam')
print(f'{toplam} kâğıttan {hata} tanesinde hata var.')
