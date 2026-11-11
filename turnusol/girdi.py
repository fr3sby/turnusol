"""Tarama girdileri: çok sayfalı PDF, tek resim ya da resim klasörü."""
import os
import numpy as np
import cv2

RESIM_UZANTI = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
PDF_DPI = 250


def _oku_resim(yol):
    # Türkçe karakterli yollar için imdecode
    veri = np.fromfile(yol, dtype=np.uint8)
    img = cv2.imdecode(veri, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f'Resim okunamadı: {yol}')
    return img


def _gri(img):
    if img.ndim == 2:
        return img
    if img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def _tiff_sayfalari(yol):
    ok, sayfalar = cv2.imreadmulti(yol, flags=cv2.IMREAD_UNCHANGED)
    if not ok:
        return [_oku_resim(yol)]
    return sayfalar


def _pdf_sayfalari(yol, dpi=PDF_DPI):
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(yol)
    try:
        for i in range(len(pdf)):
            sayfa = pdf[i]
            bmp = sayfa.render(scale=dpi / 72, grayscale=True)
            arr = bmp.to_numpy()
            yield i + 1, _gri(arr.copy())
            sayfa.close()
    finally:
        pdf.close()


def dosyalari_bul(yollar):
    """Verilen dosya/klasör yollarından işlenecek dosyaların sıralı listesi."""
    sonuc = []
    for y in yollar:
        if os.path.isdir(y):
            for ad in sorted(os.listdir(y), key=str.lower):
                p = os.path.join(y, ad)
                if os.path.isfile(p) and ad.lower().endswith(RESIM_UZANTI + ('.pdf',)):
                    sonuc.append(p)
        elif os.path.isfile(y):
            sonuc.append(y)
    return sonuc


def sayfalar(yollar):
    """(kaynak_dosya, sayfa_no, gri_görüntü) üretir."""
    for yol in dosyalari_bul(yollar):
        uz = os.path.splitext(yol)[1].lower()
        if uz == '.pdf':
            for no, img in _pdf_sayfalari(yol):
                yield yol, no, img
        elif uz in ('.tif', '.tiff'):
            for i, img in enumerate(_tiff_sayfalari(yol)):
                yield yol, i + 1, _gri(img)
        else:
            yield yol, 1, _gri(_oku_resim(yol))


def sayfa_sayisi(yollar):
    """Görüntüleri açmadan toplam sayfa sayısını tahmin eder (ilerleme çubuğu için)."""
    n = 0
    for yol in dosyalari_bul(yollar):
        uz = os.path.splitext(yol)[1].lower()
        if uz == '.pdf':
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(yol); n += len(pdf); pdf.close()
        elif uz in ('.tif', '.tiff'):
            n += max(1, cv2.imcount(yol)) if hasattr(cv2, 'imcount') else 1
        else:
            n += 1
    return n


def sayfa_goruntusu(yol, sayfa, dpi=PDF_DPI):
    """Tek bir sayfanın gri görüntüsü (kontrol ekranı için)."""
    uz = os.path.splitext(yol)[1].lower()
    if uz == '.pdf':
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(yol)
        try:
            s = pdf[sayfa - 1]
            arr = s.render(scale=dpi / 72, grayscale=True).to_numpy().copy()
            s.close()
            return _gri(arr)
        finally:
            pdf.close()
    if uz in ('.tif', '.tiff'):
        return _gri(_tiff_sayfalari(yol)[sayfa - 1])
    return _gri(_oku_resim(yol))
