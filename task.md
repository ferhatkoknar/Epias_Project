# EPİAŞ PTF Tahmin Projesi — Görev Listesi

## Aşama 1: Proje Altyapısı & Konfigürasyon
- [ ] Dosya dizin yapısını oluştur
- [ ] `requirements.txt` oluştur
- [ ] `.streamlit/config.toml` — koyu tema konfigürasyonu
- [ ] `config/settings.py` — proje sabitleri

## Aşama 2: Veri ve ETL Katmanı
- [ ] `src/data/fetcher.py` — EPİAŞ API veri çekme
- [ ] `src/data/cleaner.py` — veri temizleme
- [ ] `src/data/cache_manager.py` — fallback önbellek
- [ ] `src/features/time_features.py` — zaman özellikleri
- [ ] `src/features/market_features.py` — piyasa özellikleri
- [ ] Demo veri seti oluştur (API erişimi yokken)

## Aşama 3: Model Katmanı
- [ ] `src/models/trainer.py` — model eğitimi
- [ ] `src/models/predictor.py` — tahmin üretme
- [ ] `src/models/evaluator.py` — metrik hesaplama
- [ ] `src/models/walk_forward.py` — validasyon

## Aşama 4: Trading Simülasyonu
- [ ] `src/trading/simulator.py` — P&L simülatörü
- [ ] `src/trading/risk.py` — risk göstergesi

## Aşama 5: Premium UI
- [ ] `src/ui/styles.py` — koyu tema CSS
- [ ] `src/ui/components.py` — KPI kartları
- [ ] `src/ui/charts.py` — Plotly grafikleri
- [ ] `src/ui/export.py` — CSV dışa aktarma
- [ ] `app.py` — ana Streamlit uygulaması

## Aşama 6: Finalizasyon
- [ ] `README.md` oluştur
- [ ] Test ve doğrulama
- [ ] Tarayıcıda canlı kontrol
