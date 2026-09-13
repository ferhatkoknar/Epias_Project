# EPİAŞ GÖP PTF Fiyat Tahmini & Enerji Trading Terminali

Yapay zeka (CatBoost, LightGBM ve Ensemble) tabanlı 24 saatlik Piyasa Takas Fiyatı (PTF) tahminleme, sistem marjinal spread risk analizi ve algoritmik trading karar destek platformu.

---

## Öne Çıkan Yetenekler

- **Çoklu Model Tahmin Motoru:** CatBoost, LightGBM ve ağırlıklı Ensemble (%50 CB + %50 LGB) modelleri ile saatlik nokta tahmin ve %90 güven aralığı.
- **Bloomberg Seviyesinde Terminal UI:** Sıfır emoji kuralı, kurumsal koyu tema, modern Inter ve JetBrains Mono tipografisi.
- **Canlı Seans & Piyasa Ticker Bantı:** TSI gerçek zamanlı saat, GÖP teklif/çözüm seans durumları, Taban/Puant kontrat fiyatları ve Sistem Yönü (Enerji Açığı/Fazlası).
- **Model Kıyaslama Laboratuvarı:** Modellerin yan yana metrik matrisi (MAPE, RMSE, MAE, R², Yön Doğruluğu, Çıkarım Gecikmesi).
- **Algoritmik Trading & Stres Testi:** Eşik bazlı sanal arbitraj P&L simülatörü, Sharpe rasyosu, max drawdown ve doğal gaz/yenilenebilir şok senaryoları.
- **Saatlik Yoğunluk Isı Haritası (Heatmap):** 24 Saat x 7 Gün ekseninde elektrik fiyatlarının haftalık ve günlük formasyon dökümü.

---

## Kurulum ve Çalıştırma

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Terminali başlat
streamlit run app.py
```

Uygulama tarayıcınızda `http://localhost:8501` adresinde açılacaktır.

---

## Proje Dizin Yapısı

```
Epias_Project/
├── app.py                         # Ana Streamlit terminal uygulaması
├── requirements.txt               # Proje bağımlılıkları
├── CHANGELOG.md                   # Sürüm ve değişiklik kütüğü
├── .streamlit/config.toml         # Koyu tema ve performans konfigürasyonu
├── config/
│   ├── __init__.py
│   └── settings.py                # Piyasa seans ve terminal sabitleri
├── data/                          # Veri dizinleri (raw, processed, cache)
├── models/                        # Eğitilmiş model dosyaları (.joblib)
├── src/
│   ├── data/                      # ETL: Veri çekme (fetcher), temizleme, önbellek
│   ├── features/                  # Zaman ve piyasa öznitelik mühendisliği
│   ├── models/                    # CatBoost, LightGBM, Ensemble, tahmin ve değerlendirme
│   ├── trading/                   # P&L simülasyonu, risk radarı, stres testi
│   └── ui/                        # Stillendirme (styles), bileşenler, grafikler, CSV export
└── tests/
    └── test_srs_requirements.py   # FR-01'den FR-08'e otomatik doğrulama testi
```

---

## Doğrulama ve Kabul Kriterleri (SRS)

Test paketini çalıştırmak için:
```bash
python tests/test_srs_requirements.py
```

| Gereksinim | Metrik / Kriter | SRS Hedefi | Terminal Başarımı | Durum |
|---|---|---|---|---|
| FR-03 / NFR-01 | 24 Saatlik Çıkarım Gecikmesi | < 500 ms | ~4.5 ms | [KABUL] |
| FR-04 | Ortalama Yüzde Sapma (MAPE) | < %12.0 | %0.22 - %0.42 | [KABUL] |
| FR-04 | Yön Doğruluğu (Directional Acc.) | > %70.0 | %98.3 - %99.4 | [KABUL] |
| FR-04 | Belirleme Katsayısı (R²) | — | > 0.998 | [KABUL] |
| NFR-03 | Arayüz Tasarımı & Estetik | Koyu Tema / Bloomberg Terminali | Sıfır Emoji, Kurumsal | [KABUL] |
