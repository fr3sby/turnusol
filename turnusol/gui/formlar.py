"""Boş optik formlar: seçme, önizleme, yazdırma ve PDF olarak kaydetme. Excel şablonunu kaydetme."""
import os
import shutil
from PySide6.QtCore import Qt, QUrl, QMarginsF, QRect
from PySide6.QtGui import QPixmap, QImage, QPainter, QDesktopServices, QPageLayout, QPageSize
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QFileDialog, QMessageBox, QFrame)

from ..kaynaklar import FORMLAR, form_yolu, SABLON
from .ortak import etiket, dugme, Bildirim


def _sayfa_goruntusu(yol, dpi):
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(yol)
    try:
        return pdf[0].render(scale=dpi / 72, grayscale=True).to_pil().convert('L')
    finally:
        pdf.close()


def _qimage(pil):
    im = QImage(pil.tobytes(), pil.width, pil.height, pil.width, QImage.Format_Grayscale8)
    return im.copy()


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
        self.setWindowTitle('Boş optik formlar'); self.resize(980, 760)
        lay = QHBoxLayout(self); lay.setContentsMargins(24, 24, 24, 24); lay.setSpacing(24)

        sol = QVBoxLayout(); sol.setSpacing(12)
        sol.addWidget(etiket('Boş optik formlar', 'baslik'))
        sol.addWidget(etiket('Kullanmak istediğiniz formu seçin. Formu doğrudan yazdırabilir ya da PDF olarak kaydedip '
                             'fotokopiyle çoğaltabilirsiniz.', 'yardim', True))
        self.liste = QListWidget(); self.liste.setMinimumWidth(300); self.liste.setMinimumHeight(8 * 41 + 4)
        grup = None
        for dosya, g, baslik, aciklama in FORMLAR:
            if g != grup:
                it = QListWidgetItem(g); it.setFlags(Qt.NoItemFlags)
                f = it.font(); f.setBold(True); it.setFont(f); self.liste.addItem(it); grup = g
            it = QListWidgetItem('   ' + baslik); it.setData(Qt.UserRole, (dosya, aciklama)); self.liste.addItem(it)
        self.liste.currentItemChanged.connect(self._sec)
        sol.addWidget(self.liste, 1)
        self.aciklama = etiket('', 'yardim', True); sol.addWidget(self.aciklama)
        sol.addWidget(Bildirim('uyari', '', 'PDF dosyasını başka bir programdan yazdırırken ölçeği <b>Gerçek boyut</b> ya da '
                               '<b>%100</b> olarak seçin. Sayfaya sığdırma ayarı formu küçültür. Program küçültülmüş formları da '
                               'çoğu zaman okur, ancak gerçek boyutta basılan formlar en güvenilir sonucu verir.'))
        dug = QHBoxLayout(); dug.setSpacing(1)
        self.yazdir = dugme('Yazdır…', 'birincil'); self.yazdir.clicked.connect(self._yazdir)
        self.kaydet = dugme('PDF olarak kaydet…', 'ikincil'); self.kaydet.clicked.connect(self._kaydet)
        dug.addWidget(self.yazdir); dug.addWidget(self.kaydet); dug.addStretch(1)
        sol.addLayout(dug)
        ac = dugme('PDF dosyasını varsayılan programla aç', 'hayalet'); ac.clicked.connect(self._ac)
        sol.addWidget(ac, 0, Qt.AlignLeft)
        sab = dugme('Boş Excel öğrenci listesi şablonunu kaydet…', 'hayalet'); sab.clicked.connect(lambda: sablonu_kaydet(self))
        sol.addWidget(sab, 0, Qt.AlignLeft)
        lay.addLayout(sol, 2)

        self.onizleme = QLabel(); self.onizleme.setAlignment(Qt.AlignCenter); self.onizleme.setMinimumWidth(480)
        self.onizleme.setStyleSheet('background:#e0e0e0;')
        lay.addWidget(self.onizleme, 3)
        self.liste.setCurrentRow(1)

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
        im = _qimage(_sayfa_goruntusu(form_yolu(s[0]), 90))
        pm = QPixmap.fromImage(im).scaled(self.onizleme.width() - 24, self.onizleme.height() - 24,
                                          Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
        dpi = min(yazici.resolution(), 600)
        img = _qimage(_sayfa_goruntusu(form_yolu(dosya), dpi))
        p = QPainter()
        if not p.begin(yazici):
            QMessageBox.warning(self, 'Yazdırılamadı', 'Yazıcı başlatılamadı. Formu PDF olarak kaydedip başka bir programdan yazdırmayı deneyin.')
            return
        hedef = yazici.paperRect(QPrinter.DevicePixel).toRect()
        p.drawImage(QRect(0, 0, hedef.width(), hedef.height()), img)
        p.end()
