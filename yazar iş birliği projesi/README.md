# Yazar İş Birliği Projesi (Author Collaboration Project)

## 📋 Proje Hakkında

Bu proje, akademik yazarlar arasındaki işbirliği ilişkilerini analiz etmek ve görselleştirmek için geliştirilmiş bir graf analiz sistemidir. Excel formatındaki makale verilerini kullanarak yazarlar arasındaki işbirliği ağını oluşturur ve çeşitli analiz fonksiyonları sunar.

## 🎯 Proje Amacı

- Akademik yazarlar arasındaki işbirliği ağlarını görselleştirmek
- Yazarlar arası en kısa yolları bulmak
- İşbirliği istatistiklerini analiz etmek
- Graf teorisi algoritmalarını uygulamak (BFS, DFS, Dijkstra)
- Veri yapılarını kullanarak yazar bilgilerini organize etmek (BST, Queue)

## 🚀 Özellikler

### 📊 Graf Görselleştirme
- **Interactive Network Graph**: Yazarlar arası işbirliği ağını görselleştirme
- **Zoom & Pan**: Fare ile zoom yapma ve grafiği kaydırma
- **Node Clicking**: Düğümlere tıklayarak yazar bilgilerini görme
- **Dynamic Highlighting**: Seçilen yolları ve düğümleri vurgulama

### 🔍 Analiz Fonksiyonları

1. **En Kısa Yol Bulma**: İki yazar arasındaki en kısa işbirliği yolunu bulma
2. **Kuyruk Oluşturma**: Yazarın işbirlikçilerini makale sayısına göre sıralama
3. **BST Oluşturma**: İşbirlikçilerden Binary Search Tree oluşturma
4. **BST'den Yazar Silme**: BST'den yazar silme işlemi
5. **Kısa Yollar Hesaplama**: Bir yazarın tüm işbirlikçilerine olan en kısa yolları
6. **İşbirlikçi Sayısı**: Bir yazarın kaç kişiyle işbirliği yaptığını hesaplama
7. **En Çok İşbirliği**: En çok işbirliği yapan yazarı bulma
8. **En Uzun Yol**: Bir yazardan gidebileceği en uzun yolu bulma
9. **Yazarları Listeleme**: Tüm yazarları makale sayısına göre listeleme
10. **Yazar Arama**: Yazar adına göre arama yapma

## 📦 Gereksinimler

### Python Kütüphaneleri
```
pandas>=1.3.0
networkx>=2.6.0
matplotlib>=3.4.0
tkinter (Python ile birlikte gelir)
openpyxl (Excel okuma için)
```

### Sistem Gereksinimleri
- Python 3.7 veya üzeri
- Windows/Linux/macOS
- En az 4GB RAM (büyük veri setleri için)

## 🛠️ Kurulum

1. **Gerekli Kütüphaneleri Yükleyin**
   ```bash
   pip install pandas networkx matplotlib openpyxl
   ```

2. **Veri Dosyasını Hazırlayın**
   - `PROLAB 3 - GÜNCEL DATASET (1).xlsx` dosyasını proje klasörüne koyun
   - Excel dosyasında şu sütunlar bulunmalı:
     - `paper_title`: Makale başlığı
     - `coauthors`: Yazar listesi
     - `doi`: Makale DOI'si
     - `orcid` (opsiyonel): Yazar ORCID ID'si

3. **Programı Çalıştırın**
   ```bash
   python yazar_is_birligi_graf.py
   ```

## 📖 Kullanım Kılavuzu

### Program Başlatma
Program başlatıldığında:
1. Excel dosyası otomatik olarak okunur
2. Yazar verileri işlenir ve normalize edilir
3. Graf oluşturulur ve görselleştirilir
4. Analiz fonksiyonları için GUI açılır

### Temel Kullanım

#### Graf İnteraksiyonu
- **Zoom**: Fare tekerleği ile zoom yapın
- **Pan**: Fare ile sürükleyerek grafiği kaydırın
- **Node Click**: Düğümlere tıklayarak yazar bilgilerini görün

#### Yazar Arama
- "9. Yazarları Listele" butonu ile tüm yazarları görün
- "10. Yazar Ara" butonu ile yazar arayın
- Yazar adının bir kısmını yazarak kısmi eşleşme yapabilirsiniz

#### Analiz Fonksiyonları
Her fonksiyon için:
1. İlgili butona tıklayın
2. İstenen bilgileri girin (yazar adı, ORCID, vb.)
3. Sonuçları popup pencerede görün

## 📊 Veri Formatı

### Excel Dosya Yapısı
```excel
| paper_title | coauthors | doi | orcid |
|-------------|-----------|-----|-------|
| Makale 1    | Yazar A; Yazar B | 10.1234/abc | 0000-0001-2345-6789 |
| Makale 2    | Yazar B, Yazar C | 10.1234/def | 0000-0002-3456-7890 |
```

### Yazar Listesi Formatları
Program şu ayırıcıları destekler:
- Noktalı virgül: `;`
- Virgül: `,`
- Dikey çizgi: `|`
- Yeni satır: `\n`
- "and" kelimesi: ` and `
- Ampersand: ` & `

## 🔧 Teknik Detaylar

### Kullanılan Algoritmalar
- **Dijkstra Algoritması**: En kısa yol bulma
- **Breadth-First Search (BFS)**: Graf traversali
- **Depth-First Search (DFS)**: En uzun yol bulma
- **Binary Search Tree (BST)**: Yazar verilerini organize etme
- **Queue**: İşbirlikçi sıralama

### Veri Yapıları
- **NetworkX Graph**: Ana graf yapısı
- **Pandas DataFrame**: Veri okuma ve işleme
- **Binary Search Tree**: Yazar sıralama
- **Queue**: İşbirlikçi kuyruğu
- **Dictionary**: Yazar eşleştirme

## 🐛 Bilinen Sorunlar ve Çözümler

### Sorun 1: Yazar Sayısı Beklenenden Fazla
**Çözüm**: Excel dosyasında yazar adlarını standardize edin

### Sorun 2: Graf Çok Yoğun Görünüyor
**Çözüm**: Zoom yapın veya daha az yazar içeren alt graf oluşturun

### Sorun 3: Program Yavaş Çalışıyor
**Çözüm**: Daha az veri ile test edin veya RAM'i artırın

## 📝 Geliştirici Notları

### Kod Yapısı
- **Modüler Tasarım**: Her fonksiyon ayrı modülde
- **Hata Yönetimi**: Kapsamlı hata kontrolü
- **Dokümantasyon**: Detaylı kod açıklamaları
- **Kullanıcı Dostu**: Sezgisel GUI tasarımı

### Gelecek Geliştirmeler
- [ ] Web arayüzü ekleme
- [ ] Daha fazla analiz algoritması
- [ ] Veri dışa aktarma özellikleri
- [ ] Gerçek zamanlı veri güncelleme

## 📄 Lisans

Bu proje eğitim amaçlı geliştirilmiştir. Akademik araştırmalarda kullanım için uygundur.

---

**Not**: Bu proje, graf teorisi ve veri yapıları konularında pratik deneyim kazanmak amacıyla geliştirilmiştir. Akademik işbirliği ağlarının analizi için kullanılabilir. 