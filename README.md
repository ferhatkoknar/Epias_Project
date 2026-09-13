# EPİAŞ GÖP PTF Fiyat Tahmini & Enerji Trading Terminali

Yapay zeka tabanlı Piyasa Takas Fiyatı (PTF) tahmin ve enerji trading karar destek platformu.

## Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Uygulamayı başlat
streamlit run app.py
```

## Gereksinimler

- Python 3.10+
- Bağımlılıklar: `requirements.txt` dosyasında listelenmiştir.

## Proje Yapısı

```
Epias_Project/
├── app.py                    # Ana Streamlit uygulaması
├── requirements.txt          # Bağımlılıklar
├── .streamlit/config.toml    # Koyu tema konfigürasyonu
├── config/settings.py        # Proje sabitleri
├── data/                     # Veri dizinleri (raw, processed, cache)
├── models/                   # Eğitilmiş model dosyaları (.joblib)
├── src/
│   ├── data/                 # ETL: veri çekme, temizleme, önbellek
│   ├── features/             # Öznitelik mühendisliği
│   ├── models/               # Model eğitimi, tahmin, değerlendirme
│   ├── trading/              # P&L simülasyonu, risk analizi
│   └── ui/                   # Streamlit bileşenleri, grafikler, CSS
└── tests/                    # Birim testleri
```

## Mimari

**3 Katmanlı Yapı:**

1. **Veri & ETL Katmanı** — EPİAŞ Şeffaflık API'sinden veri çekme, temizleme, öznitelik üretme
2. **Modelleme Katmanı** — CatBoost/LightGBM ile Walk-Forward validasyonlu tahmin
3. **Sunum Katmanı** — Streamlit + Plotly ile kurumsal koyu tema dashboard

## Kabul Kriterleri

| Metrik | Hedef |
|--------|-------|
| MAPE | < %12 |
| Yön Doğruluğu | > %70 |
| Inference Süresi | < 500ms |

## Lisans

Staj projesi — Eylül 2026
