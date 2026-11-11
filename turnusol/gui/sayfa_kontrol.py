"""4. adım: kâğıtları gözle kontrol, tıklayarak düzeltme, onaylama."""
import numpy as np
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QImage, QPixmap, QPen, QColor, QBrush, QPainter, QKeySequence, QShortcut
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, QSplitter,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QLineEdit, QFrame,
                               QListWidget, QListWidgetItem, QPushButton, QButtonGroup, QGridLayout, QLabel)

from .ortak import Etiket, Bildirim, etiket, dugme, ayirici
from .tema import R, DURUM_RENK, MONO
from .. import okuma

ALAN_AD = {'FIRST_NAME': 'Ad', 'LAST_NAME': 'Soyad', 'STUDENT_ID': 'Öğrenci no', 'TEST_FORM_CODE': 'Kitapçık'}


class KagitGorunumu(QGraphicsView):
    """Kâğıt görüntüsü. Kâğıt, okumada bulunan hizalamayla dik ve düz gösterilir; isteğe bağlı 90° döndürülebilir."""
    tiklandi = Signal(object, int, bool)      # anahtar, şık index, shift

    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setStyleSheet(f'background:{R["layer_selected"]}; border:none;')
        self.k = None; self._pix = None; self._qimg = None; self.odak = None
        self.P = {}; self.ppm = 4.0; self.aci = 0

    def goster(self, k, gri, sigdir=True):
        self.k = k; self.aci = 0
        sc = self.scene(); sc.clear(); self._pix = None; self.P = {}
        if gri is None:
            return
        if k is not None:
            gri, self.P, self.ppm = okuma.duz_goruntu(gri, k)
        h, w = gri.shape
        self._buf = np.ascontiguousarray(gri)
        self._qimg = QImage(self._buf.data, w, h, w, QImage.Format_Grayscale8)
        self._pix = sc.addPixmap(QPixmap.fromImage(self._qimg))
        sc.setSceneRect(QRectF(0, 0, w, h))
        self.ciz()
        if sigdir:
            self.sigdir()

    def sigdir(self):
        """Kâğıdı pencere genişliğine sığdırır ve en üstten gösterir."""
        if not self._pix:
            return
        r = self.scene().sceneRect()
        self.resetTransform()
        self.rotate(self.aci)
        gen = r.height() if self.aci in (90, 270) else r.width()
        s = (self.viewport().width() - 8) / max(1.0, gen)
        self.scale(s, s)
        self.centerOn(r.center())
        self.verticalScrollBar().setValue(self.verticalScrollBar().minimum())

    def dondur(self, derece=90):
        self.aci = (self.aci + derece) % 360
        self.rotate(derece)

    def yakinlas(self, f):
        self.scale(f, f)

    def wheelEvent(self, e):
        if e.modifiers() & (Qt.ControlModifier | Qt.MetaModifier):
            self.yakinlas(1.15 if e.angleDelta().y() > 0 else 1 / 1.15)
        else:
            super().wheelEvent(e)

    def _olcek(self):
        t = self.transform()
        return (t.m11() ** 2 + t.m12() ** 2) ** 0.5

    def odakla(self, anahtar):
        self.odak = anahtar; self.ciz()
        if anahtar in self.P:
            P = self.P[anahtar]
            xs = [p[0] for p in P]; ys = [p[1] for p in P]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            r = self.scene().sceneRect()
            gen = r.height() if self.aci in (90, 270) else r.width()
            hedef = (self.viewport().width() / max(1.0, gen)) * 2.5   # en az 2,5 kat yakınlaş
            mevcut = self._olcek()
            if mevcut < hedef:
                self.scale(hedef / mevcut, hedef / mevcut)
            self.centerOn(cx, cy)

    def ciz(self):
        sc = self.scene()
        for it in [i for i in sc.items() if i is not self._pix]:
            sc.removeItem(it)
        k = self.k
        if not k or k.okunamadi or not k.form or not self.P:
            return
        r = 2.25 * self.ppm
        kal = max(2.0, self.ppm * 0.32)
        def halka(p, renk, kalinlik=kal):
            sc.addEllipse(p[0] - r, p[1] - r, 2 * r, 2 * r, QPen(renk, kalinlik))
        def kutu(P, renk, dolgu):
            xs = [p[0] for p in P]; ys = [p[1] for p in P]
            pad = r * 1.35
            sc.addRect(min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad,
                       QPen(renk, kal * 0.8), QBrush(dolgu))
        bekleyen = {u['hedef'] if u['tur'] == 'soru' else ('alan',) + tuple(u['hedef'])
                    for u in k.kontrol_listesi if u['tur'] in ('soru', 'alan') and (u['tur'] == 'soru' or u['hedef'][1] is not None)}
        turuncu = QColor('#ff832b'); dolgu = QColor(255, 131, 43, 40)
        for q in k.form.sorular:
            n = q['number']; P = self.P[('soru', n)]
            if n in bekleyen:
                kutu(P, turuncu, dolgu)
            degerler = [o['value'] for o in q['options']]
            if n in k.elle_cevaplar:
                for v in filter(None, k.elle_cevaplar[n].split('+')):
                    halka(P[degerler.index(v)], DURUM_RENK['elle'])
                continue
            st = k.durumlar.get(n, 'boş')
            if st != 'boş':
                for v in k.cevaplar[n].split('+'):
                    halka(P[degerler.index(v)], DURUM_RENK[st])
        for ad, f in k.form.alanlar.items():
            for ci, sutun in enumerate(f['columns']):
                key = ('alan', ad, ci); P = self.P[key]
                if key in bekleyen:
                    kutu(P, turuncu, dolgu)
                if (ad, ci) in k.elle_sutunlar:
                    v = k.elle_sutunlar[(ad, ci)]
                    vals = [b['value'] for b in sutun]
                    if v in vals: halka(P[vals.index(v)], DURUM_RENK['elle'])
                    continue
                st = k.alan_durumlari[ad][ci]
                if st == 'boş': continue
                sk = k.skorlar[key]
                for i in np.argsort(sk)[::-1][:2 if st == 'çift' else 1]:
                    halka(P[i], DURUM_RENK[st])
        if self.odak and self.odak in self.P:
            P = self.P[self.odak]
            xs = [p[0] for p in P]; ys = [p[1] for p in P]; pad = r * 1.9
            sc.addRect(min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad,
                       QPen(QColor(R['interactive']), kal * 1.4))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self.k and not self.k.okunamadi and self.k.form and self.P:
            p = self.mapToScene(e.position().toPoint())
            en, en_d = None, (2.0 * self.ppm * 2.2) ** 2
            for key, P in self.P.items():
                for i, (x, y) in enumerate(P):
                    d = (x - p.x()) ** 2 + (y - p.y()) ** 2
                    if d < en_d:
                        en, en_d = (key, i), d
            if en:
                self.tiklandi.emit(en[0], en[1], bool(e.modifiers() & Qt.ShiftModifier))
                return
        super().mousePressEvent(e)


class KontrolSayfasi(QWidget):
    def __init__(self, baglam):
        super().__init__(); self.setObjectName('sayfa')
        self.b = baglam; self.sonuc = []; self.secili = None; self.filtre = 'kontrol'
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        # üst araç çubuğu
        ust = QFrame(); ust.setObjectName('katman')
        ul = QHBoxLayout(ust); ul.setContentsMargins(24, 12, 24, 12); ul.setSpacing(12)
        ul.addWidget(etiket('Kontrol', 'altbaslik')); ul.addSpacing(8)
        self.talimat = etiket('Turuncu çerçeveli yerlere bakın. Program bir şıkkı yanlış okuduysa doğru şıkka tıklayın; '
                              'işaretli bir şıkka tekrar tıklarsanız o şık silinir. Kâğıt doğruysa <b>Onayla</b> düğmesine ya da Enter tuşuna basın. '
                              'Sonraki kâğıda geçmek için <b>Sonraki kâğıt</b> düğmesini ya da J tuşunu kullanın.', 'talimat', True)
        ul.addWidget(self.talimat, 1)
        k = dugme('Kılavuz', 'hayalet'); k.clicked.connect(lambda: self.b.kilavuz_ac.emit('kontrol')); ul.addWidget(k)
        lay.addWidget(ust); lay.addWidget(ayirici())

        bol = QSplitter(Qt.Horizontal); bol.setHandleWidth(1)
        # --- sol liste ---
        sol = QFrame(); sol.setObjectName('katman'); sl = QVBoxLayout(sol); sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(0)
        fl = QHBoxLayout(); fl.setContentsMargins(16, 12, 16, 8); fl.setSpacing(0)
        self.f_grup = QButtonGroup(self)
        self.f_kontrol = self._sekme('Kontrol bekleyen'); self.f_hepsi = self._sekme('Tümü')
        for i, d in enumerate((self.f_kontrol, self.f_hepsi)):
            self.f_grup.addButton(d, i); fl.addWidget(d)
        self.f_kontrol.setChecked(True); self.f_grup.idClicked.connect(self._filtre)
        fl.addStretch(1); sl.addLayout(fl)
        self.ara = QLineEdit(); self.ara.setPlaceholderText('Numaraya ya da ada göre arayın'); self.ara.textChanged.connect(self.listele)
        ar = QHBoxLayout(); ar.setContentsMargins(16, 0, 16, 8); ar.addWidget(self.ara); sl.addLayout(ar)
        self.liste = QTableWidget(0, 4)
        self.liste.setHorizontalHeaderLabels(['', 'Numara', 'Ad Soyad', 'Puan'])
        h = self.liste.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed); self.liste.setColumnWidth(0, 28)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents); h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.liste.verticalHeader().hide(); self.liste.verticalHeader().setDefaultSectionSize(40)
        self.liste.setSelectionBehavior(QAbstractItemView.SelectRows); self.liste.setSelectionMode(QAbstractItemView.SingleSelection)
        self.liste.setEditTriggers(QAbstractItemView.NoEditTriggers); self.liste.setShowGrid(False)
        self.liste.itemSelectionChanged.connect(self._liste_secim)
        sl.addWidget(self.liste, 1)
        self.sayac = etiket('', 'yardim'); sc = QHBoxLayout(); sc.setContentsMargins(16, 8, 16, 8); sc.addWidget(self.sayac); sl.addLayout(sc)
        bol.addWidget(sol)

        # --- orta görüntü ---
        orta = QWidget(); ol = QVBoxLayout(orta); ol.setContentsMargins(0, 0, 0, 0); ol.setSpacing(0)
        self.gor = KagitGorunumu(); self.gor.tiklandi.connect(self._tik)
        ol.addWidget(self.gor, 1)
        alt = QFrame(); alt.setObjectName('katman'); al = QHBoxLayout(alt); al.setContentsMargins(16, 6, 16, 6); al.setSpacing(16)
        for ad, renk in (('Okunan', DURUM_RENK['tamam']), ('Şüpheli', DURUM_RENK['zayıf']), ('Çift işaret', DURUM_RENK['çift']), ('Elle düzeltilen', DURUM_RENK['elle'])):
            nokta = QLabel('●'); nokta.setStyleSheet(f'color:{renk.name()}; font-size:14px;')
            al.addWidget(nokta); al.addWidget(etiket(ad, 'yardim')); al.addSpacing(4)
        al.addStretch(1)
        for metin, f, ip in (('Döndür', lambda: self.gor.dondur(90), 'Kâğıdı saat yönünde 90 derece döndür (kısayol: R)'),
                             ('−', lambda: self.gor.yakinlas(1 / 1.25), 'Uzaklaştır (kısayol: Ctrl ve eksi)'), ('Sığdır', self.gor.sigdir, 'Kâğıdı genişliğe sığdır (kısayol: F)'),
                             ('+', lambda: self.gor.yakinlas(1.25), 'Yakınlaştır (kısayol: Ctrl ve artı)')):
            d = dugme(metin, 'hayalet', ipucu=ip); d.setMinimumHeight(32); d.clicked.connect(f); al.addWidget(d)
        ol.addWidget(alt)
        bol.addWidget(orta)

        # --- sağ panel ---
        sag = QFrame(); sag.setObjectName('katman'); sa = QVBoxLayout(sag); sa.setContentsMargins(20, 20, 20, 16); sa.setSpacing(12)
        self.p_no = etiket('—', 'altbaslik'); self.p_no.setStyleSheet(f"font-family:'{MONO}';")
        self.p_ad = etiket('', 'talimat', True)
        self.p_durum = Etiket('', 'gray')
        ud = QHBoxLayout(); ud.addWidget(self.p_no); ud.addStretch(1); ud.addWidget(self.p_durum)
        sa.addLayout(ud); sa.addWidget(self.p_ad)
        self.p_kaynak = etiket('', 'yardim', True); sa.addWidget(self.p_kaynak)
        sa.addWidget(ayirici())
        g = QGridLayout(); g.setHorizontalSpacing(8); g.setVerticalSpacing(2)
        self.p_sayi = {}
        for i, (ad, an) in enumerate((('dogru', 'Doğru'), ('yanlis', 'Yanlış'), ('bos', 'Boş'), ('puan', 'Puan'))):
            s = etiket('—', 'buyukSayi'); s.setStyleSheet('font-size:24px;')
            g.addWidget(s, 0, i); g.addWidget(etiket(an, 'etiket'), 1, i); self.p_sayi[ad] = s
        sa.addLayout(g)
        sa.addWidget(ayirici())
        uh = QHBoxLayout(); uh.addWidget(etiket('Bakılacak yerler', 'bolumBaslik')); uh.addStretch(1)
        self.u_sayi = Etiket('0', 'gray'); uh.addWidget(self.u_sayi); sa.addLayout(uh)
        self.uyarilar = QListWidget(); self.uyarilar.itemClicked.connect(self._uyari_sec)
        self.uyarilar.setStyleSheet('QListWidget::item { min-height: 36px; padding: 6px 12px; }')
        self.uyarilar.setWordWrap(True); self.uyarilar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.uyarilar.setTextElideMode(Qt.ElideNone)
        sa.addWidget(self.uyarilar, 1)
        self.bildirim = Bildirim('basari', '', 'Bu kâğıtta bakılacak yer yok.'); sa.addWidget(self.bildirim)
        self.geri_al = dugme('Elle düzeltmeleri geri al', 'hayalet'); self.geri_al.clicked.connect(self._geri_al)
        sa.addWidget(self.geri_al, 0, Qt.AlignLeft)
        self.onay = dugme('Onayla', 'birincil', ipucu='Kısayol: Enter. Onaylamak sizi sonraki kâğıda geçirmez.')
        self.onay.clicked.connect(self.onayla)
        sa.addWidget(self.onay)
        nav = QHBoxLayout(); nav.setSpacing(1)
        self.onceki = dugme('Önceki kâğıt', 'ikincil', ipucu='Kısayol: K'); self.sonraki = dugme('Sonraki kâğıt', 'ikincil', ipucu='Kısayol: J')
        self.onceki.clicked.connect(lambda: self._git(-1)); self.sonraki.clicked.connect(lambda: self._git(1))
        nav.addWidget(self.onceki); nav.addWidget(self.sonraki); sa.addLayout(nav)
        bol.addWidget(sag)
        bol.setSizes([340, 800, 340]); bol.setStretchFactor(1, 1)
        bol.setCollapsible(0, False); bol.setCollapsible(2, False)
        lay.addWidget(bol, 1)

        for tus, f in ((Qt.Key_Return, self.onayla), (Qt.Key_Enter, self.onayla), (Qt.Key_J, lambda: self._git(1)),
                       (Qt.Key_K, lambda: self._git(-1)), (Qt.Key_F, self.gor.sigdir), (Qt.Key_N, self._sonraki_uyari),
                       (Qt.Key_R, lambda: self.gor.dondur(90))):
            QShortcut(QKeySequence(tus), self, f)
        QShortcut(QKeySequence.ZoomIn, self, lambda: self.gor.yakinlas(1.25))
        QShortcut(QKeySequence.ZoomOut, self, lambda: self.gor.yakinlas(1 / 1.25))
        self.b.degisti.connect(self._dis_degisim)

    def _sekme(self, metin):
        d = QPushButton(metin); d.setCheckable(True); d.setCursor(Qt.PointingHandCursor)
        d.setStyleSheet(f"QPushButton {{ border:none; border-bottom:2px solid {R['border_subtle']}; background:transparent; "
                        f"min-height:36px; padding:0 12px; text-align:center; color:{R['text_secondary']}; }}"
                        f"QPushButton:checked {{ border-bottom:2px solid {R['interactive']}; color:{R['text_primary']}; font-weight:600; }}"
                        f"QPushButton:hover {{ color:{R['text_primary']}; }}")
        return d

    # ---------- liste ----------
    def _dis_degisim(self, ne):
        if ne in ('tarama', 'liste', 'anahtar', 'puan'):
            self.yenile()

    def yenile(self):
        self.sonuc = self.b.oturum.sonuclar()
        self.listele()

    def _filtre(self, i):
        self.filtre = 'kontrol' if i == 0 else 'hepsi'; self.listele()

    def _gorunen(self):
        q = self.ara.text().strip().upper()
        out = []
        secili_k = self.secili['kagit'] if self.secili else None
        for s in self.sonuc:
            if self.filtre == 'kontrol' and not s['kontrol'] and s['kagit'] is not secili_k:
                continue
            if q and q not in (s['no'] or '') and q not in f"{s['ad']} {s['soyad']}".upper():
                continue
            out.append(s)
        return sorted(out, key=lambda s: (s['kagit'].kaynak, s['kagit'].sayfa))

    def listele(self):
        secili_k = self.secili['kagit'] if self.secili else None
        g = self._gorunen()
        self.f_kontrol.setText(f'Kontrol bekleyen ({sum(1 for s in self.sonuc if s["kontrol"])})')
        self.f_hepsi.setText(f'Tümü ({len(self.sonuc)})')
        t = self.liste; t.blockSignals(True); t.setRowCount(len(g))
        sec_satir = None
        for r, s in enumerate(g):
            k = s['kagit']
            renk = (R['error'] if k.okunamadi else ('#ff832b' if s['kontrol'] else (R['interactive'] if k.onaylandi else R['success'])))
            d = QTableWidgetItem('●'); d.setForeground(QColor(renk)); d.setTextAlignment(Qt.AlignCenter)
            t.setItem(r, 0, d)
            no = QTableWidgetItem(s['no'] or '—'); no.setFont(self._mono()); t.setItem(r, 1, no)
            t.setItem(r, 2, QTableWidgetItem(f"{s['ad']} {s['soyad']}".strip() or '—'))
            p = QTableWidgetItem('' if s['puan'] is None else str(s['puan'])); p.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            t.setItem(r, 3, p)
            for c in range(4):
                t.item(r, c).setData(Qt.UserRole, id(k))
            if k is secili_k:
                sec_satir = r
        t.blockSignals(False)
        self._g = g
        n_k = sum(1 for s in self.sonuc if s['kontrol'])
        n_o = sum(1 for s in self.sonuc if s['kagit'].onaylandi)
        self.sayac.setText(f'Toplam {len(self.sonuc)} kâğıt var. {n_k} kâğıt kontrol bekliyor, {n_o} kâğıt onaylandı.')
        if sec_satir is None and g:
            sec_satir = 0
        self._satir_sec(sec_satir)

    def _satir_sec(self, r):
        t = self.liste
        if r is None or not (0 <= r < len(self._g)):
            self.secili = None; self.gor.goster(None, None); self._panel(); return
        t.blockSignals(True); t.selectRow(r); t.blockSignals(False)
        self.sec(self._g[r])

    def _mono(self):
        f = self.font(); f.setFamily(MONO); return f

    def _liste_secim(self):
        r = self.liste.currentRow()
        if 0 <= r < len(self._g):
            self.sec(self._g[r])

    def sec(self, s):
        degisti = not self.secili or self.secili['kagit'] is not s['kagit']
        self.secili = s
        k = s['kagit']
        if degisti:
            try:
                gri = self.b.goruntu(k.kaynak, k.sayfa)
            except Exception:
                gri = None
            self.gor.odak = None
            self.gor.goster(k, gri)
        else:
            self.gor.ciz()
        self._panel()

    def _panel(self):
        s = self.secili
        self.uyarilar.clear()
        if not s:
            self.p_no.setText('—'); self.p_ad.setText('Gösterilecek kâğıt yok.'); self.p_kaynak.setText('')
            self.onay.setEnabled(False); return
        k = s['kagit']
        self.onay.setEnabled(True)
        if k.onaylandi:
            self.onay.setText('Onayı geri al'); self.onay.setObjectName('ucuncul')
        else:
            self.onay.setText('Onayla'); self.onay.setObjectName('birincil')
        self.onay.style().unpolish(self.onay); self.onay.style().polish(self.onay)
        self.p_no.setText(s['no'] or 'Numara okunamadı')
        satirlar = [f"<b>{s['ad']} {s['soyad']}</b>" if (s['ad'] or s['soyad']) else '<b>Ad ve soyad okunamadı.</b>']
        if s['ad_kaynagi'] != 'liste' and (s['ad'] or s['soyad']):
            satirlar.append('<span style="color:#6f6f6f">Ad ve soyad kâğıttan okundu.</span>')
        if s['kitapcik']:
            satirlar.append(f"Öğrenci {s['kitapcik']} kitapçığını kullanmış.")
        self.p_ad.setText('<br>'.join(satirlar))
        import os
        self.p_kaynak.setText(f'Bu kâğıt {os.path.basename(k.kaynak)} dosyasının {k.sayfa}. sayfası.')
        if k.okunamadi:
            self.p_durum.setText('Okunamadı'); self.p_durum.renk('red')
        elif s['kontrol']:
            self.p_durum.setText('Kontrol bekliyor'); self.p_durum.renk('yellow')
        elif k.onaylandi:
            self.p_durum.setText('Onaylandı'); self.p_durum.renk('blue')
        else:
            self.p_durum.setText('Sorunsuz'); self.p_durum.renk('green')
        p = s.get('puanlama') or {}
        for ad in ('dogru', 'yanlis', 'bos'):
            self.p_sayi[ad].setText(str(p.get(ad, '—')) if p and not p.get('hata') else '—')
        self.p_sayi['puan'].setText('—' if s['puan'] is None else str(s['puan']))
        for n in s['notlar']:
            pass
        uy = [u for u in k.kontrol_listesi]
        for u in uy:
            it = QListWidgetItem(u['mesaj']); it.setData(Qt.UserRole, u); self.uyarilar.addItem(it)
        for n in s['notlar']:
            if not any(n == u['mesaj'] for u in uy):
                it = QListWidgetItem(n); it.setData(Qt.UserRole, None); self.uyarilar.addItem(it)
        self.u_sayi.setText(str(self.uyarilar.count())); self.u_sayi.renk('yellow' if self.uyarilar.count() else 'gray')
        self.uyarilar.setVisible(self.uyarilar.count() > 0)
        self.bildirim.setVisible(self.uyarilar.count() == 0)
        self.geri_al.setVisible(bool(k.elle_cevaplar or k.elle_sutunlar or k.elle_alanlar))

    # ---------- etkileşim ----------
    def _uyari_sec(self, it):
        u = it.data(Qt.UserRole)
        if not u:
            return
        if u['tur'] == 'soru':
            self.gor.odakla(('soru', u['hedef']))
        elif u['tur'] == 'alan' and u['hedef'][1] is not None:
            self.gor.odakla(('alan',) + tuple(u['hedef']))

    def _sonraki_uyari(self):
        n = self.uyarilar.count()
        if not n: return
        i = (self.uyarilar.currentRow() + 1) % n
        self.uyarilar.setCurrentRow(i); self._uyari_sec(self.uyarilar.item(i))

    def _tik(self, anahtar, i, shift):
        k = self.secili['kagit'] if self.secili else None
        if not k:
            return
        if anahtar[0] == 'soru':
            n = anahtar[1]
            q = next(q for q in k.form.sorular if q['number'] == n)
            v = q['options'][i]['value']
            mevcut = set(filter(None, k.cevap(n).split('+')))
            if v in mevcut:
                mevcut.discard(v)
            elif shift:
                mevcut.add(v)
            else:
                mevcut = {v}
            k.elle_cevaplar[n] = '+'.join(sorted(mevcut))
        else:
            _, ad, ci = anahtar
            v = k.form.alanlar[ad]['columns'][ci][i]['value']
            k.elle_sutunlar[(ad, ci)] = '' if k.sutun_degeri(ad, ci) == v else v
        self.gor.odak = anahtar
        self.b.bildir('kontrol'); self._yeniden_hesapla()

    def _yeniden_hesapla(self):
        k = self.secili['kagit']
        self.sonuc = self.b.oturum.sonuclar()
        self.secili = next(s for s in self.sonuc if s['kagit'] is k)
        self.gor.ciz(); self._panel(); self.listele()

    def _geri_al(self):
        k = self.secili['kagit']
        k.elle_cevaplar.clear(); k.elle_sutunlar.clear(); k.elle_alanlar.clear(); k.onaylandi = False
        self.b.bildir('kontrol'); self._yeniden_hesapla()

    def onayla(self):
        """Seçili kâğıdı onaylar ya da onayını geri alır. Sonraki kâğıda geçmez."""
        if not self.secili:
            return
        k = self.secili['kagit']
        k.onaylandi = not k.onaylandi
        self.b.bildir('kontrol')
        self._yeniden_hesapla()

    def _git(self, yon):
        r = self.liste.currentRow() + yon
        if 0 <= r < self.liste.rowCount():
            self._satir_sec(r)

    def showEvent(self, e):
        super().showEvent(e)
        if not self.sonuc:
            self.yenile()
