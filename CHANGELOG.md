# Changelog / Değişiklik Notları

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
