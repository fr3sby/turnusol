"""5. adım: OBS not şablonu, Excel raporu, kontrol görüntüleri."""
import os
import cv2
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QColor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QCheckBox, QFileDialog, QMessageBox,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QFrame, QProgressDialog,
                               QApplication)

from .ortak import SayfaBasligi, Bildirim, Kutucuk, Etiket, etiket, dugme, ayirici
from .tema import R, MONO
from .. import okuma


class DisariSayfasi(QWidget):
    def __init__(self, baglam):
        super().__init__(); self.setObjectName('sayfa')
        self.b = baglam
        lay = QVBoxLayout(self); lay.setContentsMargins(32, 24, 32, 24); lay.setSpacing(20)
        bas = SayfaBasligi('Dışa Aktar',
                           'Notları not şablonuna yazdırın. OBS şablonu kullandıysanız doldurulan dosyayı OBS’de <b>Excel içeri al</b> düğmesiyle yükleyin. '
                           'Ayrıntılı sonuçları ve soru analizini görmek için Excel raporunu da kaydedebilirsiniz.', 'disari')
        bas.kilavuz.connect(self.b.kilavuz_ac)
        lay.addWidget(bas)

        oz = QHBoxLayout(); oz.setSpacing(1)
        self.k_puan = Kutucuk('—', 'Puanlanan kâğıt'); self.k_kontrol = Kutucuk('—', 'Kontrol bekleyen')
        self.k_girmeyen = Kutucuk('—', 'Sınav kâğıdı olmayan'); self.k_ort = Kutucuk('—', 'Ortalama puan')
        for k in (self.k_puan, self.k_kontrol, self.k_girmeyen, self.k_ort):
            oz.addWidget(k)
        lay.addLayout(oz)
        self.uyari = Bildirim('uyari', '', ''); lay.addWidget(self.uyari)

        govde = QHBoxLayout(); govde.setSpacing(24)
        # OBS şablonu
        s1 = QFrame(); s1.setObjectName('katman'); l1 = QVBoxLayout(s1); l1.setContentsMargins(20, 20, 20, 20); l1.setSpacing(12)
        l1.addWidget(etiket('Not şablonu', 'bolumBaslik'))
        self.s_yok = Bildirim('bilgi', '', 'Not şablonu yüklenmedi. Şablonu <b>Taramalar</b> adımındaki öğrenci listeleri bölümünden yükleyebilirsiniz.')
        l1.addWidget(self.s_yok)
        self.s_kutu = QWidget(); sk = QVBoxLayout(self.s_kutu); sk.setContentsMargins(0, 0, 0, 0); sk.setSpacing(8)
        sk.addWidget(etiket('Notun yazılacağı sütun', 'etiket'))
        self.sutun = QComboBox(); sk.addWidget(self.sutun)
        sk.addWidget(etiket('S1 birinci sınavın, S2 ikinci sınavın sütunudur. Daha önce not girilmiş sütunun yanında kaç öğrencinin notu olduğu yazar.', 'yardim', True))
        self.ustune = QCheckBox('Dolu notların üstüne yaz'); sk.addWidget(self.ustune)
        self.s_kaydet = dugme('Doldurulmuş şablonu kaydet…', 'birincil'); self.s_kaydet.clicked.connect(self.sablon_kaydet)
        sk.addWidget(self.s_kaydet, 0, Qt.AlignLeft)
        self.s_sonuc = etiket('', 'yardim', True); sk.addWidget(self.s_sonuc)
        l1.addWidget(self.s_kutu); l1.addStretch(1)
        govde.addWidget(s1, 1)
        # rapor
        s2 = QFrame(); s2.setObjectName('katman'); l2 = QVBoxLayout(s2); l2.setContentsMargins(20, 20, 20, 20); l2.setSpacing(12)
        l2.addWidget(etiket('Rapor ve kayıtlar', 'bolumBaslik'))
        l2.addWidget(etiket('Excel raporu sonuçları, öğrenci cevaplarını, soru analizini, kontrol listesini, sınıf listesi karşılaştırmasını ve cevap anahtarını içerir.', 'yardim', True))
        self.r_kaydet = dugme('Excel raporunu kaydet…', 'ikincil'); self.r_kaydet.clicked.connect(self.rapor_kaydet)
        l2.addWidget(self.r_kaydet, 0, Qt.AlignLeft)
        l2.addWidget(etiket('Kontrol görüntülerinde programın okuduğu şıklar her kâğıdın üzerinde işaretlidir. Bu görüntüleri itirazlar ve arşiv için saklayabilirsiniz.', 'yardim', True))
        self.g_kaydet = dugme('Kontrol görüntülerini kaydet…', 'ucuncul'); self.g_kaydet.clicked.connect(self.goruntu_kaydet)
        l2.addWidget(self.g_kaydet, 0, Qt.AlignLeft)
        l2.addStretch(1)
        govde.addWidget(s2, 1)
        lay.addLayout(govde)

        lay.addWidget(etiket('Notlar', 'bolumBaslik'))
        self.tablo = QTableWidget(0, 7)
        self.tablo.setHorizontalHeaderLabels(['Numara', 'Ad', 'Soyad', 'Kitapçık', 'Doğru', 'Yanlış', 'Puan'])
        self.tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo.verticalHeader().hide(); self.tablo.verticalHeader().setDefaultSectionSize(36)
        self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers); self.tablo.setShowGrid(False)
        self.tablo.setMinimumHeight(220)
        lay.addWidget(self.tablo, 1)
        self.b.degisti.connect(lambda ne: self.yenile())

    def showEvent(self, e):
        super().showEvent(e); self.yenile()

    def yenile(self):
        o = self.b.oturum
        s = o.sonuclar()
        puanli = [x for x in s if x['puan'] is not None]
        n_k = sum(1 for x in s if x['kontrol'])
        self.k_puan.ayarla(len(puanli))
        self.k_kontrol.ayarla(n_k, None, R['warning_text'] if n_k else None)
        self.k_girmeyen.ayarla(len(o.girmeyenler()) if (o.sinif_listesi or o.sablon) else '—')
        self.k_ort.ayarla(f'{sum(x["puan"] for x in puanli) / len(puanli):.1f}' if puanli else '—')
        mesaj = []
        if not o.anahtar.kitapciklar:
            mesaj.append('Cevap anahtarı girilmediği için program puan hesaplayamadı.')
        if n_k:
            mesaj.append(f'{n_k} kâğıt hâlâ kontrol bekliyor. Notları yine de dışa aktarabilirsiniz, ancak program bu kâğıtları okunduğu hâliyle puanlar.')
        self.uyari.ayarla('uyari', '', ' '.join(mesaj)); self.uyari.setVisible(bool(mesaj))
        # şablon
        self.s_yok.setVisible(o.sablon is None); self.s_kutu.setVisible(o.sablon is not None)
        if o.sablon:
            onceki = self.sutun.currentData()
            self.sutun.blockSignals(True); self.sutun.clear()
            for c in o.sablon.sinav_sutunlari:
                dolu = sum(1 for (n, b), v in o.sablon.mevcut.items() if b == c and v not in (None, ''))
                self.sutun.addItem(f'{c} sütunu ({dolu} öğrencinin notu var)' if dolu else f'{c} sütunu (boş)', c)
            # ilk boş sütunu öner
            i = next((i for i in range(self.sutun.count()) if '(boş)' in self.sutun.itemText(i)), 0)
            if onceki:
                i = max(0, self.sutun.findData(onceki))
            self.sutun.setCurrentIndex(i); self.sutun.blockSignals(False)
        self.s_kaydet.setEnabled(bool(puanli)); self.r_kaydet.setEnabled(bool(s)); self.g_kaydet.setEnabled(bool(s))
        # tablo
        t = self.tablo; sirali = sorted(s, key=lambda x: x['no'] or 'z'); t.setRowCount(len(sirali))
        for r, x in enumerate(sirali):
            p = x.get('puanlama') or {}
            vals = [x['no'], x['ad'], x['soyad'], x['kitapcik'], p.get('dogru', ''), p.get('yanlis', ''), '' if x['puan'] is None else x['puan']]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v)); t.setItem(r, c, it)
                if c in (0, 4, 5, 6): it.setFont(self._mono())
                if x['kontrol']: it.setBackground(QColor(R['bg_warning']))

    def _mono(self):
        f = self.font(); f.setFamily(MONO); return f

    def _ac(self, yol):
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(yol)))

    def sablon_kaydet(self):
        o = self.b.oturum
        c = self.sutun.currentData()
        oner = os.path.join(os.path.dirname(o.sablon.yol), os.path.splitext(os.path.basename(o.sablon.yol))[0] + f'_{c}_dolu.xlsx')
        yol, _ = QFileDialog.getSaveFileName(self, 'Doldurulmuş şablonu kaydet', oner, 'Excel (*.xlsx)')
        if not yol: return
        try:
            r = o.sablona_yaz(c, yol, self.ustune.isChecked())
        except Exception as e:
            QMessageBox.critical(self, 'Kaydedilemedi', str(e)); return
        satir = [f'Program {r["yazilan"]} öğrencinin notunu {os.path.basename(yol)} dosyasına yazdı.']
        if r['notu_olmayan']: satir.append(f'{len(r["notu_olmayan"])} öğrencinin sınav kâğıdı olmadığı için not alanları boş bırakıldı.')
        if r['sablonda_yok']: satir.append(f'Şablonda bulunmayan {len(r["sablonda_yok"])} numaranın notu yazılmadı: ' + ', '.join(r['sablonda_yok'][:6]) + '.')
        if r['dolu_atlanan']: satir.append(f'{len(r["dolu_atlanan"])} öğrencinin bu sütunda zaten notu olduğu için program o notların üstüne yazmadı.')
        self.s_sonuc.setText('<br>'.join(satir))

    def rapor_kaydet(self):
        o = self.b.oturum
        ilk = o.kagitlar[0].kaynak if o.kagitlar else os.path.expanduser('~')
        oner = os.path.join(os.path.dirname(ilk), 'sonuclar.xlsx')
        yol, _ = QFileDialog.getSaveFileName(self, 'Excel raporunu kaydet', oner, 'Excel (*.xlsx)')
        if not yol: return
        try:
            o.excel_yaz(yol)
        except Exception as e:
            QMessageBox.critical(self, 'Kaydedilemedi', str(e)); return
        self._ac(yol)

    def goruntu_kaydet(self):
        o = self.b.oturum
        d = QFileDialog.getExistingDirectory(self, 'Kontrol görüntülerinin kaydedileceği klasörü seçin')
        if not d: return
        hepsi = o.kagitlar + o.anahtar_kagitlari
        pd = QProgressDialog('Görüntüler kaydediliyor…', 'Durdur', 0, len(hepsi), self); pd.setWindowModality(Qt.WindowModal)
        for i, k in enumerate(hepsi):
            pd.setValue(i); QApplication.processEvents()
            if pd.wasCanceled(): break
            gri = self.b.goruntu(k.kaynak, k.sayfa)
            ad = f'{k.ogrenci_no or "okunamadi"}_{os.path.splitext(os.path.basename(k.kaynak))[0]}_s{k.sayfa}.jpg'
            ok, buf = cv2.imencode('.jpg', okuma.kontrol_goruntusu(gri, k), [cv2.IMWRITE_JPEG_QUALITY, 85])
            buf.tofile(os.path.join(d, ad))
        pd.setValue(len(hepsi))
        QDesktopServices.openUrl(QUrl.fromLocalFile(d))
