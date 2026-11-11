"""Cevap anahtarı ve puanlama.

- Her kitapçık (A, B, …) için ayrı anahtar; kitapçık kullanılmıyorsa anahtar '' adıyla tutulur.
- Anahtarı boş bırakılan sorular sınavda yok sayılır (ör. 50'lik formda 40 soru).
- Bir soru için birden fazla doğru şık kabul edilebilir ("A/B" gibi).
- Puanlar: varsayılan toplam/sınavdaki soru sayısı; aralığa göre özel puan ("1-5:4; 6-40:2").
- Yanlış doğruyu götürür: k yanlış = 1 doğru (her yanlış, o sorunun puanının 1/k'sını düşürür).
- İptal edilen soru: 'herkese_dogru' ya da 'dagit' (puanı kalan sorulara orantılı dağıtılır).
- Not tam sayıya yuvarlanır (yarım yukarı), 0'ın altına inmez.
"""
import math
import re
from dataclasses import dataclass, field


@dataclass
class CevapAnahtari:
    kitapciklar: dict = field(default_factory=dict)   # kitapçık → {soru: 'A' | 'A/B'}
    iptal: set = field(default_factory=set)
    soru_sayisi: int = 0      # 0 ise sınır yok; verilirse bu sayıdan sonraki sorular puanlanmaz (anahtar silinmez)

    def _sinirla(self, a):
        if a is None or not self.soru_sayisi:
            return a
        return {q: v for q, v in a.items() if q <= self.soru_sayisi}

    def kitapcik_listesi(self):
        return sorted(self.kitapciklar)

    def anahtar(self, kitapcik):
        """Öğrencinin kitapçığına göre anahtar. Kitapçık kullanılmıyorsa tek anahtar."""
        if kitapcik in self.kitapciklar:
            return self._sinirla(self.kitapciklar[kitapcik])
        if len(self.kitapciklar) == 1:
            return self._sinirla(next(iter(self.kitapciklar.values())))
        return None

    def sinav_sorulari(self, kitapcik=None):
        """Anahtarı dolu sorular (sınavda var sayılanlar)."""
        kaynak = [self.anahtar(kitapcik)] if kitapcik is not None else [self._sinirla(a) for a in self.kitapciklar.values()]
        sorular = set()
        for a in kaynak:
            if a:
                sorular |= {q for q, v in a.items() if v}
        return sorted(sorular)

    @staticmethod
    def metinden(metin, soru_sayisi=None):
        """'ABCDE…' ya da '1A 2B 3C' / 'A,B,C' biçimlerini çözer. Boş soru için '-' ya da '_'."""
        metin = metin.strip().upper()
        sonuc = {}
        if re.search(r'\d', metin):
            for no, deger in re.findall(r'(\d+)\s*[\.\-:)]?\s*([A-F/]+|-|_)', metin):
                sonuc[int(no)] = '' if deger in '-_' else deger
        else:
            harfler = [c for c in re.sub(r'[\s,;]', '', metin)]
            for i, c in enumerate(harfler):
                sonuc[i + 1] = '' if c in '-_' else c
        if soru_sayisi:
            sonuc = {q: v for q, v in sonuc.items() if q <= soru_sayisi}
        return sonuc

    @staticmethod
    def kagittan(kagit):
        """Taranmış anahtar kâğıdından {soru: cevap}; uyarılar listesiyle birlikte."""
        uyarilar = []
        a = {}
        for q, v in sorted(kagit.cevaplar.items()):
            v = kagit.cevap(q)
            if '+' in v:
                uyarilar.append(f'Anahtar kâğıdında {q}. soruda birden fazla şık işaretlenmiş ({v.replace("+", " ve ")}). Program bu şıkların hepsini doğru kabul etti.')
                v = v.replace('+', '/')
            a[q] = v
        for u in kagit.kontrol_listesi:
            if u['tur'] == 'soru':
                uyarilar.append('Anahtar kâğıdında bir sorun var: ' + u['mesaj'])
        return a, uyarilar


def araliklari_coz(metin):
    """'1-5:4; 6-40:2; 41:3' → {soru: puan}"""
    sonuc = {}
    if not metin:
        return sonuc
    for parca in re.split(r'[;\n]+', metin):
        parca = parca.strip()
        if not parca:
            continue
        m = re.fullmatch(r'(\d+)\s*(?:-\s*(\d+))?\s*[:=]\s*([\d.,]+)', parca)
        if not m:
            raise ValueError(f'"{parca}" ifadesi anlaşılamadı. Puanları 1-5:4; 6-40:2 biçiminde yazın.')
        a, b, p = int(m.group(1)), int(m.group(2) or m.group(1)), float(m.group(3).replace(',', '.'))
        for q in range(min(a, b), max(a, b) + 1):
            sonuc[q] = p
    return sonuc


@dataclass
class PuanAyari:
    toplam: float = 100.0
    ozel_puanlar: str = ''               # '1-5:4; 6-40:2'
    yanlis_goturur: int = 0              # 0: kapalı; 4: dört yanlış bir doğruyu götürür
    iptal_politikasi: str = 'herkese_dogru'   # ya da 'dagit'
    yuvarla: bool = True


def soru_puanlari(sorular, iptal, ayar):
    """Sınavdaki sorular için {soru: puan}."""
    ozel = araliklari_coz(ayar.ozel_puanlar)
    belirtilen = {q: ozel[q] for q in sorular if q in ozel}
    kalan = [q for q in sorular if q not in belirtilen]
    puan = dict(belirtilen)
    if kalan:
        artan = ayar.toplam - sum(belirtilen.values())
        if artan < 0:
            raise ValueError('Girdiğiniz özel puanların toplamı, toplam puandan fazla.')
        for q in kalan:
            puan[q] = artan / len(kalan)
    if ayar.iptal_politikasi == 'dagit' and iptal:
        iptal_toplam = sum(puan[q] for q in sorular if q in iptal)
        kalan_toplam = sum(puan[q] for q in sorular if q not in iptal)
        if kalan_toplam > 0:
            k = (kalan_toplam + iptal_toplam) / kalan_toplam
            puan = {q: (0.0 if q in iptal else p * k) for q, p in puan.items()}
    return puan


def yuvarla(x):
    return int(math.floor(x + 0.5))


def puanla(kagit, anahtar: CevapAnahtari, ayar: PuanAyari):
    """Bir kâğıdı puanlar. Dönüş sözlüğü: dogru, yanlis, bos, cift, iptal, ham, puan, detay, hata."""
    sonuc = {'dogru': 0, 'yanlis': 0, 'bos': 0, 'cift': 0, 'iptal': 0, 'ham': 0.0, 'puan': None,
             'detay': {}, 'hata': None}
    kit = kagit.kitapcik
    a = anahtar.anahtar(kit)
    if a is None:
        sonuc['hata'] = (f'{kit} kitapçığı için cevap anahtarı girilmemiş.' if kit else
                         'Öğrenci kitapçık türünü kodlamamış, ancak sınavda birden fazla kitapçık var.')
        return sonuc
    sorular = sorted(q for q, v in a.items() if v)
    puanlar = soru_puanlari(sorular, anahtar.iptal, ayar)
    toplam = 0.0
    for q in sorular:
        p = puanlar[q]
        verilen = kagit.cevap(q)
        dogrular = set(a[q].split('/'))
        if q in anahtar.iptal:
            sonuc['iptal'] += 1
            kazanc = p if ayar.iptal_politikasi == 'herkese_dogru' else 0.0
            sonuc['detay'][q] = ('iptal', verilen, kazanc)
            toplam += kazanc
            continue
        if not verilen:
            sonuc['bos'] += 1; sonuc['detay'][q] = ('boş', verilen, 0.0)
        elif '+' in verilen:
            sonuc['cift'] += 1; sonuc['yanlis'] += 1
            ceza = -p / ayar.yanlis_goturur if ayar.yanlis_goturur else 0.0
            sonuc['detay'][q] = ('çift', verilen, ceza); toplam += ceza
        elif verilen in dogrular:
            sonuc['dogru'] += 1; sonuc['detay'][q] = ('doğru', verilen, p); toplam += p
        else:
            sonuc['yanlis'] += 1
            ceza = -p / ayar.yanlis_goturur if ayar.yanlis_goturur else 0.0
            sonuc['detay'][q] = ('yanlış', verilen, ceza); toplam += ceza
    toplam = max(0.0, toplam)
    sonuc['ham'] = round(toplam, 4)
    sonuc['puan'] = yuvarla(toplam) if ayar.yuvarla else round(toplam, 2)
    return sonuc
