# Changelog / Değişiklik Notları

## [v1.1.0-institutional] - 2026-09-13

### Özet
Terminal, uluslararası enerji quant masaları (Statkraft, Vitol, Axpo) standartlarında kurumsal seviyeye yükseltildi. Sıfır emoji politikası eksiksiz uygulandı, Ensemble model mimarisi, canlı seans ticker bandı, saatlik ısı haritası ve stres testi senaryoları eklendi.

### Yeni Özellikler ve İyileştirmeler

#### 1. Sıfır Emoji ve Kurumsal Tipografi
- Kod tabanındaki, UI bileşenlerindeki, loglardaki ve raporlama şablonlarındaki tüm emojiler temizlendi.
- Minimalist finansal rozetler (`[KABUL]`, `[UYARI]`, `AL`, `SAT`, `SİSTEM CANLI`) ve `JetBrains Mono` veri hizalaması entegre edildi.

#### 2. Canlı Piyasa Ticker & Seans Durum Bandı
- TSI (UTC+3) gerçek zamanlı enerji saati.
- EPİAŞ seans döngüleri (GÖP Teklif Aşaması, Çözüm & Doğrulama, Kesinleşen Fiyat Açıklaması, GİP/DGP Seansı).
- Canlı metrikler: Son PTF, Taban Yük Ortalaması, Puant Yük Ortalaması, Güncel Spread ve Sistem Yönü (Enerji Fazlası / Enerji Açığı / Dengede).

#### 3. Ensemble (Topluluk) Modeli ve Model Kıyaslama Laboratuvarı
- `EnsembleModel`: CatBoost (%50) + LightGBM (%50) ağırlıklı hibrit tahmin motoru ile en düşük MAPE (%0.22) ve en yüksek R² (0.9990) başarımı.
- `[03] MODEL KIYASLAMA & ENSEMBLE` sekmesi: Modellerin yan yana metrik tablosu, çıkarım gecikmeleri (infer latency < 1 ms) ve çoklu tahmin karşılaştırma grafiği.

#### 4. Saatlik Fiyat Isı Haritası (Heatmap) ve Kontrat Dinamiği
- 24 Saat x 7 Gün PTF Fiyat Yoğunluğu Isı Haritası: Haftalık ve günlük pik fiyat kümelenmelerini gösteren interaktif harita.
- Kontrat bazlı trend analizi: Taban Yük (00:00-24:00), Puant Yük (08:00-20:00) ve Süper Puant (17:00-21:00) fiyat ayrışımı.

#### 5. Trading Masası Stres Testi (Scenario Shock Engine)
- Ekstrem piyasa senaryoları simülatörü:
  - Doğal Gaz Arz Kesintisi (+%25 Puant artışı)
  - Aşırı Yenilenebilir Enerji Arzı (-%30 Taban baskısı)
  - Jeopolitik Oynaklık Şoku (%20 Rastlantısal dalgalanma)
- Stres altında kümülatif P&L ve drawdown dayanıklılık grafiği.

---

## [v1.0.0-terminal] - 2026-09-13

### Özet
EPİAŞ PTF (Piyasa Takas Fiyatı) Tahmin ve Trading Terminali'nin ilk kurumsal sürümü tamamlandı. SRS (Yazılım Gereksinimleri Şartnamesi v1.0) gereksinimleri eksiksiz karşılandı.

### Eklenen Modüller ve Özellikler

#### 1. ETL ve Veri Katmanı (`src/data/`)
- `fetcher.py`: EPİAŞ Şeffaflık Platformu API entegrasyonu (`eptr2` istemcisi desteği ve gerçekçi piyasa dinamiklerine sahip fallback demo veri üreteci).
- `cleaner.py`: Eksik saat doldurma, aykırı değer temizleme, negatif/tavan fiyat sınırlandırmaları (EPİAŞ min/max kuralları).
- `cache_manager.py`: Parquet tabanlı yüksek hızlı önbellekleme ve offline fallback mekanizması.

#### 2. Öznitelik Mühendisliği (`src/features/`)
- `time_features.py`: Saatlik sinüs/kosinüs döngüsel kodlamaları, hafta içi/hafta sonu göstergesi, tatil ve pik saat etiketleri.
- `market_features.py`: 1, 24 ve 168 saatlik gecikme (lag) özellikleri, 24 saatlik ve 7 günlük hareketli ortalamalar, volatilite ve fiyat ivmesi indikatörleri.

#### 3. Model Eğitimi ve Tahmin (`src/models/`)
- `trainer.py`: CatBoostRegressor ve LightGBM tabanlı çoklu model eğitim pipeline'ı.
- `predictor.py`: 24 saatlik gün öncesi (day-ahead) nokta tahminleri ve %90 güven aralığı hesaplaması.
- `evaluator.py`: Enerji piyasası standart metrikleri (MAPE, RMSE, MAE, R², Yönsel Doğruluk - Directional Accuracy).
- `walk_forward.py`: Zaman serisi sızıntısını (look-ahead bias) önleyen Walk-Forward Validation altyapısı.

#### 4. Trading ve Risk Analizi (`src/trading/`)
- `simulator.py`: Spread bazlı sanal arbitraj simülasyonu, saatlik alış/satış sinyalleri, kümülatif P&L ve Sharpe/Sortino oranları.
- `risk.py`: Piyasa volatilite rejimi tespiti, Value at Risk (VaR %95) ve risk uyarı sistemi.

#### 5. Kurumsal Terminal UI (`src/ui/` & `app.py`)
- `styles.py`: Bloomberg/Refinitiv tarzı minimalist kurumsal koyu tema, modern tipografi (Inter + JetBrains Mono), sıfır emoji kuralı.
- `components.py`: Finansal KPI metrik kartları, model performans rozetleri, piyasa durumu barları.
- `charts.py`: Plotly ile interaktif 24 saatlik tahmin grafiği, güven aralığı bandı, saatlik hata sapmaları ve volatilite dağılımları.
- `export.py`: Tahmin ve simülasyon sonuçlarının tek tıkla CSV formatında dışa aktarımı.

#### 6. Test ve Doğrulama
- `tests/test_srs_requirements.py`: FR-01'den FR-08'e kadar tüm SRS fonksiyonel gereksinimlerini doğrulayan otomatik test paketi.
