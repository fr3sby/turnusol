"""Komut satırı: python -m turnusol TARAMA... [seçenekler]

Örnek:
  python -m turnusol taramalar.pdf --liste "Sınıf Listesi.XLS" --sablon Sablon.xlsx --sutun S1 --cikti sonuc
  python -m turnusol taramalar/ --anahtar ABCDABCDAB... --toplam 100 --yanlis 4 --iptal 7,12
"""
import argparse
import os
import sys

from .oturum import Oturum
from .puanlama import PuanAyari
from . import girdi, okuma


def main(argv=None):
    p = argparse.ArgumentParser(prog='turnusol', description='Turnusol optik form okuyucu')
    p.add_argument('taramalar', nargs='+', help='PDF, resim ya da klasör')
    p.add_argument('--anahtar', action='append', default=[],
                   help='Cevap anahtarı metni. Kitapçıklı: A=ABCD... (birden çok verilebilir). '
                        'Verilmezse taramadaki anahtar kâğıdı (numaranın doldurulabilen bütün hanelerinde 9 olan kâğıt) kullanılır.')
    p.add_argument('--liste', help='OBS sınıf listesi (.XLS/.xlsx)')
    p.add_argument('--sablon', help='OBS not şablonu (.xlsx)')
    p.add_argument('--sutun', help='Notun yazılacağı şablon sütunu (ör. S1)')
    p.add_argument('--ustune-yaz', action='store_true', help='Şablonda dolu notların üstüne yaz')
    p.add_argument('--toplam', type=float, default=100)
    p.add_argument('--ozel', default='', help='Özel puanlar, ör. "1-5:4; 6-40:2"')
    p.add_argument('--yanlis', type=int, default=0, help='Kaç yanlış bir doğruyu götürür (0: kapalı)')
    p.add_argument('--iptal', default='', help='İptal edilen sorular, ör. 7,12')
    p.add_argument('--iptal-politika', choices=['herkese_dogru', 'dagit'], default='herkese_dogru')
    p.add_argument('--yuvarlama-yok', action='store_true')
    p.add_argument('--cikti', default='turnusol_sonuc', help='Çıktı klasörü')
    p.add_argument('--kontrol-goruntuleri', action='store_true', help='Her kâğıt için kontrol görüntüsü kaydet')
    a = p.parse_args(argv)

    os.makedirs(a.cikti, exist_ok=True)
    o = Oturum()
    o.puan_ayari = PuanAyari(toplam=a.toplam, ozel_puanlar=a.ozel, yanlis_goturur=a.yanlis,
                             iptal_politikasi=a.iptal_politika, yuvarla=not a.yuvarlama_yok)
    if a.liste:
        o.sinif_listesi_yukle(a.liste)
    if a.sablon:
        o.sablon_yukle(a.sablon)

    def ilerle(i, n, k):
        print(f'\r{n} sayfanın {i} tanesi okundu.', end='', file=sys.stderr)
    o.tara(a.taramalar, ilerleme=ilerle)
    print(file=sys.stderr)
    for metin in a.anahtar:
        kit, _, m = metin.partition('=') if '=' in metin[:3] else ('', '', metin)
        o.anahtar_metinle(kit.strip().upper(), m)
    if a.iptal:
        o.anahtar.iptal = {int(x) for x in a.iptal.replace(' ', '').split(',') if x}
    if not o.anahtar.kitapciklar:
        print('UYARI: Cevap anahtarı verilmediği ve taramada anahtar kâğıdı bulunmadığı için program puan hesaplamadı.', file=sys.stderr)

    rapor = o.excel_yaz(os.path.join(a.cikti, 'sonuclar.xlsx'))
    print(f'Excel raporu {rapor} dosyasına kaydedildi.')
    if a.sablon and a.sutun:
        yol = os.path.join(a.cikti, os.path.splitext(os.path.basename(a.sablon))[0] + f'_{a.sutun}_dolu.xlsx')
        r = o.sablona_yaz(a.sutun, yol, a.ustune_yaz)
        print(f'Program {r["yazilan"]} öğrencinin notunu {yol} dosyasına yazdı. Şablonda bulunmayan {len(r["sablonda_yok"])} numara, '
              f'kâğıdı olmayan {len(r["notu_olmayan"])} öğrenci ve zaten notu olduğu için atlanan {len(r["dolu_atlanan"])} öğrenci var.')
    if a.kontrol_goruntuleri:
        import cv2
        kd = os.path.join(a.cikti, 'kontrol'); os.makedirs(kd, exist_ok=True)
        hepsi = {(k.kaynak, k.sayfa): k for k in o.kagitlar + o.anahtar_kagitlari}
        for yol, sayfa, gri in girdi.sayfalar(a.taramalar):
            k = hepsi.get((yol, sayfa))
            if k:
                ad = f'{os.path.splitext(os.path.basename(yol))[0]}_s{sayfa}_{k.ogrenci_no or "okunamadi"}.jpg'
                ok, buf = cv2.imencode('.jpg', okuma.kontrol_goruntusu(gri, k), [cv2.IMWRITE_JPEG_QUALITY, 85])
                buf.tofile(os.path.join(kd, ad))
    s = o.sonuclar()
    print(f'Program {len(s)} öğrenci kâğıdı ve {len(o.anahtar_kagitlari)} anahtar kâğıdı okudu. '
          f'{sum(1 for x in s if x["kontrol"])} kâğıt kontrol gerektiriyor.')


if __name__ == '__main__':
    main()
