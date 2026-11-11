"""Carbon (IBM) tabanlı tema: g10 (açık) renk jetonları, IBM Plex yazı tipleri, Qt stil sayfası.
Görünüm Carbon'dan; pencere, menü, dosya diyaloğu gibi davranışlar işletim sisteminin kendisinden gelir."""
import os
from PySide6.QtGui import QFontDatabase, QFont, QColor, QPalette

KLASOR = os.path.dirname(__file__)

# Carbon g10 jetonları
R = {
    'background': '#f4f4f4',
    'layer': '#ffffff',
    'layer_hover': '#e8e8e8',
    'layer_02': '#f4f4f4',
    'layer_selected': '#e0e0e0',
    'field': '#ffffff',
    'border_subtle': '#e0e0e0',
    'border_strong': '#8d8d8d',
    'border_interactive': '#0f62fe',
    'text_primary': '#161616',
    'text_secondary': '#525252',
    'text_helper': '#6f6f6f',
    'text_placeholder': '#a8a8a8',
    'text_on_color': '#ffffff',
    'text_disabled': '#c6c6c6',
    'interactive': '#0f62fe',
    'button_primary': '#0f62fe',
    'button_primary_hover': '#0050e6',
    'button_primary_active': '#002d9c',
    'button_secondary': '#393939',
    'button_secondary_hover': '#474747',
    'button_tertiary': '#0f62fe',
    'focus': '#0f62fe',
    'shell': '#161616',
    'shell_text': '#f4f4f4',
    'shell_hover': '#2c2c2c',
    'link': '#0f62fe',
    'success': '#24a148',
    'error': '#da1e28',
    'warning': '#f1c21b',
    'warning_text': '#8e6a00',
    'info': '#0043ce',
    # bildirim zeminleri
    'bg_success': '#defbe6',
    'bg_error': '#fff1f1',
    'bg_warning': '#fcf4d6',
    'bg_info': '#edf5ff',
    # etiket (tag) renkleri: (zemin, yazı)
    'tag_green': ('#a7f0ba', '#0e6027'),
    'tag_red': ('#ffd7d9', '#a2191f'),
    'tag_yellow': ('#fddc69', '#684e00'),
    'tag_gray': ('#e0e0e0', '#393939'),
    'tag_blue': ('#d0e2ff', '#0043ce'),
    'tag_purple': ('#e8daff', '#6929c4'),
}

# kâğıt ve soru durum renkleri (kontrol görüntüsüyle tutarlı)
DURUM_RENK = {
    'tamam': QColor('#24a148'),
    'zayıf': QColor('#ff832b'),
    'belirsiz': QColor('#ff832b'),
    'çift': QColor('#da1e28'),
    'elle': QColor('#8a3ffc'),
}

SANS = 'IBM Plex Sans'
MONO = 'IBM Plex Mono'


def fontlari_yukle():
    for ad in os.listdir(os.path.join(KLASOR, 'fontlar')):
        if ad.lower().endswith('.ttf'):
            QFontDatabase.addApplicationFont(os.path.join(KLASOR, 'fontlar', ad))


def stil():
    c = R
    return f"""
* {{ font-family: '{SANS}'; font-size: 14px; color: {c['text_primary']}; }}
QMainWindow, QDialog {{ background: {c['background']}; }}
QWidget#sayfa {{ background: {c['background']}; }}
QFrame#katman {{ background: {c['layer']}; border: none; }}
QFrame#ayirici {{ background: {c['border_subtle']}; max-height: 1px; min-height: 1px; border: none; }}

/* üst kabuk (Carbon UI shell header) */
QFrame#kabuk {{ background: {c['shell']}; }}
QLabel#kabukBaslik {{ color: {c['shell_text']}; font-size: 14px; }}
QLabel#kabukBaslik b {{ font-weight: 600; }}
QPushButton#kabukDugme {{ background: transparent; color: {c['shell_text']}; border: none; padding: 0 16px; min-height: 48px; }}
QPushButton#kabukDugme:hover {{ background: {c['shell_hover']}; }}

/* başlıklar ve metin */
QLabel#baslik {{ font-size: 28px; font-weight: 300; }}
QLabel#altbaslik {{ font-size: 20px; font-weight: 400; }}
QLabel#bolumBaslik {{ font-size: 16px; font-weight: 600; }}
QLabel#etiket {{ font-size: 12px; color: {c['text_secondary']}; letter-spacing: 0.32px; }}
QLabel#yardim {{ font-size: 12px; color: {c['text_helper']}; }}
QLabel#talimat {{ color: {c['text_secondary']}; }}
QLabel#buyukSayi {{ font-size: 32px; font-weight: 300; font-family: '{MONO}'; }}
QLabel#mono {{ font-family: '{MONO}'; }}

/* düğmeler */
QPushButton {{ border: none; min-height: 40px; padding: 0 32px 0 16px; text-align: left; }}
QPushButton:focus {{ outline: none; }}
QPushButton#birincil {{ background: {c['button_primary']}; color: {c['text_on_color']}; }}
QPushButton#birincil:hover {{ background: {c['button_primary_hover']}; }}
QPushButton#birincil:pressed {{ background: {c['button_primary_active']}; }}
QPushButton#ikincil {{ background: {c['button_secondary']}; color: {c['text_on_color']}; }}
QPushButton#ikincil:hover {{ background: {c['button_secondary_hover']}; }}
QPushButton#ucuncul {{ background: transparent; color: {c['button_tertiary']}; border: 1px solid {c['button_tertiary']}; }}
QPushButton#ucuncul:hover {{ background: {c['button_tertiary']}; color: {c['text_on_color']}; }}
QPushButton#hayalet {{ background: transparent; color: {c['link']}; padding: 0 16px; }}
QPushButton#hayalet:hover {{ background: {c['layer_hover']}; }}
QPushButton:disabled {{ background: {c['layer_selected']}; color: {c['text_disabled']}; border-color: {c['layer_selected']}; }}
QPushButton#hayalet:disabled {{ background: transparent; }}

/* giriş alanları: alt çizgili Carbon alanı */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit {{
    background: {c['field']}; border: none; border-bottom: 1px solid {c['border_strong']};
    min-height: 40px; padding: 0 12px; selection-background-color: {c['tag_blue'][0]}; selection-color: {c['text_primary']};
}}
QPlainTextEdit {{ padding: 8px 12px; font-family: '{MONO}'; }}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {{
    border: 2px solid {c['focus']}; padding: 0 10px;
}}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{ color: {c['text_disabled']}; border-bottom-color: {c['border_subtle']}; }}
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 24px; border: none; background: transparent; }}
QComboBox::drop-down {{ border: none; width: 32px; }}
QComboBox QAbstractItemView {{ background: {c['layer']}; border: 1px solid {c['border_subtle']}; selection-background-color: {c['layer_hover']}; selection-color: {c['text_primary']}; outline: none; }}

QCheckBox, QRadioButton {{ spacing: 8px; min-height: 24px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {c['text_primary']}; background: {c['layer']}; }}
QCheckBox::indicator:checked {{ background: {c['text_primary']}; image: url({os.path.join(KLASOR, 'ikonlar', 'tik.svg').replace(os.sep, '/')}); }}
QRadioButton::indicator {{ width: 16px; height: 16px; border-radius: 9px; border: 1px solid {c['text_primary']}; background: {c['layer']}; }}
QRadioButton::indicator:checked {{ background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 {c['text_primary']}, stop:0.45 {c['text_primary']}, stop:0.5 {c['layer']}, stop:1 {c['layer']}); }}

/* tablolar (Carbon data table) */
QTableView, QTableWidget, QListWidget, QTreeWidget {{
    background: {c['layer']}; border: none; gridline-color: {c['border_subtle']};
    selection-background-color: {c['layer_selected']}; selection-color: {c['text_primary']}; outline: none;
}}
QTableView::item, QTableWidget::item {{ border-bottom: 1px solid {c['border_subtle']}; padding: 0 8px; }}
QTableView::item:hover, QTableWidget::item:hover, QListWidget::item:hover {{ background: {c['layer_hover']}; }}
QHeaderView::section {{ background: {c['layer_selected']}; border: none; padding: 0 8px; min-height: 40px; font-weight: 600; }}
QListWidget::item {{ min-height: 40px; padding: 0 12px; border-bottom: 1px solid {c['border_subtle']}; }}
QListWidget::item:selected {{ background: {c['layer_selected']}; border-left: 3px solid {c['interactive']}; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #c6c6c6; min-height: 32px; }}
QScrollBar::handle:vertical:hover {{ background: #8d8d8d; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: #c6c6c6; min-width: 32px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QProgressBar {{ background: {c['border_subtle']}; border: none; max-height: 8px; min-height: 8px; text-align: center; color: transparent; }}
QProgressBar::chunk {{ background: {c['interactive']}; }}

QToolTip {{ background: #393939; color: #f4f4f4; border: none; padding: 8px 12px; }}
QStatusBar {{ background: {c['layer']}; border-top: 1px solid {c['border_subtle']}; color: {c['text_secondary']}; font-size: 12px; }}
QStatusBar QLabel {{ color: {c['text_secondary']}; font-size: 12px; padding: 0 8px; }}
QSplitter::handle {{ background: {c['border_subtle']}; }}
QTextBrowser {{ background: {c['layer']}; border: none; padding: 16px 24px; }}
QMenuBar {{ background: {c['layer']}; }}
"""


def palet(app):
    p = app.palette()
    p.setColor(QPalette.Window, QColor(R['background']))
    p.setColor(QPalette.Base, QColor(R['layer']))
    p.setColor(QPalette.Text, QColor(R['text_primary']))
    p.setColor(QPalette.WindowText, QColor(R['text_primary']))
    p.setColor(QPalette.Highlight, QColor(R['layer_selected']))
    p.setColor(QPalette.HighlightedText, QColor(R['text_primary']))
    app.setPalette(p)


def uygula(app):
    fontlari_yukle()
    app.setStyle('Fusion')
    palet(app)
    f = QFont(SANS, 10)
    f.setPixelSize(14)
    app.setFont(f)
    app.setStyleSheet(stil())
