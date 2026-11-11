"""Boş öğrenci listesi şablonunu üretir: turnusol/sablonlar/ogrenci_listesi_sablonu.xlsx
Bu dosya hem sınıf listesi hem not şablonu olarak programa verilebilir."""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YOL = os.path.join(KOK, 'turnusol', 'sablonlar', 'ogrenci_listesi_sablonu.xlsx')

wb = Workbook()
ws = wb.active; ws.title = 'Öğrenciler'
ws.append(['Öğrenci No', 'Adı', 'Soyadı', 'S1', 'S2'])
for c in range(1, 6):
    h = ws.cell(1, c); h.font = Font(bold=True); h.fill = PatternFill('solid', fgColor='DDDDDD')
    h.alignment = Alignment(horizontal='center')
for r in range(2, 302):
    ws.cell(r, 1).number_format = '@'          # numaralar metin olarak saklanır (baştaki sıfır kaybolmaz)
for col, w in zip('ABCDE', (16, 22, 22, 8, 8)):
    ws.column_dimensions[col].width = w
ws.freeze_panes = 'A2'
dv = DataValidation(type='decimal', operator='between', formula1='0', formula2='100', allow_blank=True,
                    error='Not 0 ile 100 arasında bir sayı olmalıdır.', errorTitle='Geçersiz not')
ws.add_data_validation(dv); dv.add('D2:E301')

b = wb.create_sheet('Nasıl Kullanılır')
b.column_dimensions['A'].width = 110
satirlar = [
    'Bu şablon Turnusol optik form okuyucusu için hazırlanmıştır.',
    '',
    'Öğrencileri "Öğrenciler" sayfasına satır satır yazın. Öğrenci numarasını, adı ve soyadı ayrı sütunlara girin.',
    'Öğrenci numarasını optik forma kodlanacak biçimde, yani yalnızca rakamlarla yazın.',
    'Başlık satırını silmeyin ve sütunların adını değiştirmeyin.',
    '',
    'Programda bu dosyayı "Sınıf listesi" alanına yüklerseniz program öğrenci adlarını buradan alır.',
    'Aynı dosyayı "Not şablonu" alanına da yükleyebilirsiniz. Program notları seçtiğiniz sütuna (S1 ya da S2) yazar.',
    'Başka sınavlar için S2 sütununun sağına yeni sütunlar ekleyebilirsiniz. Program her başlığı ayrı bir sınav sütunu olarak tanır.',
    '',
    'Program, dolu bir not hücresinin üzerine siz izin vermedikçe yazmaz.',
]
for i, s in enumerate(satirlar, 1):
    b.cell(i, 1, s).alignment = Alignment(wrap_text=True)
b['A1'].font = Font(bold=True)
wb.save(YOL)
print(YOL)
