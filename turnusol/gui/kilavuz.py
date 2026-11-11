"""Uygulama içi kılavuz."""
import os
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QDialog, QHBoxLayout, QListWidget, QTextBrowser, QListWidgetItem

from .tema import R, SANS, MONO

GORSEL = os.path.join(os.path.dirname(__file__), 'kilavuz')


def _img(ad, gen=560):
    return f'<p><img src="{ad}" width="{gen}"></p>'


BOLUMLER = [
    ('baslarken', 'Başlarken', f"""
<h1>Başlarken</h1>
<p>Turnusol, programla gelen optik formları okur, cevap anahtarına göre puanlar ve notları Excel dosyasına yazar.
Yozgat Bozok Üniversitesi’nde notlar doğrudan OBS’ye yüklenecek şablona yazılabilir.
İş akışı, pencerenin üstündeki beş adımdan oluşur. Adımları soldan sağa izlemeniz yeterlidir. Bir adıma geri dönmek
isterseniz adımın adına tıklayabilirsiniz.</p>
<ol>
<li><b>Taramalar</b> adımında taranmış kâğıtları ekler ve okutursunuz. Sınıf listesini ve not şablonunu da isterseniz bu adımda yüklersiniz.</li>
<li><b>Cevap Anahtarı</b> adımında taramadan gelen anahtarı kontrol edersiniz. Taramada anahtar yoksa anahtarı burada elle girersiniz.</li>
<li><b>Puanlama</b> adımında toplam puanı, soru puanlarını ve yanlışların doğruyu götürüp götürmeyeceğini ayarlarsınız.</li>
<li><b>Kontrol</b> adımında programın emin olamadığı yerlere bakarsınız. Program bir şıkkı yanlış okuduysa doğru şıkka tıklayarak düzeltirsiniz.</li>
<li><b>Dışa Aktar</b> adımında notları not şablonuna yazdırır ve Excel raporunu kaydedersiniz.</li>
</ol>
<p>Bir adımın yanında turuncu bir işaret görürseniz o adımda dikkat etmeniz gereken bir şey vardır.</p>
"""),
    ('form', 'Formu yazdırma', """
<h1>Formu yazdırma</h1>
<p>Boş formlar programın içindedir. Pencerenin üstündeki <b>Boş formlar</b> düğmesine basın ya da <b>Dosya</b> menüsünden
<b>Boş optik formlar</b> komutunu seçin. Açılan pencerede formu seçip <b>Yazdır</b> düğmesiyle doğrudan yazdırabilir ya da
<b>PDF olarak kaydet</b> düğmesiyle bilgisayarınıza kaydedebilirsiniz.</p>
<h3>Hangi formu seçmeliyim?</h3>
<p>Program iki form takımı okur. Her takımda <b>50</b>, <b>75</b> ve <b>100</b> soruluk birer form vardır. Formların hepsi A4 boyutundadır.</p>
<ul>
<li><b>Genel formlarda</b> öğrenci numarası alanı boştur. Öğrenci numarasını en soldaki kutudan başlayarak yazar ve kodlar. Bu formlar her kurumda kullanılabilir.</li>
<li><b>Yozgat Bozok Üniversitesi formlarında</b> numaranın ilk yedi hanesi (2630112) basılıdır. Öğrenci yalnızca son dört haneyi kodlar.</li>
</ul>
<p>Sınavdaki soru sayısına eşit ya da ondan büyük olan formu seçin. Program fazla soruları puanlamaz. Örneğin 40 soruluk bir sınav için 50 soruluk formu kullanabilirsiniz.
Aynı sınavda farklı formlar kullanılabilir. Program her kâğıdın hangi form olduğunu köşelerdeki işaretlerden anlar.</p>
<h3>Yazdırırken dikkat edilecekler</h3>
<ul>
<li>PDF dosyasını başka bir programdan yazdırıyorsanız ölçeği <b>Gerçek boyut</b> ya da <b>%100</b> olarak seçin. Sayfaya sığdırma ayarı formu küçültür.</li>
<li>Program fotokopiyi de okur, ancak koyu ya da gri zeminli fotokopiler okumayı zorlaştırır.</li>
<li>Kâğıdın kenarlarındaki küçük siyah kareler hizalama işaretleridir ve bu kareler kırpılmamalıdır. Kâğıdın biraz küçülmesi ya da eğik basılması okumayı etkilemez.</li>
<li>Öğrenciler <b>kurşun kalem</b> kullanmalıdır.</li>
<li>Sınavda kitapçık kullanılmıyorsa öğrenciler kitapçık türünü boş bırakır.</li>
<li>Kâğıtları toplarken katlamayın ve köşelerdeki işaretlerin üstünden zımbalamayın.</li>
</ul>
"""),
    ('anahtar', 'Cevap anahtarı', """
<h1>Cevap anahtarı</h1>
<h3>Anahtarı optik formla vermek</h3>
<p>Boş bir forma doğru cevapları kodlayın. Öğrenci numarası alanında doldurulabilen bütün hanelere <b>9</b> kodlayın.
Genel formda on bir hanenin hepsine, Yozgat Bozok Üniversitesi formunda ise son dört haneye 9 kodlanır.
Sınavda kitapçık kullanıyorsanız her kitapçık için ayrı bir anahtar formu doldurun ve formdaki kitapçık türünü işaretleyin.
Bu kâğıtları öğrenci kâğıtlarıyla birlikte taratın. Program anahtar kâğıtlarını kendisi ayırır.</p>
<h3>Anahtarı elle girmek</h3>
<p><b>Cevap Anahtarı</b> adımında anahtarı üç yoldan girebilirsiniz.</p>
<p><b>Tıklayarak:</b> Bir şıkka tıklamak o şıkkı seçer. Aynı soruda başka bir şıkka tıklarsanız seçim o şıkka geçer. Seçili şıkka tekrar tıklarsanız seçim kalkar.
Soruları istediğiniz sırayla girebilirsiniz.</p>
<p><b>Klavyeyle:</b> Bir sorunun numarasına ya da satırına tıklayın. Satır mavi renkle vurgulanır. Ardından A, B, C, D ya da E tuşuna basın.
Program o soruyu doldurur ve sıradaki soruyu seçer. Boşluk tuşu soruyu boş bırakır, ok tuşları sorular arasında gezdirir.</p>
<p><b>Hızlı giriş kutusuyla:</b> Hızlı giriş kutusu iki yazımı kabul eder:</p>
<ul>
<li>Cevapları sırayla yazabilirsiniz, örneğin <code>ABCDEABCDE</code>. Boş bırakmak istediğiniz soru için tire (<code>-</code>) yazın.</li>
<li>Cevapları soru numarasıyla yazabilirsiniz, örneğin <code>1A 2B 3C</code>.</li>
</ul>
<p>Bir soruda birden fazla şık doğru sayılacaksa ikinci şıkka <b>Shift</b> tuşuna basılı tutarak tıklayın. Program o soruda seçili şıkların hepsini doğru kabul eder.
Program, <b>Sınavdaki soru sayısı</b> kutusuna yazdığınız sayıdan sonraki soruları puanlamaz ve bu soruları soluk gösterir. Soru sayısını azaltmak girdiğiniz cevapları silmez.
İptal edilen soruları virgülle ayırarak yazın, örneğin <code>7, 12</code>.</p>
"""),
    ('tarama', 'Tarama', """
<h1>Tarama</h1>
<ul>
<li>Kâğıtları <b>200–300 dpi</b> çözünürlükte ve <b>gri tonlu</b> olarak taramanızı öneririz. Renkli tarama da olur. Bütün kâğıtları tek bir çok sayfalı PDF dosyasına taratmak işinizi kolaylaştırır.</li>
<li>Program siyah-beyaz taramayı da okur. Ancak siyah-beyaz taramada hafif işaretler daha sık kontrol listesine düşer.</li>
<li>Kâğıtların ters, yan ya da eğik taranması sorun değildir. Program bu durumları kendisi düzeltir.</li>
<li>Birden fazla PDF ya da resim dosyası (JPG, PNG, TIFF) ekleyebilirsiniz. Bir klasörü sürükleyip bırakırsanız program klasördeki dosyaların hepsini ekler.</li>
</ul>
<p>Okuma bitince program bir özet gösterir. Özette öğrenci kâğıdı, anahtar kâğıdı, kontrol gerektiren kâğıt ve okunamayan kâğıt sayıları yazar.
Bir kâğıt okunamadıysa genellikle hizalama işaretleri kırpılmıştır ya da kâğıt çok koyu taranmıştır.</p>
"""),
    ('excel', 'Excel öğrenci listesi', """
<h1>Excel öğrenci listesi</h1>
<p>OBS dosyalarını kullanamıyorsanız öğrenci listesini programla gelen Excel şablonuna girebilirsiniz.
Şablonu <b>Dosya</b> menüsündeki <b>Excel öğrenci listesi şablonunu kaydet</b> komutuyla ya da <b>Taramalar</b> adımındaki düğmeyle kaydedin.</p>
<ol>
<li>Şablonu Excel’de açın. <b>Öğrenciler</b> sayfasına her öğrenci için bir satır girin. Öğrenci numarasını, adı ve soyadı ayrı sütunlara yazın.</li>
<li>Öğrenci numarasını optik forma kodlanacak biçimde, yalnızca rakamlarla yazın. Başlık satırını silmeyin.</li>
<li>Dosyayı kaydedin ve <b>Taramalar</b> adımındaki “Sınıf listesi” kutusuna sürükleyin. Program öğrenci adlarını bu listeden alır.</li>
<li>Notların da bu dosyaya yazılmasını istiyorsanız aynı dosyayı “Not şablonu” kutusuna da sürükleyin. <b>Dışa Aktar</b> adımında notun yazılacağı sütunu (S1 ya da S2) seçin.</li>
</ol>
<p>Başka sınavlar için S2 sütununun sağına yeni sütunlar ekleyebilirsiniz. Program her başlığı ayrı bir sınav sütunu olarak tanır.</p>
"""),
    ('obs', 'OBS: sınıf listesi', f"""
<h1>OBS’den sınıf listesini indirme</h1>
<p>Bu bölüm Yozgat Bozok Üniversitesi OBS sistemine göre yazılmıştır. Program başka kurumların OBS dosyalarıyla denenmemiştir.</p>
<p>Sınıf listesini yüklemek zorunlu değildir. Listeyi yüklerseniz program öğrenci adlarını listeden alır ve listede olmayan numaraları size bildirir.</p>
<ol>
<li>OBS’ye girin. Sol menüde sırasıyla <b>Öğrenci Web (Öğretim Üyesi)</b>, <b>Verdiğim Dersler</b> ve <b>Ders Öğrenci Listesi</b> seçeneklerine tıklayın.</li>
</ol>
{_img('obs_1_verdigim_dersler.png', 300)}
<ol start="2">
<li><b>Dersleri Listele</b> düğmesine basın ve listeden dersinizi işaretleyin.</li>
<li>Raporlama kriterlerinde <b>Sınıf Listesi</b> ve <b>Excel</b> seçeneklerinin seçili olduğunu kontrol edin, sonra <b>İndir</b> düğmesine basın.</li>
</ol>
{_img('obs_2_ders_ogrenci_listesi.png')}
<p>OBS, <code>Sınıf Listesi.XLS</code> adlı bir dosya indirir. Bu dosyayı <b>Taramalar</b> adımındaki “Sınıf listesi” kutusuna sürükleyin.</p>
"""),
    ('sablon', 'OBS: not şablonu', f"""
<h1>OBS not şablonu</h1>
<p>Bu bölüm Yozgat Bozok Üniversitesi OBS sistemine göre yazılmıştır.</p>
<p>Notları OBS’ye tek seferde yüklemek için OBS’nin kendi not şablonunu kullanırsınız.</p>
<ol>
<li>OBS not girişi ekranında dersi açın ve <b>Excel şablon indir</b> düğmesine basın.</li>
<li>İndirilen dosyayı <b>Taramalar</b> adımındaki “Not şablonu” kutusuna sürükleyin.</li>
<li><b>Dışa Aktar</b> adımında notun yazılacağı sütunu seçin. <b>S1</b> birinci sınavın, <b>S2</b> ikinci sınavın sütunudur. Ardından <b>Doldurulmuş şablonu kaydet</b> düğmesine basın.</li>
<li>OBS’de <b>Dosya Seç</b> düğmesiyle kaydettiğiniz dosyayı seçin ve <b>Excel içeri al</b> düğmesine basın.</li>
</ol>
{_img('obs_3_not_girisi_sablon.png', 420)}
<p>Program şablondaki numaralara, adlara ve diğer sınav sütunlarına dokunmaz. Program yalnızca seçtiğiniz sütunu doldurur ve siz izin vermedikçe dolu bir notun üstüne yazmaz.
Sınıf listesinde olup şablonda olmayan öğrencileri (örneğin devamsızlıktan kalanları) program raporda ayrıca listeler.</p>
"""),
    ('puan', 'Puanlama', """
<h1>Puanlama</h1>
<ul>
<li>Toplam puan varsayılan olarak 100’dür ve program bu puanı sorulara eşit olarak dağıtır.</li>
<li>Sorulara farklı puan vermek için soru aralığını ve puanını yazın. Örneğin <code>1-5:4; 6-40:2</code> yazarsanız 1–5. sorular 4’er puan, 6–40. sorular 2’şer puan eder.
Belirtmediğiniz sorular kalan puanı eşit olarak paylaşır.</li>
<li>Yanlışların doğruyu götürmesini Gelişmiş ayarlar bölümünden açabilirsiniz. Örneğin dört yanlış bir doğruyu götürüyorsa her yanlış, o sorunun puanının dörtte birini düşürür.
Not sıfırın altına inmez. Program iki şık işaretlenmiş soruyu yanlış sayar.</li>
<li>İptal edilen bir soruyu program ya herkese doğru sayar ya da sorunun puanını diğer sorulara orantılı olarak dağıtır. Hangisinin uygulanacağını siz seçersiniz.</li>
<li>Program notu tam sayıya yuvarlar. Yarım puanlar yukarı yuvarlanır.</li>
</ul>
<p>Sağdaki tablo, ayarlarınıza göre her sorunun kaç puan ettiğini gösterir.</p>
"""),
    ('kontrol', 'Kontrol ve düzeltme', """
<h1>Kontrol ve düzeltme</h1>
<p>Program emin olamadığı bir yerde tahmin yapmaz ve kararı size bırakır. <b>Kontrol bekleyen</b> listesinde yalnızca bakmanız gereken kâğıtlar bulunur.
Kâğıt üzerindeki renklerin anlamları şunlardır:</p>
<table cellpadding="4">
<tr><td style="color:#24a148">●</td><td>Yeşil halka, programın okuduğu cevabı gösterir.</td></tr>
<tr><td style="color:#ff832b">●</td><td>Turuncu halka şüpheli bir işareti gösterir. Hafif işaretler, tikler ve tam silinmemiş işaretler bu renkte görünür.</td></tr>
<tr><td style="color:#da1e28">●</td><td>Kırmızı halka, iki şıkkın işaretlendiğini gösterir. Program böyle bir soruyu yanlış sayar.</td></tr>
<tr><td style="color:#8a3ffc">●</td><td>Mor halka, sizin elle düzelttiğiniz cevabı gösterir.</td></tr>
</table>
<h3>Düzeltme</h3>
<ul>
<li>Program bir şıkkı yanlış okuduysa doğru şıkkın dairesine tıklayın. İşaretli bir şıkka tekrar tıklarsanız program o şıkkı siler ve soru boş kalır.</li>
<li>Shift tuşuna basılı tutarak tıklarsanız program ikinci bir şık ekler. Bu durumda soru iki şık işaretlenmiş olarak sayılır.</li>
<li>Ad, soyad ve numara sütunlarını da aynı şekilde, doğru harfe ya da rakama tıklayarak düzeltebilirsiniz.</li>
<li>Sağdaki “Bakılacak yerler” listesinde bir maddeye tıklarsanız görüntü o yere yakınlaşır.</li>
<li>Program kâğıdı, okurken bulduğu hizalama işaretlerine göre dik ve düz gösterir. Kâğıt ters ya da eğik taranmış olsa bile ekranda düz görünür.
Görüntüyü yine de çevirmek isterseniz <b>Döndür</b> düğmesini kullanabilirsiniz.</li>
</ul>
<h3>Onaylama</h3>
<p>Kâğıda baktıktan sonra <b>Onayla</b> düğmesine basın. Onaylamak sizi sonraki kâğıda geçirmez; ne seçtiğinizi görebilmeniz için aynı kâğıt ekranda kalır.
Onayladığınız kâğıt siz başka bir kâğıda geçene kadar listede durur. Yanlışlıkla onayladıysanız aynı düğme <b>Onayı geri al</b> olarak görünür.
Sonraki kâğıda geçmek için <b>Sonraki kâğıt</b> düğmesine basın.</p>
<h3>Kısayollar</h3>
<table cellpadding="4">
<tr><td><code>Enter</code></td><td>Bu tuş kâğıdı onaylar. Onaylı kâğıtta tekrar basarsanız onay geri alınır. Tuş sonraki kâğıda geçmez.</td></tr>
<tr><td><code>J</code> ve <code>K</code></td><td>Bu tuşlar sonraki ve önceki kâğıda geçer.</td></tr>
<tr><td><code>N</code></td><td>Bu tuş aynı kâğıttaki sonraki uyarıya geçer.</td></tr>
<tr><td><code>F</code></td><td>Bu tuş kâğıdı pencere genişliğine sığdırır.</td></tr>
<tr><td><code>R</code></td><td>Bu tuş kâğıdı saat yönünde 90 derece döndürür.</td></tr>
<tr><td><code>Ctrl</code> ve fare tekerleği</td><td>Bu ikisi birlikte görüntüyü yakınlaştırır ve uzaklaştırır.</td></tr>
</table>
"""),
    ('disari', 'Dışa aktarma', """
<h1>Dışa aktarma</h1>
<ul>
<li><b>Doldurulmuş şablonu kaydet</b> düğmesi, notların yazıldığı şablonun bir kopyasını oluşturur. Yüklediğiniz şablon OBS şablonuysa bu kopyayı OBS’ye yüklersiniz.</li>
<li><b>Excel raporu</b> sonuçları, öğrenci cevaplarını ve soru analizini içerir. Cevaplar sayfasında doğru cevaplar yeşil, yanlış cevaplar kırmızı görünür.
Soru analizi sayfası her sorunun doğru yanıtlanma yüzdesini ve şıkların dağılımını gösterir. Raporda ayrıca kontrol listesi, sınıf listesi karşılaştırması ve cevap anahtarı bulunur.</li>
<li><b>Kontrol görüntüleri</b>, programın okuduğu şıkların işaretlendiği kâğıt görüntüleridir. Bu görüntüleri itirazlar ve arşiv için saklayabilirsiniz.</li>
</ul>
<p>Kontrol bekleyen kâğıt varken de dışa aktarabilirsiniz. Bu durumda program o kâğıtları okunduğu hâliyle puanlar.</p>
"""),
    ('ilk', 'İlk açılış', """
<h1>İlk açılış</h1>
<p>Program Microsoft ya da Apple tarafından imzalanmadığı için işletim sistemi ilk açılışta bir uyarı gösterebilir.
Bu uyarıyı yalnızca ilk açılışta geçmeniz gerekir.</p>
<h3>Windows</h3>
<p>“Windows bilgisayarınızı korudu” uyarısı çıkarsa uyarıdaki <b>Ek bilgi</b> bağlantısına, sonra <b>Yine de çalıştır</b> düğmesine tıklayın.</p>
<h3>Mac</h3>
<ol>
<li>Uygulamayı açmayı deneyin. macOS uygulamanın açılamadığını söylerse pencereyi <b>Bitti</b> düğmesiyle kapatın.</li>
<li><b>Sistem Ayarları</b> içinde <b>Gizlilik ve Güvenlik</b> bölümünü açın. Sayfanın altında Turnusol için bir uyarı görürsünüz. Bu uyarının yanındaki <b>Yine de Aç</b> düğmesine tıklayın.</li>
<li>macOS parolanızı isteyebilir. Parolayı girdikten sonra çıkan pencerede yine <b>Yine de Aç</b> düğmesine tıklayın.</li>
</ol>
"""),
    ('sss', 'Sık sorulanlar', """
<h1>Sık sorulanlar</h1>
<h3>Bir kâğıt okunamadı olarak görünüyor. Ne yapmalıyım?</h3>
<p>Kâğıdın kenarındaki siyah kareler kırpılmış ya da kâğıt çok koyu taranmış olabilir. Kâğıdı düz ve tam sayfa olarak yeniden taratın.</p>
<h3>Öğrenci numarasını yanlış kodlamış. Nasıl düzeltirim?</h3>
<p>Kontrol ekranında numara sütunundaki doğru rakama tıklayın. Sınıf listesini yüklediyseniz program listede olmayan numaraları zaten size bildirir.</p>
<h3>Aynı öğrenciden iki kâğıt var. Ne olur?</h3>
<p>Program bu durumu bir uyarıyla bildirir. Kontrol ekranında iki kâğıda da bakın ve yanlış olan kâğıdın numarasını düzeltin.</p>
<h3>Öğrencinin adı ve soyadı kutulara sığmıyor. Sorun olur mu?</h3>
<p>Bu bir sorun değildir. Sınıf listesini yüklediyseniz program adı ve soyadı öğrenci numarasına bakarak listeden alır.</p>
"""),
]


class Kilavuz(QDialog):
    def __init__(self, ust=None):
        super().__init__(ust)
        self.setWindowTitle('Kılavuz — Turnusol'); self.resize(980, 720)
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        self.icindekiler = QListWidget(); self.icindekiler.setFixedWidth(240)
        self.icindekiler.setStyleSheet(f'QListWidget {{ background:{R["layer_02"]}; border-right:1px solid {R["border_subtle"]}; padding-top:8px; }}')
        self.metin = QTextBrowser(); self.metin.setOpenExternalLinks(True); self.metin.setSearchPaths([GORSEL])
        self.metin.document().setDefaultStyleSheet(
            f"body {{ font-family:'{SANS}'; font-size:14px; color:{R['text_primary']}; line-height:150%; }}"
            f"h1 {{ font-size:28px; font-weight:300; margin-bottom:12px; }} h3 {{ font-size:16px; font-weight:600; margin-top:18px; }}"
            f"code {{ font-family:'{MONO}'; background:{R['layer_02']}; }} li {{ margin-bottom:6px; }}")
        lay.addWidget(self.icindekiler); lay.addWidget(self.metin, 1)
        self.anahtarlar = []
        for k, ad, _ in BOLUMLER:
            self.icindekiler.addItem(QListWidgetItem(ad)); self.anahtarlar.append(k)
        self.icindekiler.currentRowChanged.connect(lambda i: self.metin.setHtml(BOLUMLER[i][2]))
        self.icindekiler.setCurrentRow(0)

    def ac(self, bolum=None):
        if bolum in self.anahtarlar:
            self.icindekiler.setCurrentRow(self.anahtarlar.index(bolum))
        self.show(); self.raise_(); self.activateWindow()
