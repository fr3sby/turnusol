"""3. adım: puanlama ayarları ve önizleme."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup, QLineEdit,
                               QDoubleSpinBox, QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
                               QAbstractItemView, QFrame)

from .ortak import SayfaBasligi, Bildirim, Katlanir, etiket, dugme
from .tema import R
from ..puanlama import soru_puanlari, araliklari_coz


class PuanSayfasi(QWidget):
    def __init__(self, baglam):
        super().__init__(); self.setObjectName('sayfa')
        self.b = baglam
        lay = QVBoxLayout(self); lay.setContentsMargins(32, 24, 32, 24); lay.setSpacing(24)
        bas = SayfaBasligi('Puanlama',
                           'Program varsayılan olarak her soruya eşit puan verir, toplam puanı 100 kabul eder ve notu tam sayıya yuvarlar. '
                           'Farklı bir puanlama istiyorsanız aşağıdaki ayarları değiştirin. Sağdaki tablo her sorunun kaç puan ettiğini gösterir.',
                           'puan')
        bas.kilavuz.connect(self.b.kilavuz_ac)
        lay.addWidget(bas)
        govde = QHBoxLayout(); govde.setSpacing(32)

        # --- sol: ayarlar ---
        sol = QVBoxLayout(); sol.setSpacing(16)
        sol.addWidget(etiket('Toplam puan', 'etiket'))
        self.toplam = QDoubleSpinBox(); self.toplam.setRange(1, 1000); self.toplam.setDecimals(0); self.toplam.setValue(100)
        self.toplam.setMaximumWidth(200); sol.addWidget(self.toplam)

        sol.addWidget(etiket('Soru puanları', 'etiket'))
        self.esit = QRadioButton('Her soru eşit puan'); self.ozel = QRadioButton('Sorulara farklı puan ver')
        g = QButtonGroup(self); g.addButton(self.esit); g.addButton(self.ozel); self.esit.setChecked(True)
        sol.addWidget(self.esit); sol.addWidget(self.ozel)
        self.ozel_metin = QLineEdit(); self.ozel_metin.setPlaceholderText('Örnek: 1-5:4; 6-40:2')
        self.ozel_yardim = etiket('Soru aralığını ve puanını iki nokta ile ayırın, farklı aralıkları noktalı virgülle ayırın. '
                                  'Belirtmediğiniz sorular kalan puanı eşit olarak paylaşır. Bütün soruları belirtirseniz toplam puan, '
                                  'girdiğiniz puanların toplamı olur.', 'yardim', True)
        sol.addWidget(self.ozel_metin); sol.addWidget(self.ozel_yardim)

        gelismis = QWidget(); gl = QVBoxLayout(gelismis); gl.setContentsMargins(8, 12, 8, 12); gl.setSpacing(12)
        self.yanlis = QCheckBox('Yanlışlar doğruyu götürsün')
        yr = QHBoxLayout(); yr.setSpacing(8)
        self.yanlis_k = QSpinBox(); self.yanlis_k.setRange(2, 10); self.yanlis_k.setValue(4); self.yanlis_k.setMaximumWidth(90)
        yr.addSpacing(24); yr.addWidget(self.yanlis_k); yr.addWidget(etiket('yanlış 1 doğruyu götürür', 'talimat')); yr.addStretch(1)
        gl.addWidget(self.yanlis); gl.addLayout(yr)
        gl.addWidget(etiket('İptal edilen sorular', 'etiket'))
        self.iptal_herkes = QRadioButton('Herkese doğru sayılsın'); self.iptal_dagit = QRadioButton('Puanı diğer sorulara dağıtılsın')
        g2 = QButtonGroup(self); g2.addButton(self.iptal_herkes); g2.addButton(self.iptal_dagit); self.iptal_herkes.setChecked(True)
        gl.addWidget(self.iptal_herkes); gl.addWidget(self.iptal_dagit)
        self.iptal_bilgi = etiket('', 'yardim', True); gl.addWidget(self.iptal_bilgi)
        self.yuvarla = QCheckBox('Notu tam sayıya yuvarla'); self.yuvarla.setChecked(True)
        gl.addWidget(self.yuvarla)
        sol.addWidget(Katlanir('Gelişmiş ayarlar', gelismis, acik=False))
        sol.addStretch(1)
        govde.addLayout(sol, 1)

        # --- sağ: önizleme ---
        sag = QVBoxLayout(); sag.setSpacing(8)
        sag.addWidget(etiket('Soru başına puan', 'bolumBaslik'))
        self.uyari = Bildirim('hata', '', ''); self.uyari.hide(); sag.addWidget(self.uyari)
        self.tablo = QTableWidget(0, 4)
        self.tablo.setHorizontalHeaderLabels(['Soru', 'Puan', 'Soru', 'Puan'])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.verticalHeader().hide(); self.tablo.verticalHeader().setDefaultSectionSize(32)
        self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers); self.tablo.setSelectionMode(QAbstractItemView.NoSelection)
        self.tablo.setShowGrid(False)
        sag.addWidget(self.tablo, 1)
        self.toplam_yazi = etiket('', 'talimat'); sag.addWidget(self.toplam_yazi)
        govde.addLayout(sag, 1)
        lay.addLayout(govde, 1)

        for w in (self.toplam, self.yanlis_k):
            w.valueChanged.connect(self.uygula)
        for w in (self.esit, self.ozel, self.yanlis, self.iptal_herkes, self.iptal_dagit, self.yuvarla):
            w.toggled.connect(self.uygula)
        self.ozel_metin.textChanged.connect(self.uygula)
        self.b.degisti.connect(lambda ne: self.onizle() if ne in ('anahtar', 'tarama') else None)
        self.uygula()

    def uygula(self, *_):
        p = self.b.oturum.puan_ayari
        p.toplam = self.toplam.value()
        p.ozel_puanlar = self.ozel_metin.text() if self.ozel.isChecked() else ''
        p.yanlis_goturur = self.yanlis_k.value() if self.yanlis.isChecked() else 0
        p.iptal_politikasi = 'dagit' if self.iptal_dagit.isChecked() else 'herkese_dogru'
        p.yuvarla = self.yuvarla.isChecked()
        self.ozel_metin.setEnabled(self.ozel.isChecked()); self.ozel_yardim.setEnabled(self.ozel.isChecked())
        self.yanlis_k.setEnabled(self.yanlis.isChecked())
        self.onizle()
        self.b.bildir('puan')

    def onizle(self):
        o = self.b.oturum
        sorular = o.anahtar.sinav_sorulari()
        if not sorular:
            n = max([k.form.soru_sayisi for k in o.kagitlar if k.form] or [50])
            sorular = list(range(1, n + 1))
            self.toplam_yazi.setText('Cevap anahtarı henüz girilmediği için tablo formdaki bütün soruları gösteriyor.')
        iptal = o.anahtar.iptal
        ip = [str(x) for x in sorted(iptal)]
        ip_metin = (' ve '.join(ip) if len(ip) <= 2 else ', '.join(ip[:-1]) + ' ve ' + ip[-1])
        self.iptal_bilgi.setText((f'Şu anda {ip_metin}. sorular iptal edildi.' if len(ip) > 1 else f'Şu anda {ip_metin}. soru iptal edildi.') if iptal
                                 else 'İptal edilecek soruları Cevap Anahtarı adımında girebilirsiniz.')
        try:
            P = soru_puanlari(sorular, iptal, o.puan_ayari)
            self.uyari.hide()
        except ValueError as e:
            self.uyari.ayarla('hata', '', str(e)); self.uyari.show()
            return
        yari = (len(sorular) + 1) // 2
        self.tablo.setRowCount(yari)
        def hucre(v, sag=False, soluk=False):
            it = QTableWidgetItem(v)
            it.setTextAlignment((Qt.AlignRight if sag else Qt.AlignLeft) | Qt.AlignVCenter)
            if soluk: it.setForeground(Qt.gray)
            return it
        for i, q in enumerate(sorular):
            r, c = i % yari, (i // yari) * 2
            ip = q in iptal
            self.tablo.setItem(r, c, hucre(f'{q}' + ('  (iptal)' if ip else ''), soluk=ip))
            self.tablo.setItem(r, c + 1, hucre(f'{P[q]:.2f}'.rstrip('0').rstrip('.'), True, ip and o.puan_ayari.iptal_politikasi == 'dagit'))
        for r in range(len(sorular) - yari if len(sorular) % 2 else yari):
            pass
        top = sum(P.values())
        ek = (f' {o.puan_ayari.yanlis_goturur} yanlış bir doğruyu götürür.' if o.puan_ayari.yanlis_goturur else '')
        if o.anahtar.sinav_sorulari():
            self.toplam_yazi.setText(f'Sınavda {len(sorular)} soru var ve toplam puan {top:g}.{ek}')
