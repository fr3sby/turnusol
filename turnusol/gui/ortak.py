"""Ortak arayüz parçaları (Carbon bileşenlerinin Qt karşılıkları)."""
import os
from PySide6.QtCore import Qt, Signal, QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QIcon
from PySide6.QtWidgets import (QWidget, QLabel, QFrame, QHBoxLayout, QVBoxLayout, QPushButton,
                               QSizePolicy, QFileDialog, QToolButton)

from .tema import R, SANS, MONO, KLASOR


def etiket(metin, ad='etiket', kelime_kaydir=False):
    l = QLabel(metin); l.setObjectName(ad); l.setWordWrap(kelime_kaydir)
    if ad in ('talimat', 'yardim'):
        l.setTextFormat(Qt.RichText); l.setOpenExternalLinks(False)
    return l


def dugme(metin, tur='birincil', kisayol=None, ipucu=None):
    b = QPushButton(metin); b.setObjectName(tur); b.setCursor(Qt.PointingHandCursor)
    if kisayol:
        b.setShortcut(kisayol)
    if ipucu:
        b.setToolTip(ipucu)
    return b


def ayirici():
    f = QFrame(); f.setObjectName('ayirici'); return f


class Etiket(QLabel):
    """Carbon 'tag': küçük, hap biçimli durum etiketi."""
    def __init__(self, metin='', renk='gray'):
        super().__init__(metin)
        self.renk(renk)

    def renk(self, renk):
        bg, fg = R['tag_' + renk]
        self.setStyleSheet(f'background:{bg}; color:{fg}; border-radius:12px; padding:2px 8px; font-size:12px;')
        self.setFixedHeight(24)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)


class Bildirim(QFrame):
    """Carbon 'inline notification': solda renkli çizgi, açık zemin."""
    TUR = {'bilgi': ('info', 'bg_info'), 'basari': ('success', 'bg_success'),
           'uyari': ('warning', 'bg_warning'), 'hata': ('error', 'bg_error')}

    def __init__(self, tur='bilgi', baslik='', metin=''):
        super().__init__()
        lay = QHBoxLayout(self); lay.setContentsMargins(16, 12, 16, 12); lay.setSpacing(8)
        self.baslik = QLabel(); self.baslik.setStyleSheet('font-weight:600;')
        self.metin = QLabel(); self.metin.setWordWrap(True); self.metin.setTextFormat(Qt.RichText)
        self.metin.setTextInteractionFlags(Qt.TextBrowserInteraction)
        lay.addWidget(self.baslik, 0, Qt.AlignTop); lay.addWidget(self.metin, 1)
        self.ayarla(tur, baslik, metin)

    def ayarla(self, tur, baslik, metin):
        cizgi, zemin = self.TUR[tur]
        self.setStyleSheet(f'Bildirim {{ background:{R[zemin]}; border-left:3px solid {R[cizgi]}; }}')
        self.baslik.setText(baslik); self.baslik.setVisible(bool(baslik))
        self.metin.setText(metin)


class Kutucuk(QFrame):
    """Büyük sayı + açıklama (özet kutucuğu)."""
    def __init__(self, sayi='—', aciklama=''):
        super().__init__(); self.setObjectName('katman')
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 16, 16, 16); lay.setSpacing(4)
        self.s = etiket(str(sayi), 'buyukSayi'); self.a = etiket(aciklama, 'etiket')
        lay.addWidget(self.s); lay.addWidget(self.a)

    def ayarla(self, sayi, aciklama=None, renk=None):
        self.s.setText(str(sayi))
        self.s.setStyleSheet(f'color:{renk};' if renk else '')
        if aciklama is not None:
            self.a.setText(aciklama)


class Katlanir(QWidget):
    """'Gelişmiş ayarlar' gibi açılıp kapanan bölüm (Carbon accordion)."""
    def __init__(self, baslik, icerik: QWidget, acik=False):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        self.dugme = QToolButton(); self.dugme.setText(baslik); self.dugme.setCheckable(True)
        self.dugme.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.dugme.setArrowType(Qt.DownArrow if acik else Qt.RightArrow)
        self.dugme.setStyleSheet(f'QToolButton {{ border:none; border-top:1px solid {R["border_subtle"]}; '
                                 f'min-height:40px; padding:0 8px; text-align:left; background:transparent; }}'
                                 f'QToolButton:hover {{ background:{R["layer_hover"]}; }}')
        self.dugme.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.dugme.setCursor(Qt.PointingHandCursor)
        self.icerik = icerik
        lay.addWidget(self.dugme); lay.addWidget(icerik)
        self.dugme.setChecked(acik); icerik.setVisible(acik)
        self.dugme.toggled.connect(self._degis)

    def _degis(self, acik):
        self.dugme.setArrowType(Qt.DownArrow if acik else Qt.RightArrow)
        self.icerik.setVisible(acik)


class DosyaAlani(QFrame):
    """Carbon 'file uploader' bırakma alanı."""
    dosyalar = Signal(list)

    def __init__(self, metin, filtre, coklu=True, klasor_de=False):
        super().__init__()
        self.filtre, self.coklu, self.klasor_de = filtre, coklu, klasor_de
        self.setAcceptDrops(True); self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(96)
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 16, 16, 16)
        self.l = QLabel(metin); self.l.setTextFormat(Qt.RichText); self.l.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.l.setWordWrap(True)
        lay.addWidget(self.l)
        self._stil(False)

    def _stil(self, ustunde):
        self.setStyleSheet(f'DosyaAlani {{ background:{R["layer"]}; border:{"2px solid " + R["focus"] if ustunde else "1px dashed " + R["border_strong"]}; }}')

    def mousePressEvent(self, e):
        if self.coklu:
            yollar, _ = QFileDialog.getOpenFileNames(self, 'Dosya seç', '', self.filtre)
        else:
            y, _ = QFileDialog.getOpenFileName(self, 'Dosya seç', '', self.filtre)
            yollar = [y] if y else []
        if yollar:
            self.dosyalar.emit(yollar)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction(); self._stil(True)

    def dragLeaveEvent(self, e):
        self._stil(False)

    def dropEvent(self, e):
        self._stil(False)
        yollar = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if not self.coklu:
            yollar = yollar[:1]
        if yollar:
            self.dosyalar.emit(yollar)


class AdimCubugu(QWidget):
    """Carbon 'progress indicator': üstte çizgi, numara ve ad; tıklanabilir."""
    secildi = Signal(int)

    def __init__(self, adlar):
        super().__init__()
        self.adlar = adlar; self.aktif = 0
        self.durum = [''] * len(adlar)        # alt satırdaki kısa durum metni
        self.tamam = [False] * len(adlar)
        self.uyari = [False] * len(adlar)
        self.setFixedHeight(64); self.setMouseTracking(True); self._ustte = -1
        self.setCursor(Qt.PointingHandCursor)

    def ayarla(self, i, durum=None, tamam=None, uyari=None):
        if durum is not None: self.durum[i] = durum
        if tamam is not None: self.tamam[i] = tamam
        if uyari is not None: self.uyari[i] = uyari
        self.update()

    def sec(self, i):
        self.aktif = i; self.update()

    def _genislik(self):
        return self.width() / len(self.adlar)

    def mouseMoveEvent(self, e):
        i = int(e.position().x() // self._genislik())
        if i != self._ustte:
            self._ustte = i; self.update()

    def leaveEvent(self, e):
        self._ustte = -1; self.update()

    def mousePressEvent(self, e):
        i = int(e.position().x() // self._genislik())
        if 0 <= i < len(self.adlar):
            self.secildi.emit(i)

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w = self._genislik()
        p.fillRect(self.rect(), QColor(R['layer']))
        for i, ad in enumerate(self.adlar):
            x = int(i * w)
            if i == self._ustte and i != self.aktif:
                p.fillRect(x, 0, int(w), self.height(), QColor(R['layer_hover']))
            aktif = i == self.aktif
            renk = QColor(R['interactive']) if (aktif or self.tamam[i]) else QColor(R['border_subtle'])
            p.fillRect(x + 1, 0, int(w) - 2, 3 if aktif else 2, renk)
            # simge: tamam → dolu daire + tik, aktif → halka, uyarı → turuncu, diğer → boş halka
            cx, cy, r = x + 24, 26, 8
            if self.uyari[i]:
                p.setPen(Qt.NoPen); p.setBrush(QColor('#ff832b')); p.drawEllipse(cx - r, cy - r, 2 * r, 2 * r)
                p.setPen(QPen(QColor('#ffffff'), 2)); p.drawLine(cx, cy - 4, cx, cy + 1); p.drawPoint(cx, cy + 4)
            elif self.tamam[i] and not aktif:
                p.setPen(Qt.NoPen); p.setBrush(QColor(R['interactive'])); p.drawEllipse(cx - r, cy - r, 2 * r, 2 * r)
                p.setPen(QPen(QColor('#ffffff'), 1.6)); p.drawPolyline([QPointF(cx - 4, cy), QPointF(cx - 1, cy + 3), QPointF(cx + 4, cy - 3)])
            else:
                p.setBrush(Qt.NoBrush)
                p.setPen(QPen(QColor(R['interactive'] if aktif else R['text_secondary']), 1.5))
                p.drawEllipse(cx - r, cy - r, 2 * r, 2 * r)
                if aktif:
                    p.setPen(Qt.NoPen); p.setBrush(QColor(R['interactive'])); p.drawEllipse(cx - 3, cy - 3, 6, 6)
            f = QFont(SANS); f.setPixelSize(14); f.setWeight(QFont.DemiBold if aktif else QFont.Normal); p.setFont(f)
            p.setPen(QColor(R['text_primary']))
            p.drawText(x + 40, 31, f'{i + 1}. {ad}')
            f2 = QFont(SANS); f2.setPixelSize(12); p.setFont(f2)
            p.setPen(QColor('#8e6a00') if self.uyari[i] else QColor(R['text_helper']))
            p.drawText(x + 40, 51, self.durum[i])
        p.setPen(QColor(R['border_subtle'])); p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)


class SayfaBasligi(QWidget):
    """Her adımın başlığı + tek satır talimat + sağda isteğe bağlı 'Kılavuzda aç' bağlantısı."""
    kilavuz = Signal(str)

    def __init__(self, baslik, talimat, kilavuz_bolumu=None):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        ust = QHBoxLayout(); ust.setSpacing(16)
        ust.addWidget(etiket(baslik, 'baslik')); ust.addStretch(1)
        if kilavuz_bolumu:
            b = dugme('Bu adımı kılavuzda aç', 'hayalet')
            b.clicked.connect(lambda: self.kilavuz.emit(kilavuz_bolumu))
            ust.addWidget(b, 0, Qt.AlignBottom)
        lay.addLayout(ust)
        self.t = etiket(talimat, 'talimat', True)
        lay.addWidget(self.t)
