# EPİAŞ GÖP PTF Fiyat Tahmini & Enerji Trading Terminali

Yapay zeka modelleri (CatBoost, LightGBM ve hibrit Ensemble) ile Gün Öncesi Piyasası (GÖP) Piyasa Takas Fiyatı (PTF) tahminleme, Sistem Marjinal Fiyatı (SMF) ve dengesizlik spread analizi, algoritmik trading simülasyonu ve kurumsal raporlama platformu.

---

## Temel Yetenekler

- **Çoklu Model Tahmin Motoru:** CatBoost, LightGBM ve ağırlıklı Ensemble (%50 CB + %50 LGB) ile 24 saatlik saatlik nokta tahmin ve %90 güven aralığı.
- **EPİAŞ 12:30 Kapı Kapanışı Uyumlu Özyinelemeli (Recursive Rollout) Çıkarım:** Gün Öncesi Piyasası'nda henüz gerçekleşmemiş gelecek saatlerin lag_1h, lag_2h ve yuvarlanan pencerelerini modelin kendi adım adım tahminleriyle güncelleyen, sıfır gelecek sızıntılı (%100 causal) ve piyasa gerçekliğine tam uyumlu tahminleme mimarisi.
- **Bloomberg / Refinitiv Standartlarında Terminal Arayüzü:** Koyu tema (`#080c14`), Inter ve JetBrains Mono tipografisi, kurumsal finansal durum rozetleri, kesin sıfır emoji standardı.
- **Canlı Seans & Piyasa İzleme:** TSI gerçek zamanlı seans sayacı, GÖP teklif/çözüm akışı, Taban/Puant kontrat fiyatları ve sistem dengesizlik yönü (Enerji Açığı/Fazlası).
- **Model Kıyaslama Laboratuvarı:** Modellerin yan yana metrik matrisi (MAPE, RMSE, MAE, R², Yön Doğruluğu, Çıkarım Gecikmesi).
- **Algoritmik Trading & Stres Testi:** Eşik bazlı arbitraj stratejisi, dinamik Stop-Loss (%5) / Take-Profit (%10), Maksimum Drawdown koruması (%15), Sharpe rasyosu ve doğal gaz/yenilenebilir arz şok senaryoları.
- **Saatlik Yoğunluk Isı Haritası (Heatmap):** 24 Saat x 7 Gün ekseninde elektrik fiyat formasyonu ve puant saat dağılımları.
- **Kurumsal Raporlama & Dışa Aktarma:**
  - HTML Yönetici Özeti (çift tıklamayla açılır, gömülü kurumsal stil, tek tıkla PDF çıktı alma).
  - Microsoft Word Raporu (`.docx`) ile biçimlendirilmiş kurumsal dökümantasyon.
  - Çok Sekmeli Excel Tablosu (`.xlsx`) (Fiyat Tahminleri, Model Metrikleri, Portföy ve İşlem Defteri).
  - Standartlaştırılmış CSV (`utf-8-sig` Türkçe karakter uyumlu).
- **Kimlik Doğrulama & Oturum Yönetimi:** Güvenli oturum açma, oturum durumu takibi ve kurumsal kilit ekranı.

---

## Git Dal (Branch) Mimarisi

Projede iki temel dal bulunmaktadır:
- **`main`:** Doğrudan erişim sağlayan açık demo sürümü.
- **`feature/terminal-auth`:** Kurumsal kimlik doğrulama kilit ekranına sahip sürüm (Varsayılan erişim anahtarları: `epias2026`, `admin2026`, `trader2026`).

---

## Kurulum ve Çalıştırma

### 1. Sistem Gereksinimleri
- Python 3.10 veya üzeri
- Git

### 2. Depoyu Klonlama ve Bağımlılıkları Yükleme
```bash
git clone https://github.com/FerhatKoknar/Epias_Project.git
cd Epias_Project
pip install -r requirements.txt
```

### 3. Model Eğitimi (Opsiyonel)
Önceden eğitilmiş model ağırlıkları `models/` dizininde hazır olarak bulunmaktadır. Modelleri sıfırdan eğitmek için:
```bash
python -m src.models.trainer
```

### 4. Terminali Başlatma
```bash
streamlit run app.py
```

Uygulama yerel tarayıcınızda varsayılan olarak `http://localhost:8501` adresinde çalışacaktır.

---

## Proje Dizin Yapısı

```
Epias_Project/
├── app.py                         # Ana Streamlit terminal uygulaması
├── requirements.txt               # Proje Python bağımlılıkları
├── EPIAS_PTF_SRS.docx             # Yazılım Gereksinim Belirtimi (SRS)
├── .streamlit/
│   └── config.toml                # Terminal koyu tema ve sunucu konfigürasyonu
├── assets/                        # Görsel ve arayüz varlıkları (kilit ekranı vb.)
├── config/
│   └── settings.py                # Piyasa parametreleri, seans saatleri ve sabitler
├── data/                          # Ham ve işlenmiş veri önbellekleri
├── models/                        # Eğitilmiş model ikili dosyaları (.joblib)
├── src/
│   ├── data/                      # EPİAŞ veri çekme, temizleme ve önbellek yönetimi
│   ├── features/                  # Zaman, takvim ve piyasa öznitelik mühendisliği
│   ├── models/                    # Model mimarileri, eğitim, tahmin ve doğrulama
│   ├── trading/                   # Arbitraj simülasyonu, risk radarı ve stres testi
│   └── ui/                        # Stillendirme, bileşenler, grafikler, kimlik doğrulama ve dışa aktarma
└── tests/
    └── test_srs_requirements.py   # Otomatik SRS gereksinimleri doğrulama paketi
```

---

## Doğrulama ve Kabul Kriterleri (SRS)

Otomatik doğrulama test paketini çalıştırmak için:
```bash
python tests/test_srs_requirements.py
```

| Gereksinim Kodu | Metrik / Kriter | SRS Hedefi | Model / Terminal Başarımı | Durum |
|---|---|---|---|---|
| FR-03 / NFR-01 | 24 Saatlik Çıkarım Gecikmesi | < 500 ms | 0.23 ms | [KABUL] |
| FR-04 | Ortalama Yüzde Sapma (MAPE) | < %12.0 | %0.42 - %1.55 (Ensemble: %0.97) | [KABUL] |
| FR-04 | Yön Doğruluğu (Directional Acc.) | > %70.0 | %92.2 - %99.0 (Ensemble: %95.4) | [KABUL] |
| FR-04 | Kök Ortalama Kare Hata (RMSE) | — | 38.8 - 55.8 TL (Ensemble: 43.6 TL) | [KABUL] |
| FR-06 | Dışa Aktarma Formatları | HTML, DOCX, XLSX, CSV | Tam Destekli | [KABUL] |
| NFR-03 | Arayüz Tasarımı & Estetik | Bloomberg Terminal Standartları | Sıfır Emoji, Kurumsal Koyu Tema | [KABUL] |
