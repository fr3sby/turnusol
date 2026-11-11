"""2. adım: cevap anahtarı (kitapçık başına), iptal edilen sorular."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QButtonGroup,
                               QLineEdit, QSpinBox, QScrollArea, QFrame, QInputDialog, QLabel)

from .ortak import SayfaBasligi, Bildirim, Etiket, etiket, dugme
from .tema import R, MONO
from ..puanlama import CevapAnahtari

SIK = 'ABCDE'


class SoruSatiri(QWidget):
    """Bir sorunun anahtar satırı.
    Tıklama tek şık seçer; seçili şıkka tekrar tıklamak seçimi kaldırır; Shift ile tıklama ikinci doğru şık ekler."""
    degisti = Signal(int, str)
    secildi = Signal(int)

    def __init__(self, no):
        super().__init__()
        self.no = no
        lay = QHBoxLayout(self); lay.setContentsMargins(4, 0, 4, 0); lay.setSpacing(4)
        self.setFixedHeight(34)
        self.n = QLabel(f'{no}.'); self.n.setFixedWidth(34); self.n.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self.n); lay.addSpacing(6)
        self.d = []
        for c in SIK:
            b = QPushButton(c); b.setFixedSize(28, 28); b.setCursor(Qt.PointingHandCursor); b.setProperty('secili', False)
            b.setFocusPolicy(Qt.NoFocus)
            b.setStyleSheet(f"QPushButton {{ border:1px solid {R['border_strong']}; border-radius:14px; padding:0; min-height:0; "
                            f"text-align:center; background:{R['layer']}; color:{R['text_secondary']}; font-size:12px; }}"
                            f"QPushButton:hover {{ border-color:{R['text_primary']}; }}"
                            f"QPushButton[secili=\"true\"] {{ background:{R['text_primary']}; color:#fff; border-color:{R['text_primary']}; }}"
                            f"QPushButton:disabled {{ background:{R['layer']}; color:{R['text_disabled']}; border-color:{R['border_subtle']}; }}")
            b.clicked.connect(lambda _=False, cc=c: self._tiklandi(cc))
            self.d.append(b); lay.addWidget(b)
        lay.addStretch(1)
        self._iptal = False; self._aktif = False
        self._stil()

    def deger(self):
        return '/'.join(c for c, b in zip(SIK, self.d) if b.property('secili'))

    @staticmethod
    def _isaretle(b, secili):
        if bool(b.property('secili')) != secili:
            b.setProperty('secili', secili)
            b.style().unpolish(b); b.style().polish(b)

    def ayarla(self, v, iptal=False):
        secili = set(filter(None, (v or '').split('/')))
        for c, b in zip(SIK, self.d):
            self._isaretle(b, c in secili)
        self._iptal = iptal; self._stil()

    def changeEvent(self, e):
        super().changeEvent(e)
        if e.type() == e.Type.EnabledChange:
            self._stil()

    def aktif(self, a):
        self._aktif = a; self._stil()

    def _stil(self):
        renk = R['error'] if self._iptal else (R['text_primary'] if self.isEnabled() else R['text_disabled'])
        cizgi = 'text-decoration: line-through;' if self._iptal else ''
        self.n.setStyleSheet(f"font-family:'{MONO}'; font-weight:500; color:{renk}; {cizgi}")
        self.n.setToolTip('Bu soru iptal edildi.' if self._iptal else '')
        self.setStyleSheet(f"SoruSatiri {{ background:{R['tag_blue'][0]}; }}" if self._aktif else '')
        self.setAttribute(Qt.WA_StyledBackground, True)

    def sik_sec(self, c, ekle=False):
        """c şıkkını seçer. ekle=True ise mevcut seçime ekler/çıkarır."""
        mevcut = set(filter(None, self.deger().split('/')))
        if ekle:
            mevcut ^= {c}
        elif mevcut == {c}:
            mevcut = set()
        else:
            mevcut = {c}
        for cc, b in zip(SIK, self.d):
            self._isaretle(b, cc in mevcut)
        self.degisti.emit(self.no, self.deger())

    def temizle(self):
        for b in self.d:
            self._isaretle(b, False)
        self.degisti.emit(self.no, '')

    def _tiklandi(self, c):
        from PySide6.QtWidgets import QApplication
        self.sik_sec(c, bool(QApplication.keyboardModifiers() & Qt.ShiftModifier))
        self.secildi.emit(self.no)

    def mousePressEvent(self, e):
        self.secildi.emit(self.no)
        super().mousePressEvent(e)


class AnahtarSayfasi(QWidget):
    def __init__(self, baglam):
        super().__init__(); self.setObjectName('sayfa')
        self.b = baglam; self.kitapcik = ''; self.aktif_soru = None; self._kendi = False
        self.setFocusPolicy(Qt.StrongFocus)
        lay = QVBoxLayout(self); lay.setContentsMargins(32, 24, 32, 24); lay.setSpacing(20)
        bas = SayfaBasligi('Cevap Anahtarı',
                           'Cevap anahtarı taramadan geldiyse aşağıda hazır görünür ve sizin yalnızca kontrol etmeniz yeterlidir. '
                           'Taramada anahtar kâğıdı yoksa anahtarı şıklara tıklayarak ya da <b>Hızlı giriş</b> kutusuna yazarak girin. '
                           'Soruları istediğiniz sırayla girebilirsiniz.',
                           'anahtar')
        bas.kilavuz.connect(self.b.kilavuz_ac)
        lay.addWidget(bas)
        self.bilgi = Bildirim('bilgi', '', ''); lay.addWidget(self.bilgi)

        # kitapçık seçici (Carbon content switcher)
        ks = QHBoxLayout(); ks.setSpacing(0)
        ks.addWidget(etiket('Kitapçık', 'etiket')); ks.addSpacing(12)
        self.ks_kutu = QHBoxLayout(); self.ks_kutu.setSpacing(0); ks.addLayout(self.ks_kutu)
        self.grup = QButtonGroup(self); self.grup.setExclusive(True)
        self.grup.idClicked.connect(self._kitapcik_sec)
        ekle = dugme('+ Kitapçık ekle', 'hayalet'); ekle.clicked.connect(self._kitapcik_ekle)
        self.sil = dugme('Bu anahtarı sil', 'hayalet'); self.sil.clicked.connect(self._kitapcik_sil)
        ks.addSpacing(12); ks.addWidget(ekle); ks.addWidget(self.sil); ks.addStretch(1)
        lay.addLayout(ks)

        # hızlı giriş + soru sayısı
        ust = QHBoxLayout(); ust.setSpacing(16)
        k1 = QVBoxLayout(); k1.setSpacing(4); k1.addWidget(etiket('Hızlı giriş', 'etiket'))
        self.hizli = QLineEdit(); self.hizli.setPlaceholderText('Örnek: ABCDEABCDE ya da 1A 2B 3C')
        self.hizli.returnPressed.connect(self._hizli_uygula)
        k1.addWidget(self.hizli); ust.addLayout(k1, 3)
        k2 = QVBoxLayout(); k2.setSpacing(4); k2.addWidget(etiket('Sınavdaki soru sayısı', 'etiket'))
        self.soru_sayisi = QSpinBox(); self.soru_sayisi.setRange(1, 100); self.soru_sayisi.setValue(50)
        self.soru_sayisi.valueChanged.connect(self._soru_sayisi_degisti)
        k2.addWidget(self.soru_sayisi); ust.addLayout(k2, 1)
        k3 = QVBoxLayout(); k3.setSpacing(4); k3.addWidget(etiket('İptal edilen sorular', 'etiket'))
        self.iptal = QLineEdit(); self.iptal.setPlaceholderText('Örnek: 7, 12')
        self.iptal.editingFinished.connect(self._iptal_degisti)
        k3.addWidget(self.iptal); ust.addLayout(k3, 1)
        lay.addLayout(ust)
        lay.addWidget(etiket('Hızlı giriş kutusuna yazdıktan sonra Enter tuşuna basın. Boş bırakmak istediğiniz soru için tire (-) yazın. '
                             'Program, sınavdaki soru sayısından sonraki soruları puanlamaz.', 'yardim', True))
        lay.addWidget(etiket('Şıklara tıklayarak da girebilirsiniz. Bir şıkka tıklamak o şıkkı seçer, aynı şıkka tekrar tıklamak seçimi kaldırır. '
                             'Bir soruda birden fazla şık doğru sayılacaksa diğer şıklara Shift tuşuna basılı tutarak tıklayın. '
                             'Bir soruyu seçtikten sonra klavyeden A, B, C, D ya da E tuşuna basarsanız o soru dolar ve sıradaki soru seçilir. '
                             'Boşluk tuşu soruyu boş bırakır, ok tuşları sorular arasında gezdirir.', 'yardim', True))

        # ızgara
        self.izgara_kap = QFrame(); self.izgara_kap.setObjectName('katman')
        self.izgara = QGridLayout(self.izgara_kap); self.izgara.setContentsMargins(24, 16, 24, 16)
        self.izgara.setHorizontalSpacing(40); self.izgara.setVerticalSpacing(6)
        self.satirlar = {}
        lay.addWidget(self.izgara_kap)
        lay.addStretch(1)
        self.b.degisti.connect(self._dis_degisim)
        self.yenile()

    # ---------- yardımcılar ----------
    @property
    def A(self):
        return self.b.oturum.anahtar

    def _form_soru_sayisi(self):
        o = self.b.oturum
        fs = [k.form.soru_sayisi for k in o.kagitlar + o.anahtar_kagitlari if k.form]
        return max(fs) if fs else 50

    def _izgarayi_kur(self, n):
        if len(self.satirlar) == n:
            return
        while self.izgara.count():
            w = self.izgara.takeAt(0).widget()
            if w: w.hide(); w.setParent(None); w.deleteLater()
        self.satirlar = {}
        sutun_basi = 10 if n <= 50 else (15 if n <= 75 else 20)
        for q in range(1, n + 1):
            s = SoruSatiri(q); s.degisti.connect(self._sik_degisti); s.secildi.connect(self._soru_sec)
            self.satirlar[q] = s
            self.izgara.addWidget(s, (q - 1) % sutun_basi, (q - 1) // sutun_basi)

    def _kitapcik_dugmeleri(self):
        while self.ks_kutu.count():
            w = self.ks_kutu.takeAt(0).widget()
            if w: self.grup.removeButton(w); w.hide(); w.setParent(None); w.deleteLater()
        adlar = self.A.kitapcik_listesi() or ['']
        if self.kitapcik not in adlar:
            self.kitapcik = adlar[0]
        for i, k in enumerate(adlar):
            d = QPushButton(k or 'Tek anahtar'); d.setCheckable(True); d.setCursor(Qt.PointingHandCursor)
            d.setStyleSheet(f"QPushButton {{ border:1px solid {R['text_primary']}; background:transparent; min-height:32px; "
                            f"padding:0 16px; text-align:center; color:{R['text_secondary']}; }}"
                            f"QPushButton:hover {{ background:{R['layer_hover']}; color:{R['text_primary']}; }}"
                            f"QPushButton:checked {{ background:{R['text_primary']}; color:#fff; }}")
            self.grup.addButton(d, i); self.ks_kutu.addWidget(d)
            d.setChecked(k == self.kitapcik)
        self._adlar = adlar
        self.sil.setVisible(bool(self.A.kitapciklar.get(self.kitapcik)))

    def yenile(self, tarama=False):
        o = self.b.oturum
        n_form = self._form_soru_sayisi()
        self.soru_sayisi.setMaximum(n_form)
        self._izgarayi_kur(n_form)
        self._kitapcik_dugmeleri()
        a = self.A.kitapciklar.get(self.kitapcik, {})
        dolu = [q for q, v in a.items() if v]
        self.soru_sayisi.blockSignals(True)
        if tarama and dolu:
            self.soru_sayisi.setValue(max(dolu))        # anahtar taramadan geldiyse soru sayısı ondan alınır
            self.A.soru_sayisi = max(dolu) if max(dolu) < n_form else 0
        elif self.A.soru_sayisi:
            self.soru_sayisi.setValue(min(self.A.soru_sayisi, n_form))
        else:
            self.soru_sayisi.setValue(n_form)
        self.soru_sayisi.blockSignals(False)
        for q, s in self.satirlar.items():
            s.ayarla(a.get(q, ''), q in self.A.iptal)
            s.setEnabled(q <= self.soru_sayisi.value())
        self.iptal.setText(', '.join(map(str, sorted(self.A.iptal))))
        # bilgi kutusu
        if o.anahtar_kagitlari:
            kits = sorted(k.kitapcik for k in o.anahtar_kagitlari if k.kitapcik)
            if kits:
                ne = ' ve '.join(kits) + (' kitapçıklarının' if len(kits) > 1 else ' kitapçığının')
                metin = f'Program taramada {ne} cevap anahtarı kâğıdını buldu.'
            else:
                metin = 'Program taramada cevap anahtarı kâğıdını buldu.'
            if o.anahtar_uyarilari:
                metin += '<br>' + '<br>'.join(o.anahtar_uyarilari[:5])
            else:
                metin += ' Anahtarı aşağıdan kontrol edebilirsiniz.'
            self.bilgi.ayarla('uyari' if o.anahtar_uyarilari else 'basari', '', metin)
        elif self.A.kitapciklar:
            self.bilgi.ayarla('bilgi', '', 'Cevap anahtarını elle girdiniz.')
        else:
            self.bilgi.ayarla('bilgi', '', 'Taramada cevap anahtarı kâğıdı bulunamadı. Anahtarı şıklara tıklayarak ya da '
                              'Hızlı giriş kutusuna yazarak girebilirsiniz. Anahtarı optik formla vermek isterseniz '
                              'öğrenci numarasının doldurulabilen bütün hanelerine <b>9</b> kodlayın ve kâğıdı taramaya ekleyin.')

    # ---------- olaylar ----------
    def _dis_degisim(self, ne):
        if ne == 'tarama':
            self.yenile(tarama=True)
        elif ne == 'anahtar' and not self._kendi:
            self.yenile()

    def _kitapcik_sec(self, i):
        self.kitapcik = self._adlar[i]; self.yenile()

    def _kitapcik_ekle(self):
        mevcut = set(self.A.kitapciklar)
        oneri = next((c for c in 'ABCDEF' if c not in mevcut), '')
        k, ok = QInputDialog.getItem(self, 'Kitapçık ekle', 'Eklemek istediğiniz kitapçık türünü seçin.', [c for c in 'ABCDEF' if c not in mevcut], 0, False)
        if ok and k:
            if '' in self.A.kitapciklar and not self.A.kitapciklar['']:
                del self.A.kitapciklar['']
            self.A.kitapciklar[k] = {}
            self.kitapcik = k; self.b.bildir('anahtar')

    def _kitapcik_sil(self):
        self.A.kitapciklar.pop(self.kitapcik, None); self.kitapcik = ''; self.b.bildir('anahtar')

    def _sik_degisti(self, q, v):
        self.A.kitapciklar.setdefault(self.kitapcik, {})[q] = v
        self.sil.setVisible(True)
        self._kendi = True
        try:
            self.b.bildir('anahtar')       # diğer adımlar güncellenir; bu sayfa yeniden çizilmez
        finally:
            self._kendi = False

    def _soru_sec(self, q):
        if self.aktif_soru in self.satirlar:
            self.satirlar[self.aktif_soru].aktif(False)
        self.aktif_soru = q
        if q in self.satirlar:
            self.satirlar[q].aktif(True)
        self.setFocus()

    def keyPressEvent(self, e):
        q = self.aktif_soru
        if q is None or q not in self.satirlar:
            return super().keyPressEvent(e)
        metin = e.text().upper()
        n = self.soru_sayisi.value()
        if metin in tuple(SIK):
            ekle = bool(e.modifiers() & Qt.ShiftModifier)
            self.satirlar[q].sik_sec(metin, ekle)
            if not ekle and q < n:
                self._soru_sec(q + 1)
        elif e.key() in (Qt.Key_Space, Qt.Key_Minus, Qt.Key_Backspace, Qt.Key_Delete):
            self.satirlar[q].temizle()
            if e.key() != Qt.Key_Backspace and q < n:
                self._soru_sec(q + 1)
            elif e.key() == Qt.Key_Backspace and q > 1:
                self._soru_sec(q - 1)
        elif e.key() in (Qt.Key_Down, Qt.Key_Right) and q < n:
            self._soru_sec(q + 1)
        elif e.key() in (Qt.Key_Up, Qt.Key_Left) and q > 1:
            self._soru_sec(q - 1)
        else:
            super().keyPressEvent(e)

    def _hizli_uygula(self):
        metin = self.hizli.text().strip()
        if not metin:
            return
        a = CevapAnahtari.metinden(metin, len(self.satirlar))
        hedef = self.A.kitapciklar.setdefault(self.kitapcik, {})
        hedef.update(a)
        self.hizli.clear(); self.b.bildir('anahtar')

    def _soru_sayisi_degisti(self, n):
        # anahtar silinmez; sınırın ötesindeki sorular yalnızca puanlanmaz
        self.A.soru_sayisi = n if n < len(self.satirlar) else 0
        for q, s in self.satirlar.items():
            s.setEnabled(q <= n)
        self._kendi = True
        try:
            self.b.bildir('anahtar')
        finally:
            self._kendi = False

    def _iptal_degisti(self):
        try:
            self.A.iptal = {int(x) for x in self.iptal.text().replace(' ', '').split(',') if x}
        except ValueError:
            return
        self.b.bildir('anahtar')
