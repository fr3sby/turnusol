"""Sade Excel raporu (az renk, düz tablolar)."""
import os
from collections import Counter

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from .oturum import LISTEDE_YOK

BASLIK = PatternFill('solid', fgColor='DDDDDD')
DOGRU = PatternFill('solid', fgColor='E2F0D9')
YANLIS = PatternFill('solid', fgColor='F8D7D3')
KONTROL = PatternFill('solid', fgColor='FFF2CC')
KALIN = Font(bold=True)


def _tablo(ws, basliklar, satirlar, genislik=None):
    ws.append(basliklar)
    for c in range(1, len(basliklar) + 1):
        ws.cell(1, c).fill = BASLIK; ws.cell(1, c).font = KALIN
    for r in satirlar:
        ws.append(r)
    ws.freeze_panes = 'A2'
    for i, b in enumerate(basliklar, 1):
        w = (genislik or {}).get(b) or max([len(str(b))] + [len(str(r[i - 1])) for r in satirlar
                                                             if i - 1 < len(r) and r[i - 1] is not None])
        ws.column_dimensions[get_column_letter(i)].width = min(max(6, w + 2), 60)


def excel_raporu(oturum, yol):
    wb = Workbook()
    sonuc = oturum.sonuclar()
    sirali = sorted(sonuc, key=lambda s: (s['no'] or 'zzz'))

    # 1) Sonuçlar
    ws = wb.active; ws.title = 'Sonuçlar'
    rows = []
    for i, s in enumerate(sirali, 1):
        p = s.get('puanlama') or {}
        rows.append([i, s['no'], s['ad'], s['soyad'], s['kitapcik'] or '',
                     p.get('dogru'), p.get('yanlis'), p.get('bos'), s['puan'],
                     'Kontrol' if s['kontrol'] else '', '; '.join(s['notlar']),
                     f"{os.path.basename(s['kagit'].kaynak)} s.{s['kagit'].sayfa}"])
    _tablo(ws, ['Sıra', 'Öğrenci No', 'Ad', 'Soyad', 'Kitapçık', 'Doğru', 'Yanlış', 'Boş', 'Puan',
                'Durum', 'Açıklama', 'Kaynak'], rows, {'Açıklama': 50})
    for r in range(2, ws.max_row + 1):
        ws.cell(r, 2).number_format = '@'
        if ws.cell(r, 10).value:
            for c in range(1, 13):
                ws.cell(r, c).fill = KONTROL

    # 2) Cevaplar
    ws = wb.create_sheet('Cevaplar')
    nmax = max([s['kagit'].form.soru_sayisi for s in sonuc if s['kagit'].form] or [0])
    sorular = oturum.anahtar.sinav_sorulari() or list(range(1, nmax + 1))
    rows = []
    for s in sirali:
        k = s['kagit']
        rows.append([s['no'], s['kitapcik'] or ''] + [k.cevap(q) if not k.okunamadi else '' for q in sorular])
    _tablo(ws, ['Öğrenci No', 'Kitapçık'] + [str(q) for q in sorular], rows)
    for i, s in enumerate(sirali, 2):
        det = (s.get('puanlama') or {}).get('detay', {})
        for j, q in enumerate(sorular, 3):
            ws.column_dimensions[get_column_letter(j)].width = 4
            d = det.get(q)
            if d:
                ws.cell(i, j).fill = DOGRU if d[0] == 'doğru' else (YANLIS if d[0] in ('yanlış', 'çift') else PatternFill())
            ws.cell(i, j).alignment = Alignment(horizontal='center')

    # 3) Soru analizi
    ws = wb.create_sheet('Soru Analizi')
    rows = []
    gecerli = [s for s in sonuc if s.get('puanlama') and not s['puanlama']['hata']]
    for q in sorular:
        dagilim = Counter(s['kagit'].cevap(q) for s in gecerli)
        n = len(gecerli) or 1
        dogru = sum(1 for s in gecerli if s['puanlama']['detay'].get(q, ('',))[0] == 'doğru')
        anahtarlar = ' / '.join(f"{kit or 'Tek'}:{a.get(q, '')}" for kit, a in sorted(oturum.anahtar.kitapciklar.items()))
        rows.append([q, anahtarlar, 'İptal' if q in oturum.anahtar.iptal else '',
                     round(100 * dogru / n), round(100 * dagilim.get('', 0) / n)] +
                    [dagilim.get(c, 0) for c in 'ABCDE'] + [sum(v for c, v in dagilim.items() if '+' in c)])
    _tablo(ws, ['Soru', 'Anahtar', 'Durum', 'Doğru %', 'Boş %', 'A', 'B', 'C', 'D', 'E', 'Çift'], rows)

    # 4) Kontrol listesi
    ws = wb.create_sheet('Kontrol Listesi')
    rows = []
    for s in sirali:
        for n in s['notlar']:
            rows.append([s['no'], f"{s['ad']} {s['soyad']}".strip(),
                         f"{os.path.basename(s['kagit'].kaynak)} s.{s['kagit'].sayfa}", n])
    for u in oturum.anahtar_uyarilari:
        rows.append(['ANAHTAR', '', '', u])
    _tablo(ws, ['Öğrenci No', 'Ad Soyad', 'Kaynak', 'Açıklama'], rows, {'Açıklama': 60})

    # 5) Liste karşılaştırma
    ws = wb.create_sheet('Liste Karşılaştırma')
    rows = [['Sınav kâğıdı yok', o.no, o.ad, o.soyad, o.aciklama] for o in oturum.girmeyenler()]
    rows += [['Listede var, not şablonunda yok', o.no, o.ad, o.soyad, o.aciklama]
             for o in oturum.sablonda_olmayan_liste_ogrencileri()]
    rows += [['Kâğıt var, listede yok', s['no'], s['ad'], s['soyad'], '']
             for s in sirali if LISTEDE_YOK in s['notlar']]
    _tablo(ws, ['Durum', 'Öğrenci No', 'Ad', 'Soyad', 'Açıklama'], rows)
    for r in range(2, ws.max_row + 1):
        ws.cell(r, 2).number_format = '@'

    # 6) Anahtar ve ayarlar
    ws = wb.create_sheet('Anahtar ve Ayarlar')
    pa = oturum.puan_ayari
    rows = [[f"Kitapçık {kit or '(tek)'}", ' '.join(f'{q}{v or "-"}' for q, v in sorted(a.items()))]
            for kit, a in sorted(oturum.anahtar.kitapciklar.items())]
    rows += [['İptal edilen sorular', ', '.join(map(str, sorted(oturum.anahtar.iptal))) or 'İptal edilen soru yok'],
             ['Toplam puan', pa.toplam], ['Özel puanlar', pa.ozel_puanlar or 'Her soru eşit puan'],
             ['Yanlış doğruyu götürür', f'{pa.yanlis_goturur} yanlış bir doğruyu götürür' if pa.yanlis_goturur else 'Yanlışlar doğruyu götürmez'],
             ['İptal edilen soru', 'Herkese doğru sayılır' if pa.iptal_politikasi == 'herkese_dogru' else 'Puanı diğer sorulara dağıtılır'],
             ['Yuvarlama', 'Not tam sayıya yuvarlanır' if pa.yuvarla else 'Not yuvarlanmaz']]
    _tablo(ws, ['Ayar', 'Değer'], rows, {'Değer': 80})
    wb.save(yol)
    return yol
