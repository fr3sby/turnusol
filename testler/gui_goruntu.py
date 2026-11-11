"""Arayüzün ekran görüntülerini (offscreen) üretir. Uydurma test verisiyle.
Kullanım: QT_QPA_PLATFORM=offscreen python3 testler/gui_goruntu.py VERI_KLASORU CIKTI_KLASORU"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from turnusol.gui.tema import uygula
from turnusol.gui.ana_pencere import AnaPencere

VERI, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
app = QApplication(sys.argv); uygula(app)
w = AnaPencere(); w.resize(1440, 900); w.show(); app.processEvents()


def cek(ad, widget=None):
    for _ in range(5): app.processEvents()
    (widget or w).grab().save(os.path.join(OUT, ad + '.png'))
    print('kaydedildi', ad)


cek('0_bos')
b = w.b
w.sayfalar[0].ekle([os.path.join(VERI, 'tarama.pdf')])
w.sayfalar[0].liste_kutu._yukle(os.path.join(VERI, 'Sınıf Listesi.XLS'))
w.sayfalar[0].sablon_kutu._yukle(os.path.join(VERI, 'Sablon.xlsx'))
b.oturum.tara(b.taranacaklar)
w.sayfalar[0]._bitti('')
cek('1_taramalar')
w.git(1); cek('2_anahtar')
w.git(2); p = w.sayfalar[2]; p.yanlis.setChecked(True); cek('3_puanlama')
p.yanlis.setChecked(False)
w.git(3); k = w.sayfalar[3]; k.yenile(); app.processEvents()
# çift işaretli bir kâğıt seç ve uyarıya odaklan
if k.uyarilar.count():
    k.uyarilar.setCurrentRow(0); k._uyari_sec(k.uyarilar.item(0))
cek('4_kontrol')
k.gor.sigdir(); cek('4b_kontrol_tam')
w.git(4); cek('5_disari')
w.kilavuz.resize(1000, 720); w.kilavuz.ac('obs'); cek('6_kilavuz_obs', w.kilavuz)
w.kilavuz.ac('kontrol'); cek('7_kilavuz_kontrol', w.kilavuz)
w.formlari_ac(); f = w._formlar; f.resize(1000, 760); f.liste.setCurrentRow(1); f._goster(); cek('8_bos_formlar', f)
from turnusol.gui.hakkinda import Hakkinda
h = Hakkinda(w); h.show(); cek('9_hakkinda', h)
