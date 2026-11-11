"""Uygulamanın paylaşılan durumu: oturum + değişiklik sinyali + sayfa görüntüsü önbelleği."""
from collections import OrderedDict
from PySide6.QtCore import QObject, Signal

from ..oturum import Oturum
from .. import girdi


class Baglam(QObject):
    degisti = Signal(str)          # neyin değiştiği: 'tarama', 'liste', 'anahtar', 'puan', 'kontrol'
    kilavuz_ac = Signal(str)       # kılavuz bölümü
    adima_git = Signal(int)

    def __init__(self):
        super().__init__()
        self.oturum = Oturum()
        self.taranacaklar = []      # kullanıcının eklediği dosyalar
        self._onbellek = OrderedDict()

    def sifirla_okuma(self):
        o = self.oturum
        o.kagitlar.clear(); o.anahtar_kagitlari.clear(); o.anahtar_uyarilari.clear()
        # elle girilmiş anahtarlar korunur, taramadan gelenler yeniden okunacak
        self._onbellek.clear()

    def goruntu(self, kaynak, sayfa):
        anahtar = (kaynak, sayfa)
        if anahtar in self._onbellek:
            self._onbellek.move_to_end(anahtar)
            return self._onbellek[anahtar]
        img = girdi.sayfa_goruntusu(kaynak, sayfa)
        self._onbellek[anahtar] = img
        while len(self._onbellek) > 6:
            self._onbellek.popitem(last=False)
        return img

    def bildir(self, ne):
        self.degisti.emit(ne)
