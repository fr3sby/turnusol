"""Boş optik formlar: seçme, önizleme, yazdırma ve PDF olarak kaydetme. Excel şablonunu kaydetme."""
import os
import shutil
from PySide6.QtCore import Qt, QUrl, QMarginsF, QRect
from PySide6.QtGui import QPixmap, QImage, QPainter, QDesktopServices, QPageLayout, QPageSize
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QFileDialog, QMessageBox, QFrame, QScrollArea, QWidget, QSizePolicy)

from ..kaynaklar import FORMLAR, form_yolu, SABLON
from .ortak import etiket, dugme, Bildirim


def _sayfa_goruntusu(yol, dpi):
    """PDF'nin ilk sayfasını gri tonlu QImage olarak döndürür (Pillow gerekmez)."""
    import numpy as np
    from .. import girdi
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(yol)
    try:
        s = pdf[0]
        arr = girdi._gri(s.render(scale=dpi / 72, grayscale=True).to_numpy().copy())
        s.close()
    finally:
        pdf.close()
    arr = np.ascontiguousarray(arr, dtype=np.uint8)
    h, w = arr.shape
    return QImage(arr.data, w, h, arr.strides[0], QImage.Format_Grayscale8).copy()


def sablonu_kaydet(ust):
    hedef, _ = QFileDialog.getSaveFileName(ust, 'Excel şablonunu kaydet',
                                           os.path.join(os.path.expanduser('~'), 'Ogrenci Listesi.xlsx'),
                                           'Excel dosyası (*.xlsx)')
    if not hedef:
        return
    if not hedef.lower().endswith('.xlsx'):
        hedef += '.xlsx'
    try:
        shutil.copyfile(SABLON, hedef)
    except OSError as e:
        QMessageBox.warning(ust, 'Şablon kaydedilemedi', f'Dosya kaydedilemedi. Sistem şu hatayı verdi: {e}')
        return
    QMessageBox.information(ust, 'Şablon kaydedildi',
                            f'Excel şablonu {os.path.basename(hedef)} adıyla kaydedildi. Öğrencileri “Öğrenciler” sayfasına '
                            'girdikten sonra dosyayı programa sınıf listesi ya da not şablonu olarak yükleyebilirsiniz.')


class FormlarPenceresi(QDialog):
    def __init__(self, ust=None):
        super().__init__(ust)
        self.setWindowTitle('Boş optik formlar'); self.resize(1100, 820); self.setMinimumSize(900, 640)
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 24, 0); lay.setSpacing(16)

        # sol sütun kaydırılabilir bir alanda durur; pencere küçülünce öğeler üst üste binmez
        panel = QWidget(); sol = QVBoxLayout(panel); sol.setContentsMargins(24, 24, 8, 24); sol.setSpacing(12)
        sol.addWidget(etiket('Boş optik formlar', 'baslik'))
        sol.addWidget(etiket('Kullanmak istediğiniz formu seçin. Formu doğrudan yazdırabilir ya da PDF olarak kaydedip '
                             'fotokopiyle çoğaltabilirsiniz.', 'yardim', True))
        self.liste = QListWidget()
        self.liste.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.liste.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        grup = None
        for dosya, g, baslik, aciklama in FORMLAR:
            if g != grup:
                it = QListWidgetItem(g); it.setFlags(Qt.NoItemFlags)
                f = it.font(); f.setBold(True); it.setFont(f); self.liste.addItem(it); grup = g
            it = QListWidgetItem('   ' + baslik); it.setData(Qt.UserRole, (dosya, aciklama)); self.liste.addItem(it)
        self.liste.currentItemChanged.connect(self._sec)
        sol.addWidget(self.liste)
        self.aciklama = etiket('', 'yardim', True); self.aciklama.setMinimumHeight(36)
        sol.addWidget(self.aciklama)
        sol.addWidget(Bildirim('uyari', '', 'PDF dosyasını başka bir programdan yazdırırken ölçeği <b>Gerçek boyut</b> ya da '
                               '<b>%100</b> olarak seçin. Sayfaya sığdırma ayarı formu küçültür.'))
        dug = QHBoxLayout(); dug.setSpacing(1)
        self.yazdir = dugme('Yazdır…', 'birincil'); self.yazdir.clicked.connect(self._yazdir)
        self.kaydet = dugme('PDF olarak kaydet…', 'ikincil'); self.kaydet.clicked.connect(self._kaydet)
        dug.addWidget(self.yazdir); dug.addWidget(self.kaydet); dug.addStretch(1)
        sol.addLayout(dug)
        ac = dugme('PDF dosyasını varsayılan programla aç', 'hayalet'); ac.clicked.connect(self._ac)
        sol.addWidget(ac, 0, Qt.AlignLeft)
        sab = dugme('Boş Excel öğrenci listesi şablonunu kaydet…', 'hayalet'); sab.clicked.connect(lambda: sablonu_kaydet(self))
        sol.addWidget(sab, 0, Qt.AlignLeft)
        sol.addStretch(1)
        alan = QScrollArea(); alan.setWidget(panel); alan.setWidgetResizable(True); alan.setFrameShape(QFrame.NoFrame)
        alan.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        alan.setFixedWidth(430)
        lay.addWidget(alan)

        self.onizleme = QLabel(); self.onizleme.setAlignment(Qt.AlignCenter)
        self.onizleme.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.onizleme.setStyleSheet('background:#e0e0e0;')
        sag = QVBoxLayout(); sag.setContentsMargins(0, 24, 0, 24); sag.addWidget(self.onizleme)
        lay.addLayout(sag, 1)
        self.liste.setCurrentRow(1)

    def _liste_yuksekligi(self):
        h = sum(self.liste.sizeHintForRow(i) for i in range(self.liste.count()))
        self.liste.setFixedHeight(h + 2 * self.liste.frameWidth() + 2)

    def showEvent(self, e):
        super().showEvent(e); self._liste_yuksekligi(); self._goster()

    def _secili(self):
        it = self.liste.currentItem()
        return it.data(Qt.UserRole) if it else None

    def _sec(self, *_):
        s = self._secili()
        for b in (self.yazdir, self.kaydet):
            b.setEnabled(bool(s))
        if not s:
            return
        dosya, aciklama = s
        self.aciklama.setText(aciklama)
        self._goster()

    def _goster(self):
        s = self._secili()
        if not s:
            return
        w, h = self.onizleme.width() - 32, self.onizleme.height() - 32
        if w < 50 or h < 50:
            return
        if getattr(self, '_onbellek', (None,))[0] != s[0]:
            self._onbellek = (s[0], QPixmap.fromImage(_sayfa_goruntusu(form_yolu(s[0]), 150)))
        dpr = self.devicePixelRatioF()
        pm = self._onbellek[1].scaled(int(w * dpr), int(h * dpr), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pm.setDevicePixelRatio(dpr)
        self.onizleme.setPixmap(pm)

    def resizeEvent(self, e):
        super().resizeEvent(e); self._goster()

    def _kaydet(self):
        dosya, _ = self._secili()
        hedef, _ = QFileDialog.getSaveFileName(self, 'Formu PDF olarak kaydet',
                                               os.path.join(os.path.expanduser('~'), dosya), 'PDF dosyası (*.pdf)')
        if not hedef:
            return
        if not hedef.lower().endswith('.pdf'):
            hedef += '.pdf'
        try:
            shutil.copyfile(form_yolu(dosya), hedef)
        except OSError as e:
            QMessageBox.warning(self, 'Form kaydedilemedi', f'Dosya kaydedilemedi. Sistem şu hatayı verdi: {e}')

    def _ac(self):
        s = self._secili()
        if s:
            QDesktopServices.openUrl(QUrl.fromLocalFile(form_yolu(s[0])))

    def _yazdir(self):
        dosya, _ = self._secili()
        yazici = QPrinter(QPrinter.HighResolution)
        yazici.setPageLayout(QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Portrait, QMarginsF(0, 0, 0, 0)))
        yazici.setFullPage(True)
        yazici.setDocName(dosya)
        d = QPrintDialog(yazici, self); d.setWindowTitle('Formu yazdır')
        if d.exec() != QDialog.Accepted:
            return
        try:
            bas(yazici, form_yolu(dosya))
        except Exception as e:
            QMessageBox.warning(self, 'Yazdırılamadı',
                                f'Form yazıcıya gönderilemedi. Sistem şu hatayı verdi: {e}\n\n'
                                'Formu PDF olarak kaydedip başka bir programdan yazdırmayı deneyin.')


def bas(yazici, yol):
    """PDF'nin ilk sayfasını yazıcıya gerçek boyutta basar. Yazıcı çoklu kopyayı kendisi yapamıyorsa kopyaları tek tek gönderir."""
    yazici.setFullPage(True)
    dpi = max(150, min(yazici.resolution(), 600))
    img = _sayfa_goruntusu(yol, dpi)
    kopya = 1 if yazici.supportsMultipleCopies() else max(1, yazici.copyCount())
    p = QPainter()
    if not p.begin(yazici):
        raise RuntimeError('Yazıcı başlatılamadı.')
    try:
        for i in range(kopya):
            if i:
                yazici.newPage()
            hedef = yazici.paperRect(QPrinter.DevicePixel).toRect()
            p.drawImage(QRect(0, 0, hedef.width(), hedef.height()), img)
    finally:
        p.end()
