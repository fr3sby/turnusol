"""Bir sınavın okunması, puanlanması ve çıktılarının üretilmesi (GUI ve komut satırı bunu kullanır)."""
import os
from collections import Counter
from dataclasses import dataclass, field

from . import girdi, okuma, obs, yerlesim
from .puanlama import CevapAnahtari, PuanAyari, puanla


LISTEDE_YOK = 'Bu numara sınıf listesinde yok.'


@dataclass
class Oturum:
    kayit: dict = field(default_factory=yerlesim.yukle)
    ayar: okuma.Ayarlar = field(default_factory=okuma.Ayarlar)
    kagitlar: list = field(default_factory=list)        # öğrenci kâğıtları
    anahtar_kagitlari: list = field(default_factory=list)
    anahtar: CevapAnahtari = field(default_factory=CevapAnahtari)
    anahtar_uyarilari: list = field(default_factory=list)
    puan_ayari: PuanAyari = field(default_factory=PuanAyari)
    sinif_listesi: obs.SinifListesi = None
    sablon: obs.NotSablonu = None

    # ---------- okuma ----------
    def tara(self, yollar, ilerleme=None):
        """Dosyaları okur. Numarası tamamen 9 olan kâğıtları (formun anahtar numarası) cevap anahtarı olarak ayırır."""
        toplam = girdi.sayfa_sayisi(yollar) if ilerleme else 0
        for i, (yol, sayfa, gri) in enumerate(girdi.sayfalar(yollar)):
            k = okuma.oku(gri, self.kayit, kaynak=yol, sayfa=sayfa, ayar=self.ayar)
            if k.form is not None and k.ogrenci_no == k.form.anahtar_numarasi:
                self.anahtar_kagitlari.append(k)
                self._anahtar_kagidi_ekle(k)
            else:
                self.kagitlar.append(k)
            if ilerleme:
                if ilerleme(i + 1, max(toplam, i + 1), k) is False:
                    break
        return self

    def _anahtar_kagidi_ekle(self, k):
        a, uy = CevapAnahtari.kagittan(k)
        kit = k.kitapcik
        if kit in self.anahtar.kitapciklar:
            ad = f'{kit} kitapçığı' if kit else 'Sınav'
            self.anahtar_uyarilari.append(f'{ad} için birden fazla anahtar kâğıdı okundu. Program son okunan kâğıdı kullandı ({os.path.basename(k.kaynak)} dosyasının {k.sayfa}. sayfası).')
        self.anahtar.kitapciklar[kit] = a
        self.anahtar_uyarilari += uy

    def anahtar_metinle(self, kitapcik, metin, soru_sayisi=None):
        self.anahtar.kitapciklar[kitapcik] = CevapAnahtari.metinden(metin, soru_sayisi)

    # ---------- listeler ----------
    def sinif_listesi_yukle(self, yol):
        self.sinif_listesi = obs.sinif_listesi_oku(yol)

    def sablon_yukle(self, yol):
        self.sablon = obs.sablon_oku(yol)

    def ogrenci_bilgisi(self, no):
        """(ad, soyad, kaynak) — önce sınıf listesi, sonra şablon."""
        for kaynak in (self.sinif_listesi.ogrenciler if self.sinif_listesi else [],
                       self.sablon.ogrenciler if self.sablon else []):
            for o in kaynak:
                if o.no == no:
                    return o.ad, o.soyad, 'liste'
        return None

    # ---------- sonuçlar ----------
    def sonuclar(self):
        satirlar = []
        sayac = Counter(k.ogrenci_no for k in self.kagitlar if not k.okunamadi)
        liste_nolari = set()
        if self.sinif_listesi:
            liste_nolari |= {o.no for o in self.sinif_listesi.ogrenciler}
        if self.sablon:
            liste_nolari |= set(self.sablon.satirlar)
        for k in self.kagitlar:
            s = {'kagit': k, 'no': k.ogrenci_no, 'ad': k.alan('FIRST_NAME'), 'soyad': k.alan('LAST_NAME'),
                 'ad_kaynagi': 'kâğıt', 'kitapcik': k.kitapcik, 'notlar': []}
            bilgi = self.ogrenci_bilgisi(k.ogrenci_no)
            if bilgi:
                s['ad'], s['soyad'], s['ad_kaynagi'] = bilgi
            elif liste_nolari and not k.okunamadi:
                s['notlar'].append(LISTEDE_YOK)
            if not k.okunamadi and sayac[k.ogrenci_no] > 1:
                s['notlar'].append('Bu numarayla birden fazla kâğıt okundu.')
            if k.okunamadi:
                s['puan'] = None
                s['notlar'].append('Kâğıt okunamadı.')
            else:
                p = puanla(k, self.anahtar, self.puan_ayari) if self.anahtar.kitapciklar else None
                s['puanlama'] = p
                if p and p['hata']:
                    s['notlar'].append(p['hata'])
                s['puan'] = p['puan'] if p and not p['hata'] else None
            s['notlar'] += [u['mesaj'] for u in k.kontrol_listesi]
            s['kontrol'] = bool(s['notlar']) and not k.onaylandi
            satirlar.append(s)
        return satirlar

    def girmeyenler(self):
        """Listede olup kâğıdı olmayan öğrenciler."""
        okunan = {k.ogrenci_no for k in self.kagitlar}
        kaynak = self.sinif_listesi.ogrenciler if self.sinif_listesi else (self.sablon.ogrenciler if self.sablon else [])
        return [o for o in kaynak if o.no not in okunan]

    def sablonda_olmayan_liste_ogrencileri(self):
        if not (self.sinif_listesi and self.sablon):
            return []
        return [o for o in self.sinif_listesi.ogrenciler if o.no not in self.sablon.satirlar]

    def sablona_yaz(self, sinav_sutunu, cikti_yolu, ustune_yaz=False):
        notlar = {}
        for s in self.sonuclar():
            if s['puan'] is not None and s['no'] and '?' not in s['no']:
                notlar[s['no']] = s['puan']
        return obs.sablon_doldur(self.sablon, sinav_sutunu, notlar, cikti_yolu, ustune_yaz)

    def excel_yaz(self, yol):
        from .rapor import excel_raporu
        return excel_raporu(self, yol)
