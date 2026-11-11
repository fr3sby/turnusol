"""Form yerleşimleri (sürümlü).

Her form sürümü `yerlesimler/<sürüm>/` altında JSON olarak durur. Formlar işaret
(ArUco) numaralarıyla tanınır; yeni bir form sürümü yeni numaralar alır, eski
sürümlerin JSON'ları silinmez. Böylece eski basılmış formlar okunmaya devam eder.

İşaret numarası düzeni (DICT_4X4 ailesi; okuma 4X4_1000 ile yapılır, ilk 50'si 4X4_50 ile aynı):
  v1    (Bozok, numaranın ilk 7 hanesi basılı): 50 soru → 0–7, 75 soru → 8–15, 100 soru → 16–23
  genel (ön baskısız numara alanı):           50 soru → 24–31, 75 soru → 32–39, 100 soru → 40–47
"""
import glob
import json
import os
from dataclasses import dataclass, field

KLASOR = os.path.join(os.path.dirname(__file__), 'yerlesimler')


@dataclass
class Yerlesim:
    surum: str
    form: str                 # '50q', '75q', '100q'
    soru_sayisi: int
    veri: dict = field(repr=False)

    @property
    def isaretler(self):
        return {m['id']: m for m in self.veri['markers']}

    @property
    def alanlar(self):
        return self.veri['fields']

    @property
    def sorular(self):
        return self.veri['questions']

    @property
    def anahtar_numarasi(self):
        return self.veri.get('key_student_id', '')

    @property
    def onek(self):
        return self.veri['fields'].get('STUDENT_ID', {}).get('preprinted_prefix', '')

    @property
    def ad(self):
        return f'{self.soru_sayisi} soruluk form ({self.surum})'


def yukle(klasor=KLASOR):
    """İşaret numarası → Yerlesim sözlüğü döndürür."""
    kayit = {}
    for yol in sorted(glob.glob(os.path.join(klasor, '*', '*.json'))):
        surum = os.path.basename(os.path.dirname(yol))
        with open(yol, encoding='utf-8') as f:
            veri = json.load(f)
        y = Yerlesim(surum=surum, form=veri['form'], soru_sayisi=veri['num_questions'], veri=veri)
        for m in veri['markers']:
            if m['id'] in kayit:
                raise ValueError(f'İşaret numarası {m["id"]} iki yerleşimde birden kullanılmış ({yol})')
            kayit[m['id']] = y
    return kayit
