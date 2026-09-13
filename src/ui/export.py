"""
Veri Dışa Aktarma Modülü (FR-08)
CSV dışa aktarma ve teknik rapor oluşturma.
"""

import io
import pandas as pd
from datetime import datetime


def export_predictions_csv(
    forecast_df: pd.DataFrame,
    actual_df: pd.DataFrame = None,
    metrics: dict = None,
) -> bytes:
    """
    Tahmin sonuçlarını CSV formatında dışa aktarır.
    
    Returns:
        CSV bytes (Streamlit download_button için)
    """
    export_df = forecast_df.copy()
    
    if actual_df is not None and "ptf" in actual_df.columns:
        # Gerçekleşen ve tahmin birleştir
        export_df = pd.merge(
            actual_df[["datetime", "ptf"]].rename(columns={"ptf": "gerceklesen_ptf"}),
            forecast_df.rename(columns={"predicted_ptf": "tahmin_ptf"}),
            on="datetime",
            how="outer",
        )
    
    # Metadata satırları
    buffer = io.StringIO()
    buffer.write(f"# EPİAŞ GÖP PTF Tahmin Raporu\n")
    buffer.write(f"# Oluşturulma: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    if metrics:
        buffer.write(f"# Model MAPE: %{metrics.get('mape', 'N/A')}\n")
        buffer.write(f"# Yön Doğruluğu: %{metrics.get('directional_accuracy', 'N/A')}\n")
    
    buffer.write("#\n")
    export_df.to_csv(buffer, index=False, encoding="utf-8-sig")
    
    return buffer.getvalue().encode("utf-8-sig")


def generate_technical_report(
    metrics: dict,
    trading_metrics: dict = None,
    summary: dict = None,
    model_type: str = "catboost",
) -> str:
    """
    Teknik analiz raporu oluşturur (Markdown formatı).
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report = f"""
# EPİAŞ GÖP PTF — Teknik Analiz Raporu
**Oluşturulma Tarihi:** {now}  
**Model:** {model_type.upper()}  

---

## 1. Model Performans Metrikleri

| Metrik | Değer | Hedef | Durum |
|--------|-------|-------|-------|
| MAPE | %{metrics.get('mape', 0):.2f} | <%12 | {'[KABUL] Basarili' if metrics.get('mape', 100) < 12 else '[UYARI] Basarisiz'} |
| RMSE | {metrics.get('rmse', 0):,.1f} TL | — | — |
| MAE | {metrics.get('mae', 0):,.1f} TL | — | — |
| R² | {metrics.get('r2', 0):.4f} | — | — |
| Yön Doğruluğu | %{metrics.get('directional_accuracy', 0):.1f} | >%70 | {'[KABUL] Basarili' if metrics.get('directional_accuracy', 0) > 70 else '[UYARI] Basarisiz'} |
| Maksimum Hata | {metrics.get('max_error', 0):,.1f} TL | — | — |

"""
    
    if summary:
        report += f"""
## 2. Tahmin Özeti

| Parametre | Değer |
|-----------|-------|
| Ortalama PTF | {summary.get('avg_ptf', 0):,.0f} TL/MWh |
| Minimum PTF | {summary.get('min_ptf', 0):,.0f} TL/MWh |
| Maksimum PTF | {summary.get('max_ptf', 0):,.0f} TL/MWh |
| 24s Trend | {summary.get('trend', '—')} |
| En Yüksek Saat | {summary.get('peak_hour', '—')}:00 |
| En Düşük Saat | {summary.get('offpeak_hour', '—')}:00 |
| Fiyat Aralığı | {summary.get('spread_range', 0):,.0f} TL |

"""
    
    if trading_metrics:
        report += f"""
## 3. Trading Simülasyonu

| Parametre | Değer |
|-----------|-------|
| Toplam P&L | {trading_metrics.get('total_pnl', 0):,.0f} TL |
| Toplam İşlem | {trading_metrics.get('total_trades', 0)} |
| Başarı Oranı | %{trading_metrics.get('win_rate', 0):.1f} |
| Ort. Kazanç | {trading_metrics.get('avg_win', 0):,.0f} TL |
| Ort. Kayıp | {trading_metrics.get('avg_loss', 0):,.0f} TL |
| Maks. Drawdown | {trading_metrics.get('max_drawdown_tl', 0):,.0f} TL ({trading_metrics.get('max_drawdown_pct', 0):.1f}%) |
| Sharpe Oranı | {trading_metrics.get('sharpe_ratio', 0):.2f} |
| Profit Factor | {trading_metrics.get('profit_factor', 0):.2f} |

"""
    
    report += """
---
*Bu rapor EPİAŞ GÖP PTF Tahmin Terminali tarafından otomatik üretilmiştir.*
"""
    
    return report
