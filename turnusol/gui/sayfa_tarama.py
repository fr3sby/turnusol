"""1. adım: taramaları ve (isteğe bağlı) OBS dosyalarını ekle, oku."""
import os
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
                               QHeaderView, QProgressBar, QAbstractItemView, QMessageBox, QFrame)

from .formlar import sablonu_kaydet
from .ortak import SayfaBasligi, DosyaAlani, Bildirim, Kutucuk, Etiket, etiket, dugme, ayirici
from .tema import R
from .. import girdi


class OkumaIsi(QThread):
    ilerleme = Signal(int, int, str)
    bitti = Signal(str)

    def __init__(self, baglam, yollar):
        super().__init__()
        self.baglam, self.yollar, self.iptal = baglam, yollar, False

    def run(self):
        try:
            def ilerle(i, n, k):
                self.ilerleme.emit(i, n, f'{os.path.basename(k.kaynak)} dosyasının {k.sayfa}. sayfası')
                return not self.iptal
            self.baglam.oturum.tara(self.yollar, ilerleme=ilerle)
            self.bitti.emit('')
        except Exception as e:  # kullanıcıya göster
            self.bitti.emit(str(e))


class ObsKutusu(QFrame):
    """Sınıf listesi / not şablonu yükleme kutusu."""
    def __init__(self, baslik, aciklama, filtre, yukle, kaldir):
        super().__init__(); self.setObjectName('katman')
        self.yukle_f, self.kaldir_f = yukle, kaldir
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 16, 16, 16); lay.setSpacing(8)
        ust = QHBoxLayout(); ust.addWidget(etiket(baslik, 'bolumBaslik')); ust.addStretch(1)
        self.durum = Etiket('Yüklenmedi', 'gray'); ust.addWidget(self.durum)
        lay.addLayout(ust)
        lay.addWidget(etiket(aciklama, 'yardim', True))
        self.alan = DosyaAlani('<b>Dosyayı buraya sürükleyin</b> ya da <span style="color:#0f62fe">tıklayıp seçin.</span>', filtre, coklu=False)
        self.alan.setMinimumHeight(56)
        self.alan.dosyalar.connect(lambda y: self._yukle(y[0]))
        lay.addWidget(self.alan)
        self.bilgi = etiket('', 'yardim', True); lay.addWidget(self.bilgi)
        self.kaldir = dugme('Kaldır', 'hayalet'); self.kaldir.clicked.connect(self._kaldir); self.kaldir.hide()
        lay.addWidget(self.kaldir, 0, Qt.AlignLeft)

    def _yukle(self, yol):
        try:
            bilgi = self.yukle_f(yol)
        except Exception as e:
            QMessageBox.warning(self, 'Dosya okunamadı', str(e)); return
        self.goster(os.path.basename(yol), bilgi)

    def goster(self, dosya, bilgi):
        self.durum.setText('Yüklendi'); self.durum.renk('green')
        self.bilgi.setText(f'<b>{dosya}</b><br>{bilgi}'); self.kaldir.show(); self.alan.hide()

    def _kaldir(self):
        self.kaldir_f(); self.durum.setText('Yüklenmedi'); self.durum.renk('gray')
        self.bilgi.setText(''); self.kaldir.hide(); self.alan.show()


class TaramaSayfasi(QWidget):
    def __init__(self, baglam):
        super().__init__(); self.setObjectName('sayfa')
        self.b = baglam; self.is_ = None
        lay = QVBoxLayout(self); lay.setContentsMargins(32, 24, 32, 24); lay.setSpacing(24)
        bas = SayfaBasligi('Taramalar',
                           'Taranmış optik formları aşağıdaki alana ekleyin ve <b>Oku</b> düğmesine basın. '
                           'Cevap anahtarını optik formla hazırladıysanız o kâğıdı da aynı taramaya koyabilirsiniz. '
                           'Program, öğrenci numarasının doldurulabilen bütün hanelerine <b>9</b> kodlanmış kâğıdı cevap anahtarı olarak ayırır.',
                           'tarama')
        bas.kilavuz.connect(self.b.kilavuz_ac)
        lay.addWidget(bas)

        govde = QHBoxLayout(); govde.setSpacing(24)
        # --- sol: taramalar ---
        sol = QVBoxLayout(); sol.setSpacing(12)
        sol.addWidget(etiket('Optik taramalar', 'bolumBaslik'))
        self.alan = DosyaAlani('<b>Dosyaları buraya sürükleyin</b> ya da <span style="color:#0f62fe">tıklayıp seçin.</span>'
                               '<br><span style="color:#6f6f6f; font-size:12px">Program PDF, JPG, PNG ve TIFF dosyalarını okur. '
                               'Çok sayfalı bir PDF ya da birden fazla dosya ekleyebilirsiniz.</span>',
                               'Taramalar (*.pdf *.jpg *.jpeg *.png *.tif *.tiff *.bmp)')
        self.alan.dosyalar.connect(self.ekle)
        sol.addWidget(self.alan)
        self.tablo = QTableWidget(0, 3)
        self.tablo.setHorizontalHeaderLabels(['Dosya', 'Sayfa', ''])
        self.tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tablo.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tablo.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tablo.verticalHeader().hide(); self.tablo.verticalHeader().setDefaultSectionSize(40)
        self.tablo.setSelectionMode(QAbstractItemView.NoSelection); self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo.setShowGrid(False); self.tablo.setMinimumHeight(140)
        sol.addWidget(self.tablo, 1)
        sat = QHBoxLayout(); sat.setSpacing(1)
        self.oku = dugme('Oku', 'birincil', 'Ctrl+R', 'Eklenen taramaları okur (Ctrl+R)')
        self.oku.clicked.connect(self.basla)
        self.temizle = dugme('Listeyi temizle', 'hayalet'); self.temizle.clicked.connect(self.listeyi_temizle)
        sat.addWidget(self.oku); sat.addSpacing(8); sat.addWidget(self.temizle); sat.addStretch(1)
        sol.addLayout(sat)
        self.cubuk = QProgressBar(); self.cubuk.hide(); sol.addWidget(self.cubuk)
        self.cubuk_yazi = etiket('', 'yardim'); self.cubuk_yazi.hide(); sol.addWidget(self.cubuk_yazi)
        govde.addLayout(sol, 3)

        # --- sağ: OBS dosyaları ---
        sag = QVBoxLayout(); sag.setSpacing(12)
        ust = QHBoxLayout(); ust.addWidget(etiket('Öğrenci listeleri', 'bolumBaslik')); ust.addWidget(Etiket('isteğe bağlı', 'gray'))
        ust.addStretch(1); sag.addLayout(ust)
        ne = dugme('Bu dosyaları OBS’den nasıl indiririm?', 'hayalet'); ne.clicked.connect(lambda: self.b.kilavuz_ac.emit('obs'))
        self.liste_kutu = ObsKutusu('Sınıf listesi', 'Program öğrenci adlarını bu listeden alır ve listede olmayan numaraları size bildirir. '
                                    'OBS listesi yerine programın Excel şablonunu da kullanabilirsiniz.',
                                    'Sınıf listesi (*.xls *.xlsx)', self._liste_yukle, self._liste_kaldir)
        self.sablon_kutu = ObsKutusu('Not şablonu', 'Program notları bu şablona yazar. Doldurulan şablonu OBS’ye doğrudan yükleyebilirsiniz.',
                                     'Not şablonu (*.xlsx)', self._sablon_yukle, self._sablon_kaldir)
        sab = dugme('Boş Excel öğrenci listesi şablonunu kaydet', 'hayalet')
        sab.clicked.connect(lambda: sablonu_kaydet(self))
        sag.addWidget(self.liste_kutu); sag.addWidget(self.sablon_kutu); sag.addWidget(ne, 0, Qt.AlignLeft)
        sag.addWidget(sab, 0, Qt.AlignLeft)
        sag.addStretch(1)
        govde.addLayout(sag, 2)
        lay.addLayout(govde, 1)

        # --- özet ---
        self.ozet_bas = etiket('Okuma sonucu', 'bolumBaslik'); self.ozet_bas.hide()
        lay.addWidget(self.ozet_bas)
        ozet = QHBoxLayout(); ozet.setSpacing(1)
        self.k_okunan = Kutucuk('—', 'Öğrenci kâğıdı'); self.k_anahtar = Kutucuk('—', 'Cevap anahtarı kâğıdı')
        self.k_kontrol = Kutucuk('—', 'Kontrol gerekiyor'); self.k_okunamayan = Kutucuk('—', 'Okunamadı')
        self.kutular = [self.k_okunan, self.k_anahtar, self.k_kontrol, self.k_okunamayan]
        for k in self.kutular:
            ozet.addWidget(k); k.hide()
        lay.addLayout(ozet)
        self.sonraki = dugme('Cevap anahtarı adımına geç', 'ikincil'); self.sonraki.hide()
        self.sonraki.clicked.connect(lambda: self.b.adima_git.emit(1))
        lay.addWidget(self.sonraki, 0, Qt.AlignLeft)
        self._tabloyu_yenile()

    # --- dosya listesi ---
    def ekle(self, yollar):
        for y in girdi.dosyalari_bul(yollar):
            if y not in self.b.taranacaklar:
                self.b.taranacaklar.append(y)
        self._tabloyu_yenile()

    def listeyi_temizle(self):
        self.b.taranacaklar.clear(); self._tabloyu_yenile()

    def _tabloyu_yenile(self):
        t = self.tablo; t.setRowCount(0)
        for y in self.b.taranacaklar:
            r = t.rowCount(); t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(os.path.basename(y)))
            t.item(r, 0).setToolTip(y)
            try:
                n = girdi.sayfa_sayisi([y])
            except Exception:
                n = '?'
            it = QTableWidgetItem(str(n)); it.setTextAlignment(Qt.AlignCenter); t.setItem(r, 1, it)
            sil = dugme('Çıkar', 'hayalet'); sil.setMinimumHeight(32); sil.setMinimumWidth(84)
            sil.clicked.connect(lambda _=False, yy=y: (self.b.taranacaklar.remove(yy), self._tabloyu_yenile()))
            t.setCellWidget(r, 2, sil)
        self.oku.setEnabled(bool(self.b.taranacaklar))
        self.temizle.setVisible(bool(self.b.taranacaklar))

    # --- okuma ---
    def basla(self):
        if self.is_ and self.is_.isRunning():
            self.is_.iptal = True; return
        self.b.sifirla_okuma()
        self.oku.setText('Durdur'); self.oku.setObjectName('ikincil'); self.oku.style().unpolish(self.oku); self.oku.style().polish(self.oku)
        self.cubuk.setValue(0); self.cubuk.show(); self.cubuk_yazi.show()
        self.is_ = OkumaIsi(self.b, list(self.b.taranacaklar))
        self.is_.ilerleme.connect(self._ilerle); self.is_.bitti.connect(self._bitti)
        self.is_.start()

    def _ilerle(self, i, n, ad):
        self.cubuk.setMaximum(n); self.cubuk.setValue(i)
        self.cubuk_yazi.setText(f'{n} sayfanın {i} tanesi okundu. Şu anda {ad} okunuyor.')

    def _bitti(self, hata):
        self.oku.setText('Yeniden oku'); self.oku.setObjectName('birincil'); self.oku.style().unpolish(self.oku); self.oku.style().polish(self.oku)
        self.cubuk.hide(); self.cubuk_yazi.hide()
        if hata:
            QMessageBox.critical(self, 'Okuma hatası', hata)
        self.b.bildir('tarama')
        self.ozeti_guncelle()

    def ozeti_guncelle(self):
        o = self.b.oturum
        if not o.kagitlar and not o.anahtar_kagitlari:
            return
        s = o.sonuclar()
        self.ozet_bas.show(); self.sonraki.show()
        for k in self.kutular: k.show()
        self.k_okunan.ayarla(len(o.kagitlar))
        kits = ', '.join(sorted(k.kitapcik or 'tek' for k in o.anahtar_kagitlari))
        self.k_anahtar.ayarla(len(o.anahtar_kagitlari), 'Cevap anahtarı kâğıdı' + (f' ({kits})' if kits else ''))
        n_k = sum(1 for x in s if x['kontrol'])
        self.k_kontrol.ayarla(n_k, None, R['warning_text'] if n_k else None)
        n_o = sum(1 for k in o.kagitlar if k.okunamadi)
        self.k_okunamayan.ayarla(n_o, None, R['error'] if n_o else None)

    # --- OBS ---
    def _liste_yukle(self, yol):
        self.b.oturum.sinif_listesi_yukle(yol); self.b.bildir('liste')
        sl = self.b.oturum.sinif_listesi
        return f'Listede {len(sl.ogrenciler)} öğrenci var.' + (f' Ders bilgisi: {sl.ders}.' if sl.ders else '')

    def _liste_kaldir(self):
        self.b.oturum.sinif_listesi = None; self.b.bildir('liste')

    def _sablon_yukle(self, yol):
        self.b.oturum.sablon_yukle(yol); self.b.bildir('liste')
        sb = self.b.oturum.sablon
        dolu = {c: sum(1 for (n, b), v in sb.mevcut.items() if b == c and v not in (None, '')) for c in sb.sinav_sutunlari}
        return f'Şablonda {len(sb.satirlar)} öğrenci var. ' + ' '.join(
            (f'{c} sütununda {d} öğrencinin notu var.' if d else f'{c} sütunu boş.') for c, d in dolu.items())

    def _sablon_kaldir(self):
        self.b.oturum.sablon = None; self.b.bildir('liste')
