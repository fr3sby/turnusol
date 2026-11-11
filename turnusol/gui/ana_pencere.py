"""Ana pencere: üst kabuk, adım çubuğu, sayfalar, durum çubuğu, menüler."""
from PySide6.QtCore import Qt
import os
from PySide6.QtGui import QAction, QKeySequence, QPixmap
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QStackedWidget,
                               QScrollArea, QMessageBox)

from .. import __version__
from .baglam import Baglam
from .ortak import AdimCubugu, dugme
from .kilavuz import Kilavuz
from .hakkinda import Hakkinda
from .formlar import FormlarPenceresi, sablonu_kaydet
from .sayfa_tarama import TaramaSayfasi
from .sayfa_anahtar import AnahtarSayfasi
from .sayfa_puan import PuanSayfasi
from .sayfa_kontrol import KontrolSayfasi
from .sayfa_disari import DisariSayfasi

ADIMLAR = ['Taramalar', 'Cevap Anahtarı', 'Puanlama', 'Kontrol', 'Dışa Aktar']


def _kaydir(w):
    s = QScrollArea(); s.setWidget(w); s.setWidgetResizable(True); s.setFrameShape(QFrame.NoFrame)
    return s


class AnaPencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Turnusol')
        self.resize(1360, 860); self.setMinimumSize(1100, 700)
        self.b = Baglam()
        self.kilavuz = Kilavuz(self)

        merkez = QWidget(); lay = QVBoxLayout(merkez); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        # üst kabuk
        kabuk = QFrame(); kabuk.setObjectName('kabuk'); kabuk.setFixedHeight(48)
        kl = QHBoxLayout(kabuk); kl.setContentsMargins(16, 0, 0, 0); kl.setSpacing(0)
        logo = QLabel(); logo.setPixmap(QPixmap(os.path.join(os.path.dirname(__file__), 'ikonlar', 'serit.png')).scaled(
            40, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        kl.addWidget(logo); kl.addSpacing(8)
        bas = QLabel('Turnusol  <span style="color:#a8a8a8">Optik Form Okuyucu</span>'); bas.setObjectName('kabukBaslik')
        kl.addWidget(bas); kl.addStretch(1)
        f = dugme('Boş formlar', 'kabukDugme', ipucu='Boş optik formları yazdırır ya da PDF olarak kaydeder.')
        f.clicked.connect(self.formlari_ac); kl.addWidget(f)
        k = dugme('Kılavuz', 'kabukDugme', ipucu='F1'); k.clicked.connect(lambda: self.kilavuz.ac())
        kl.addWidget(k)
        lay.addWidget(kabuk)

        self.adim = AdimCubugu(ADIMLAR); self.adim.secildi.connect(self.git)
        lay.addWidget(self.adim)

        self.yigin = QStackedWidget()
        self.sayfalar = [TaramaSayfasi(self.b), AnahtarSayfasi(self.b), PuanSayfasi(self.b),
                         KontrolSayfasi(self.b), DisariSayfasi(self.b)]
        for i, s in enumerate(self.sayfalar):
            self.yigin.addWidget(s if i == 3 else _kaydir(s))
        lay.addWidget(self.yigin, 1)
        self.setCentralWidget(merkez)

        self.durum = QLabel(''); self.statusBar().addWidget(self.durum, 1)
        self.statusBar().addPermanentWidget(QLabel(f'v{__version__}'))

        self.b.kilavuz_ac.connect(self.kilavuz.ac)
        self.b.adima_git.connect(self.git)
        self.b.degisti.connect(self.adimlari_guncelle)
        self._menuler()
        self.git(0); self.adimlari_guncelle()

    def _menuler(self):
        m = self.menuBar()
        dosya = m.addMenu('Dosya')
        a = QAction('Taramaları ekle…', self); a.setShortcut(QKeySequence.Open)
        a.triggered.connect(lambda: (self.git(0), self.sayfalar[0].alan.mousePressEvent(None))); dosya.addAction(a)
        dosya.addSeparator()
        bf = QAction('Boş optik formlar…', self); bf.setShortcut('Ctrl+P'); bf.triggered.connect(self.formlari_ac); dosya.addAction(bf)
        sb = QAction('Excel öğrenci listesi şablonunu kaydet…', self); sb.triggered.connect(lambda: sablonu_kaydet(self))
        dosya.addAction(sb)
        dosya.addSeparator()
        c = QAction('Çıkış', self); c.setShortcut(QKeySequence.Quit); c.triggered.connect(self.close); dosya.addAction(c)
        gor = m.addMenu('Git')
        for i, ad in enumerate(ADIMLAR):
            g = QAction(f'{i + 1}. {ad}', self); g.setShortcut(f'Ctrl+{i + 1}'); g.triggered.connect(lambda _=False, j=i: self.git(j))
            gor.addAction(g)
        yardim = m.addMenu('Yardım')
        y = QAction('Kılavuz', self); y.setShortcut(QKeySequence.HelpContents); y.triggered.connect(lambda: self.kilavuz.ac())
        yardim.addAction(y)
        h = QAction('Hakkında', self); h.triggered.connect(self._hakkinda); yardim.addAction(h)

    def _hakkinda(self):
        Hakkinda(self).exec()

    def formlari_ac(self):
        if not hasattr(self, '_formlar'):
            self._formlar = FormlarPenceresi(self)
        self._formlar.show(); self._formlar.raise_(); self._formlar.activateWindow()

    def git(self, i):
        self.yigin.setCurrentIndex(i); self.adim.sec(i)

    def adimlari_guncelle(self, *_):
        o = self.b.oturum
        s = o.sonuclar() if o.kagitlar else []
        n_k = sum(1 for x in s if x['kontrol'])
        oku = len(o.kagitlar)
        self.adim.ayarla(0, f'{oku} kâğıt okundu.' if oku else 'Taramaları ekleyin.', tamam=oku > 0,
                         uyari=any(k.okunamadi for k in o.kagitlar))
        kits = o.anahtar.kitapcik_listesi()
        dolu = bool(o.anahtar.sinav_sorulari())
        n_s = len(o.anahtar.sinav_sorulari())
        self.adim.ayarla(1, ((f'{len(kits)} kitapçık için {n_s} soruluk anahtar var.' if len(kits) > 1 else f'{n_s} soruluk anahtar girildi.')
                             if dolu else 'Anahtar henüz girilmedi.'),
                         tamam=dolu, uyari=bool(oku and not dolu))
        p = o.puan_ayari
        self.adim.ayarla(2, f'Toplam puan {p.toplam:g}' + (f', {p.yanlis_goturur} yanlış bir doğruyu götürür.' if p.yanlis_goturur else '.'), tamam=dolu)
        self.adim.ayarla(3, (f'{n_k} kâğıt kontrol bekliyor.' if n_k else 'Kontrol bekleyen kâğıt yok.') if oku else 'Önce taramaları okutun.',
                         tamam=bool(oku and not n_k), uyari=n_k > 0)
        self.adim.ayarla(4, 'Not şablonu yüklendi.' if o.sablon else 'Notları ve raporu kaydedin.', tamam=False)
        parca = []
        if o.sinif_listesi: parca.append(f'Sınıf listesinde {len(o.sinif_listesi.ogrenciler)} öğrenci var.')
        if o.sablon: parca.append(f'Not şablonunda {len(o.sablon.satirlar)} öğrenci var.')
        if oku: parca.append(f'{oku} kâğıt okundu ve {n_k} kâğıt kontrol bekliyor.' if n_k else f'{oku} kâğıt okundu.')
        self.durum.setText('  '.join(parca) or 'Başlamak için taramaları ekleyin.')
