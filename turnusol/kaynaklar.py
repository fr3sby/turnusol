"""Programla birlikte gelen dosyalar: boş optik formlar ve Excel şablonu."""
import os

KOK = os.path.dirname(os.path.abspath(__file__))
FORM_KLASORU = os.path.join(KOK, 'formlar')
SABLON = os.path.join(KOK, 'sablonlar', 'ogrenci_listesi_sablonu.xlsx')

# (dosya, grup, başlık, açıklama)
FORMLAR = [
    ('optik_form_50_soru_genel.pdf', 'Genel formlar', '50 soruluk genel form',
     'Öğrenci numarası alanı boştur. Öğrenci numarasını en soldaki kutudan başlayarak kodlar. Her kurumda kullanılabilir.'),
    ('optik_form_75_soru_genel.pdf', 'Genel formlar', '75 soruluk genel form',
     'Öğrenci numarası alanı boştur. Öğrenci numarasını en soldaki kutudan başlayarak kodlar. Her kurumda kullanılabilir.'),
    ('optik_form_100_soru_genel.pdf', 'Genel formlar', '100 soruluk genel form',
     'Öğrenci numarası alanı boştur. Öğrenci numarasını en soldaki kutudan başlayarak kodlar. Her kurumda kullanılabilir.'),
    ('optik_form_50_soru.pdf', 'Yozgat Bozok Üniversitesi formları', '50 soruluk form (2630112)',
     'Numaranın ilk yedi hanesi (2630112) formda basılıdır. Öğrenci yalnızca son dört haneyi kodlar.'),
    ('optik_form_75_soru.pdf', 'Yozgat Bozok Üniversitesi formları', '75 soruluk form (2630112)',
     'Numaranın ilk yedi hanesi (2630112) formda basılıdır. Öğrenci yalnızca son dört haneyi kodlar.'),
    ('optik_form_100_soru.pdf', 'Yozgat Bozok Üniversitesi formları', '100 soruluk form (2630112)',
     'Numaranın ilk yedi hanesi (2630112) formda basılıdır. Öğrenci yalnızca son dört haneyi kodlar.'),
]


def form_yolu(dosya):
    return os.path.join(FORM_KLASORU, dosya)
