"""Hakkında penceresi."""
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QWidget

from .. import __version__
from .ortak import etiket, dugme
from .tema import KLASOR

EPOSTA = 'S.bugrahan.yinanc@yobu.edu.tr'
DEPO = 'https://github.com/fr3sby/turnusol'
OPENMCR = 'https://github.com/iansan5653/open-mcr'

METIN = f'''
<p>Turnusol, ArUco işaretli A4 optik formları okur, cevap anahtarına göre puanlar ve sonuçları Excel dosyasına yazar.</p>

<h3>Geliştirici</h3>
<p>Program Uzm. Fzt. Satuk Buğrahan Yinanç tarafından geliştirilmiştir.
Karşılaştığınız hataları ve önerilerinizi <a href="mailto:{EPOSTA}">{EPOSTA}</a> adresine iletebilirsiniz.
Kaynak kodu ve yeni sürümleri <a href="{DEPO}">{DEPO}</a> adresinde bulabilirsiniz.</p>

<h3>OBS uyumu</h3>
<p>Programın OBS dosyalarıyla (sınıf listesi ve not şablonu) uyumu yalnızca Yozgat Bozok Üniversitesi OBS sistemi için denenmiştir.
Başka kurumlarda öğrenci listesini programla gelen Excel şablonuna girerek kullanabilirsiniz.</p>

<h3>Atıf</h3>
<p>Turnusol, Ian Sanders’ın geliştirdiği açık kaynaklı <a href="{OPENMCR}">OpenMCR</a> projesinden (Copyright © 2019 Ian Sanders)
türetilmiştir. Formlar, okuma yöntemi ve arayüz bu proje temel alınarak yeniden yazılmıştır.</p>

<h3>Lisans</h3>
<p>Turnusol, OpenMCR gibi GNU Genel Kamu Lisansı sürüm 3 (GPL-3.0) ile dağıtılır. Programı bu lisansın koşullarına uyarak
kullanabilir, değiştirebilir ve paylaşabilirsiniz. Program hiçbir garanti verilmeden sunulur.
Arayüzde kullanılan IBM Plex yazı tipleri SIL Open Font License 1.1 ile dağıtılır.</p>
'''


class Hakkinda(QDialog):
    def __init__(self, ust=None):
        super().__init__(ust)
        self.setWindowTitle('Turnusol hakkında'); self.resize(620, 640)
        lay = QVBoxLayout(self); lay.setContentsMargins(24, 24, 24, 16); lay.setSpacing(16)
        bas = QHBoxLayout(); bas.setSpacing(16)
        logo = QLabel(); logo.setPixmap(QPixmap(os.path.join(KLASOR, 'ikonlar', 'uygulama.png')).scaled(
            72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        bas.addWidget(logo, 0, Qt.AlignTop)
        ad = QVBoxLayout(); ad.setSpacing(2)
        ad.addWidget(etiket('Turnusol', 'baslik'))
        ad.addWidget(etiket(f'Optik form okuyucu, sürüm {__version__}', 'yardim'))
        bas.addLayout(ad, 1)
        lay.addLayout(bas)
        govde = QLabel(METIN); govde.setWordWrap(True); govde.setTextFormat(Qt.RichText)
        govde.setOpenExternalLinks(True); govde.setTextInteractionFlags(Qt.TextBrowserInteraction)
        govde.setObjectName('hakkindaMetin')
        alan = QScrollArea(); alan.setWidgetResizable(True); alan.setFrameShape(QFrame.NoFrame)
        ic = QWidget(); il = QVBoxLayout(ic); il.setContentsMargins(0, 0, 8, 0); il.addWidget(govde); il.addStretch(1)
        alan.setWidget(ic)
        lay.addWidget(alan, 1)
        alt = QHBoxLayout(); alt.addStretch(1)
        k = dugme('Kapat', 'birincil'); k.clicked.connect(self.accept); alt.addWidget(k)
        lay.addLayout(alt)
